/*
 * app.js — pantallas, estado en memoria, peticiones y limpieza.
 *
 * La fotografía vive solo aquí, en memoria del navegador; nunca se envía a ningún
 * sitio salvo a /api/generate, y se descarta al pulsar «Siguiente participante».
 *
 * La clave de API no aparece en este archivo ni en ninguna respuesta al cliente.
 */

(function () {
  'use strict';

  /** Textos de error según UI_COPY.md §3, indexados por `error.code` de API.md §5. */
  const ERROR_MESSAGES = {
    MISSING_PHOTO: 'Esa foto no se pudo usar. Vamos a tomar otra.',
    INVALID_IMAGE: 'Esa foto no se pudo usar. Vamos a tomar otra.',
    INVALID_STYLE: 'Elige uno de los personajes para continuar.',
    INVALID_NAME: 'Usa solo letras, espacios y guiones (hasta 20 caracteres).',
    IMAGE_TOO_LARGE: 'La foto es demasiado grande. Vamos a tomar otra.',
    BUSY: 'Estamos terminando otra aventura. Espera un momento.',
    PROVIDER_RATE_LIMIT: 'Hay muchas aventuras en preparación. Espera un momento y vuelve a intentarlo.',
    PROVIDER_TIMEOUT: 'Esto está tardando más de lo normal. Inténtalo otra vez.',
    PROVIDER_BAD_RESPONSE: 'No pudimos crear tu personaje esta vez. Inténtalo otra vez.',
    PROVIDER_ERROR: 'No pudimos crear tu personaje esta vez. Inténtalo otra vez.',
    PROVIDER_NOT_CONFIGURED: 'Algo no está listo todavía. Pídele ayuda a la persona encargada.',
    INTERNAL_ERROR: 'Algo salió mal. Inténtalo otra vez.',
    OFFLINE: 'No hay conexión. Pídele ayuda a la persona encargada.'
  };

  /** Códigos que obligan a volver a la captura de la foto. */
  const CODES_NEEDING_NEW_PHOTO = ['MISSING_PHOTO', 'INVALID_IMAGE', 'IMAGE_TOO_LARGE'];
  const LOADING_SLOW_MS = 15000;

  /**
   * Emoji e etiqueta de categoría por estilo. Es solo presentación: el catálogo
   * del servidor no depende de esto y no se envía a la API.
   */
  const STYLE_DECOR = {
    superhero: { icon: '🦸', tag: 'Cósmico' },
    royalty: { icon: '👑', tag: 'Realeza' },
    astronaut: { icon: '🧑‍🚀', tag: 'Espacio' },
    explorer: { icon: '🧭', tag: 'Aventura' },
    wizard: { icon: '🧙', tag: 'Fantasía' },
    inventor: { icon: '🤖', tag: 'Futuro' },
    knight: { icon: '🛡️', tag: 'Heroísmo' },
    ocean: { icon: '🐠', tag: 'Océano' }
  };
  const DEFAULT_DECOR = { icon: '✨', tag: 'Aventura' };

  /** Progreso simulado de la pantalla de carga: nunca promete un tiempo concreto. */
  const PROGRESS_TICK_MS = 400;
  const PROGRESS_MAX_BEFORE_DONE = 92;

  /**
   * Códigos en los que ofrecer «Elegir otro personaje» no ayuda: hay que
   * reintentar, no cambiar de estilo.
   */
  const CODES_WITHOUT_STYLE_OPTION = ['BUSY', 'PROVIDER_RATE_LIMIT', 'OFFLINE'];

  const SCREENS = ['welcome', 'camera', 'select', 'loading', 'result'];

  /** Estado en memoria de la sesión del participante. */
  const state = {
    photo: null,
    photoUrl: null,
    resultUrl: null,
    selectedStyle: null,
    catalog: [],
    transformed: false,
    generating: false,
    lastNameAttempt: '',
    health: { provider: 'mock', demo_mode: true },
    controller: null,
    loadingTimer: null,
    progressTimer: null,
    progress: 0
  };

  const $ = function (id) {
    return document.getElementById(id);
  };

  const dom = {};

  // ---------------------------------------------------------------- utilidades

  function showScreen(name) {
    SCREENS.forEach(function (screen) {
      const section = dom.screens[screen];
      if (section) {
        section.hidden = screen !== name;
      }
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function hideError() {
    dom.generateError.hidden = true;
    dom.generateErrorText.textContent = '';
    delete dom.generateError.dataset.retry;
    delete dom.generateError.dataset.code;
  }

  /**
   * Muestra el aviso de error de generación.
   *
   * El aviso es fijo (lo fija el CSS), así que se ve siempre, incluso si la
   * persona está desplazada hacia abajo mirando las tarjetas. Antes era `sticky` y
   * podía quedar fuera de la vista: parecía que no había pasado nada.
   *
   * `retryTarget` decide qué hace «Intentar de nuevo»: `camera` vuelve a la
   * captura y cualquier otro valor reintenta la generación.
   */
  function showError(code, retryTarget) {
    dom.generateErrorText.textContent = ERROR_MESSAGES[code] || ERROR_MESSAGES.INTERNAL_ERROR;
    dom.generateError.dataset.retry = retryTarget || 'generate';
    dom.generateError.dataset.code = code;
    dom.generateError.hidden = false;

    // Se ofrece cambiar de personaje solo cuando eso puede servir de algo.
    if (dom.btnGenerateOther) {
      dom.btnGenerateOther.hidden = CODES_WITHOUT_STYLE_OPTION.indexOf(code) >= 0;
    }
  }

  function revokePhotoUrl() {
    if (state.photoUrl) {
      URL.revokeObjectURL(state.photoUrl);
      state.photoUrl = null;
    }
  }

  function revokeResultUrl() {
    if (state.resultUrl) {
      URL.revokeObjectURL(state.resultUrl);
      state.resultUrl = null;
    }
  }

  function clearNameError() {
    dom.nameError.hidden = true;
    dom.nameError.textContent = '';
  }

  function setNameError(message) {
    dom.nameError.textContent = message;
    dom.nameError.hidden = false;
  }

  /** Reglas del nombre, aplicadas también en el cliente para avisar antes de enviar. */
  function validateName(value) {
    const name = (value || '').trim().replace(/\s+/g, ' ');
    if (!name) {
      return { ok: true, name: '' };
    }
    if (name.length > 20) {
      return { ok: false, name: name };
    }
    if (!/^[\p{L} '\u2019\u02bc-]+$/u.test(name)) {
      return { ok: false, name: name };
    }
    return { ok: true, name: name };
  }

  // ------------------------------------------------------------- carga inicial

  async function loadHealth() {
    try {
      const response = await fetch('/api/health', { cache: 'no-store' });
      const data = await response.json();
      state.health = {
        provider: data.provider || 'mock',
        demo_mode: Boolean(data.demo_mode)
      };
      dom.demoBadge.hidden = !state.health.demo_mode;
      if (data.status !== 'ok') {
        showError('PROVIDER_NOT_CONFIGURED', 'none');
      }
    } catch (error) {
      dom.demoBadge.hidden = true;
    }
  }

  async function loadCatalog() {
    try {
      const response = await fetch('/api/transformations', { cache: 'no-store' });
      const data = await response.json();
      state.catalog = data.transformations || [];
      renderCatalog();
    } catch (error) {
      state.catalog = [];
    }
  }

  function renderCatalog() {
    dom.styleGrid.innerHTML = '';

    state.catalog.forEach(function (style) {
      const decor = STYLE_DECOR[style.id] || DEFAULT_DECOR;

      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'card-style';
      card.dataset.styleId = style.id;
      card.setAttribute('role', 'radio');
      card.setAttribute('aria-checked', 'false');
      card.setAttribute('aria-label', style.label + '. ' + style.description);

      const check = document.createElement('span');
      check.className = 'card-style-check';
      check.textContent = '✓ ¡Elegido!';

      const icon = document.createElement('span');
      icon.className = 'card-style-icon';
      icon.setAttribute('aria-hidden', 'true');
      icon.textContent = decor.icon;

      const label = document.createElement('span');
      label.className = 'card-style-label';
      label.textContent = style.label;

      const description = document.createElement('span');
      description.className = 'card-style-description';
      description.textContent = style.description;

      const tag = document.createElement('span');
      tag.className = 'card-style-tag';
      tag.textContent = '⭐ ' + decor.tag;

      card.append(check, icon, label, description, tag);
      card.addEventListener('click', function () {
        selectStyle(style.id);
      });

      dom.styleGrid.appendChild(card);
    });
  }

  function selectStyle(styleId) {
    state.selectedStyle = styleId;
    forEachStyleCard(function (card) {
      const selected = card.dataset.styleId === styleId;
      card.classList.toggle('is-selected', selected);
      card.setAttribute('aria-checked', selected ? 'true' : 'false');
    });
    hideError();
  }

  // --------------------------------------------------------------- pantalla 2

  async function enterCamera() {
    showScreen('camera');
    dom.snapshot.hidden = true;
    dom.video.hidden = false;
    dom.btnCapture.hidden = false;
    dom.btnRepeat.hidden = true;
    dom.btnContinue.hidden = true;
    dom.cameraError.hidden = true;
    dom.cameraStatus.hidden = false;
    dom.cameraStatus.textContent = 'Activando la cámara…';

    const result = await Camera.start(dom.video);
    if (!result.ok) {
      showCameraError(result.message);
      return;
    }
    dom.cameraStatus.hidden = true;
  }

  function showCameraError(message) {
    Camera.stop();
    dom.cameraStatus.hidden = true;
    dom.cameraErrorText.textContent = message;
    dom.cameraError.hidden = false;
    dom.btnCapture.hidden = true;
    dom.btnRepeat.hidden = true;
    dom.btnContinue.hidden = true;
  }

  async function capturePhoto() {
    dom.btnCapture.disabled = true;
    const blob = await Camera.capture(dom.video);
    dom.btnCapture.disabled = false;

    if (!blob) {
      showCameraError(Camera.messages.generic);
      return;
    }

    state.photo = blob;
    revokePhotoUrl();
    state.photoUrl = URL.createObjectURL(blob);

    dom.snapshot.src = state.photoUrl;
    dom.snapshot.hidden = false;
    dom.video.hidden = true;

    // La cámara se apaga en cuanto hay foto: la luz del dispositivo se apaga.
    Camera.stop();

    dom.cameraStatus.hidden = true;
    dom.cameraError.hidden = true;
    dom.btnCapture.hidden = true;
    dom.btnRepeat.hidden = false;
    dom.btnContinue.hidden = false;
  }

  // --------------------------------------------------------------- pantalla 3

  function enterSelect() {
    if (state.photoUrl) {
      dom.selectPhoto.src = state.photoUrl;
    }
    if (!state.selectedStyle && state.catalog.length) {
      selectStyle(state.catalog[0].id);
    }
    showScreen('select');
    hideError();
  }

  // --------------------------------------------------------------- generación

  function setLoadingHint() {
    dom.loadingHint.textContent = 'Esto puede tardar un poquito.';
    window.clearTimeout(state.loadingTimer);
    state.loadingTimer = window.setTimeout(function () {
      dom.loadingHint.textContent = 'Ya casi… la magia necesita un poquito más.';
    }, LOADING_SLOW_MS);
  }

  /**
   * Barra de progreso de la pantalla de carga.
   *
   * Es una animación de acompañamiento, no una medición: avanza deprisa al
   * principio y se frena cerca del final, porque no se puede conocer el progreso
   * real del proveedor. Nunca llega al 100 % hasta que la imagen está lista, y no
   * se muestra ningún tiempo estimado (prohibido prometer tiempos).
   */
  function startProgress() {
    window.clearInterval(state.progressTimer);
    state.progress = 6;
    paintProgress();

    state.progressTimer = window.setInterval(function () {
      const remaining = PROGRESS_MAX_BEFORE_DONE - state.progress;
      if (remaining <= 0) {
        return;
      }
      // Se acerca al máximo sin alcanzarlo: cuanto más cerca, más lento.
      state.progress += Math.max(remaining * 0.06, 0.25);
      paintProgress();
    }, PROGRESS_TICK_MS);
  }

  function paintProgress() {
    if (dom.progressBar) {
      dom.progressBar.style.width = Math.min(state.progress, 100).toFixed(1) + '%';
    }
  }

  function stopProgress(completed) {
    window.clearInterval(state.progressTimer);
    state.progressTimer = null;
    if (completed) {
      state.progress = 100;
      paintProgress();
    }
  }

  async function generate() {
    if (state.generating) {
      return;
    }
    if (!state.photo || !state.selectedStyle) {
      showError(state.photo ? 'INVALID_STYLE' : 'MISSING_PHOTO', state.photo ? 'generate' : 'camera');
      return;
    }

    const nameCheck = validateName(dom.inputName.value);
    if (!nameCheck.ok) {
      setNameError('Usa solo letras, espacios y guiones (hasta 20 caracteres).');
      showScreen('select');
      return;
    }
    clearNameError();

    state.generating = true;
    state.lastNameAttempt = nameCheck.name;
    hideError();
    showScreen('loading');
    setLoadingHint();
    startProgress();
    dom.btnTransform.disabled = true;

    const form = new FormData();
    form.append('photo', state.photo, 'foto.jpg');
    form.append('style_id', state.selectedStyle);
    if (nameCheck.name) {
      form.append('name', nameCheck.name);
    }

    state.controller = new AbortController();

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        body: form,
        signal: state.controller.signal,
        cache: 'no-store'
      });

      if (!response.ok) {
        let code = 'INTERNAL_ERROR';
        try {
          const payload = await response.json();
          code = (payload.error && payload.error.code) || code;
        } catch (parseError) {
          code = 'INTERNAL_ERROR';
        }
        state.transformed = false;
        showScreen('select');
        showError(code, CODES_NEEDING_NEW_PHOTO.indexOf(code) >= 0 ? 'camera' : 'generate');
        return;
      }

      const blob = await response.blob();
      stopProgress(true);
      revokeResultUrl();
      state.resultUrl = URL.createObjectURL(blob);
      dom.resultImage.src = state.resultUrl;
      dom.resultCaption.textContent = captionFor(state.selectedStyle, nameCheck.name);
      state.transformed = true;
      dom.downloadError.hidden = true;
      showScreen('result');
    } catch (error) {
      if (error && error.name === 'AbortError') {
        // Cancelado por el operador: se vuelve a la selección sin mensaje de error.
        showScreen('select');
        return;
      }
      state.transformed = false;
      showScreen('select');
      showError('OFFLINE', 'generate');
    } finally {
      window.clearTimeout(state.loadingTimer);
      stopProgress(false);
      state.generating = false;
      state.controller = null;
      dom.btnTransform.disabled = false;
    }
  }

  function captionFor(styleId, name) {
    const style = state.catalog.filter(function (item) {
      return item.id === styleId;
    })[0];
    const defaultTitle = style ? style.default_title : '';
    return name ? name + ', ' + defaultTitle : defaultTitle;
  }

  // ------------------------------------------------------------------ descarga

  function downloadResult() {
    if (!state.resultUrl) {
      dom.downloadError.hidden = false;
      return;
    }
    try {
      const link = document.createElement('a');
      link.href = state.resultUrl;
      link.download = 'mi_personaje.png';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      dom.downloadError.hidden = true;
    } catch (error) {
      dom.downloadError.hidden = false;
    }
  }

  // ------------------------------------------------------------------ limpieza

  /** Reinicio completo para el siguiente participante (SPEC.md §10 y TASKS.md Fase 7). */
  function nextParticipant() {
    Camera.stop();
    window.clearTimeout(state.loadingTimer);
    stopProgress(false);
    if (state.controller) {
      state.controller.abort();
      state.controller = null;
    }

    revokePhotoUrl();
    revokeResultUrl();

    state.photo = null;
    state.selectedStyle = null;
    state.transformed = false;
    state.generating = false;
    state.lastNameAttempt = '';

    dom.snapshot.removeAttribute('src');
    dom.selectPhoto.removeAttribute('src');
    dom.resultImage.removeAttribute('src');
    dom.resultCaption.textContent = '';
    dom.inputName.value = '';
    dom.video.srcObject = null;
    clearNameError();
    hideError();
    dom.downloadError.hidden = true;
    dom.cameraError.hidden = true;

    forEachStyleCard(function (card) {
      card.classList.remove('is-selected');
      card.setAttribute('aria-checked', 'false');
    });

    // La barra de progreso vuelve a cero: si no, la siguiente aventura empezaría
    // con la barra llena.
    state.progress = 0;
    paintProgress();

    dom.btnTransform.disabled = false;
    showScreen('welcome');
  }

  /** Recorre las tarjetas del catálogo que construye `renderCatalog`. */
  function forEachStyleCard(callback) {
    Array.prototype.forEach.call(dom.styleGrid.children, callback);
  }

  /** «Probar otro personaje»: se conserva la foto, se descarta el resultado (E-09). */
  function tryAnotherStyle() {
    revokeResultUrl();
    dom.resultImage.removeAttribute('src');
    state.transformed = false;
    enterSelect();
  }

  function retryFromError() {
    // Se lee antes de ocultar, porque `hideError` limpia los datos del aviso.
    const target = dom.generateError.dataset.retry || 'generate';
    hideError();
    if (target === 'camera') {
      enterCamera();
      return;
    }
    if (target === 'none') {
      return;
    }
    generate();
  }

  // -------------------------------------------------------------------- arranque

  function cacheDom() {
    dom.screens = {
      welcome: $('screen-welcome'),
      camera: $('screen-camera'),
      select: $('screen-select'),
      loading: $('screen-loading'),
      result: $('screen-result')
    };
    dom.video = $('video');
    dom.snapshot = $('snapshot');
    dom.cameraStatus = $('camera-status');
    dom.cameraError = $('camera-error');
    dom.cameraErrorText = $('camera-error-text');
    dom.styleGrid = $('style-grid');
    dom.selectPhoto = $('select-photo');
    dom.inputName = $('input-name');
    dom.nameError = $('name-error');
    dom.resultImage = $('result-image');
    dom.resultCaption = $('result-caption');
    dom.downloadError = $('download-error');
    dom.generateError = $('generate-error');
    dom.generateErrorText = $('generate-error-text');
    dom.btnGenerateOther = $('btn-generate-other');
    dom.demoBadge = $('demo-badge');
    dom.loadingHint = $('loading-hint');
    dom.progressBar = $('progress-bar');
    dom.btnCapture = $('btn-capture');
    dom.btnRepeat = $('btn-repeat');
    dom.btnContinue = $('btn-continue');
    dom.btnTransform = $('btn-transform');
  }

  function bindEvents() {
    $('btn-start').addEventListener('click', enterCamera);
    dom.btnCapture.addEventListener('click', capturePhoto);
    dom.btnRepeat.addEventListener('click', enterCamera);
    dom.btnContinue.addEventListener('click', enterSelect);
    $('btn-back-camera').addEventListener('click', enterCamera);
    $('btn-camera-retry').addEventListener('click', enterCamera);
    dom.btnTransform.addEventListener('click', generate);
    dom.btnCancel = $('btn-cancel');
    dom.btnCancel.addEventListener('click', function () {
      if (state.controller) {
        state.controller.abort();
      }
      stopProgress(false);
      showScreen('select');
    });
    $('btn-download').addEventListener('click', downloadResult);
    $('btn-other-style').addEventListener('click', tryAnotherStyle);
    $('btn-next').addEventListener('click', nextParticipant);
    $('btn-generate-retry').addEventListener('click', retryFromError);
    $('btn-generate-other').addEventListener('click', function () {
      hideError();
      enterSelect();
    });
    dom.inputName.addEventListener('input', function () {
      const check = validateName(dom.inputName.value);
      if (!check.ok) {
        setNameError('Usa solo letras, espacios y guiones (hasta 20 caracteres).');
      } else {
        clearNameError();
      }
    });

    // Al cerrar o recargar la pestaña se apaga la cámara y se liberan los objetos.
    window.addEventListener('beforeunload', function () {
      Camera.stop();
      window.clearTimeout(state.loadingTimer);
      window.clearInterval(state.progressTimer);
      revokePhotoUrl();
      revokeResultUrl();
    });
  }

  function init() {
    cacheDom();
    bindEvents();
    showScreen('welcome');
    loadHealth();
    loadCatalog();
  }

  document.addEventListener('DOMContentLoaded', init);

  // Expuesto solo para depuración manual en consola: no contiene datos del participante.
  window.App = { state: state };
})();
