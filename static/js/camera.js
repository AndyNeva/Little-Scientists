/*
 * camera.js — acceso a la webcam, captura y liberación de la cámara.
 *
 * Textos de error según UI_COPY.md §2. Este archivo no conoce la API del
 * servidor: solo gestiona el dispositivo y devuelve un Blob con la foto.
 */

(function (global) {
  'use strict';

  const CAMERA_MESSAGES = {
    NotAllowedError: 'Necesitamos permiso para usar la cámara. Pídele ayuda a la persona encargada.',
    NotFoundError: 'No encontramos una cámara conectada.',
    NotReadableError: 'La cámara está ocupada por otra aplicación.',
    insecure: 'Abre la aplicación desde localhost para usar la cámara.',
    generic: 'No pudimos activar la cámara. Pídele ayuda a la persona encargada.'
  };

  /** Lado mayor de la foto capturada, en píxeles. */
  const CAPTURE_MAX_SIDE = 1024;
  const CAPTURE_QUALITY = 0.92;

  let stream = null;

  function isSecureContextAvailable() {
    if (global.isSecureContext) {
      return true;
    }
    const host = global.location && global.location.hostname;
    return host === 'localhost' || host === '127.0.0.1' || host === '[::1]';
  }

  function messageForError(error) {
    if (!error) {
      return CAMERA_MESSAGES.generic;
    }
    return CAMERA_MESSAGES[error.name] || CAMERA_MESSAGES.generic;
  }

  /** Detiene todas las pistas de la cámara (SPEC.md §10 «Limpieza al terminar»). */
  function stop() {
    if (stream) {
      stream.getTracks().forEach(function (track) {
        track.stop();
      });
      stream = null;
    }
    return null;
  }

  /**
   * Activa la cámara y conecta el stream al elemento <video>.
   * Devuelve { ok: true } o { ok: false, message }.
   */
  async function start(videoElement) {
    if (!isSecureContextAvailable()) {
      return { ok: false, message: CAMERA_MESSAGES.insecure };
    }
    if (!global.navigator || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return { ok: false, message: CAMERA_MESSAGES.generic };
    }

    stop();

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
    } catch (error) {
      return { ok: false, message: messageForError(error) };
    }

    videoElement.srcObject = stream;
    try {
      await videoElement.play();
    } catch (error) {
      // Algunos navegadores bloquean play() hasta que hay datos; se reintenta con loadedmetadata.
      await new Promise(function (resolve) {
        videoElement.addEventListener('loadedmetadata', resolve, { once: true });
        setTimeout(resolve, 1500);
      });
      try {
        await videoElement.play();
      } catch (playError) {
        return { ok: false, message: CAMERA_MESSAGES.generic };
      }
    }

    return { ok: true };
  }

  /** Indica si hay un stream activo. */
  function isActive() {
    return stream !== null;
  }

  /**
   * Captura el fotograma actual como Blob JPEG, reduciendo el lado mayor.
   * Devuelve null si todavía no hay imagen.
   */
  async function capture(videoElement) {
    const width = videoElement.videoWidth;
    const height = videoElement.videoHeight;
    if (!width || !height) {
      return null;
    }

    const scale = Math.min(1, CAPTURE_MAX_SIDE / Math.max(width, height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);

    const context = canvas.getContext('2d');
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise(function (resolve) {
      canvas.toBlob(resolve, 'image/jpeg', CAPTURE_QUALITY);
    });

    // El lienzo no se conserva: se libera el buffer en cuanto hay Blob.
    canvas.width = 0;
    canvas.height = 0;

    return blob;
  }

  global.Camera = {
    start: start,
    stop: stop,
    capture: capture,
    isActive: isActive,
    messages: CAMERA_MESSAGES
  };
})(window);
