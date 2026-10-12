"""Pruebas de la interfaz y del interruptor de proveedor.

Dos objetivos:

1. Que el marcado siga exponiendo **todos** los identificadores que consume
   `static/js/app.js`. Un rediseño que rompa esta correspondencia deja la
   aplicación inservible aunque el backend funcione.
2. Que **el proveedor activo no se refleje en la interfaz** (requisito del
   proyecto): cambiar de Cloudflare a Gemini no debe verse por ningún lado salvo
   en los registros del servidor.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")

#: Identificadores que `app.js` busca por `id`. Si falta uno, la interfaz se rompe.
REQUIRED_IDS = (
    "screen-welcome",
    "screen-camera",
    "screen-select",
    "screen-loading",
    "screen-result",
    "video",
    "snapshot",
    "camera-status",
    "camera-error",
    "camera-error-text",
    "style-grid",
    "select-photo",
    "input-name",
    "name-error",
    "name-help",
    "result-image",
    "result-caption",
    "download-error",
    "generate-error",
    "generate-error-text",
    "demo-badge",
    "loading-hint",
    "progress-bar",
    "btn-start",
    "btn-capture",
    "btn-repeat",
    "btn-continue",
    "btn-back-camera",
    "btn-camera-retry",
    "btn-transform",
    "btn-cancel",
    "btn-download",
    "btn-other-style",
    "btn-next",
    "btn-generate-retry",
    "btn-generate-other",
)


@pytest.mark.parametrize("element_id", REQUIRED_IDS)
def test_el_marcado_conserva_los_identificadores_que_usa_app_js(element_id: str):
    assert f'id="{element_id}"' in TEMPLATE


def test_los_identificadores_que_usa_app_js_existen_de_verdad():
    """Compara la lista del JavaScript con el marcado: detecta cualquier olvido."""
    app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    usados = set(re.findall(r"\$\('([a-z0-9-]+)'\)", app_js))

    faltantes = sorted(elemento for elemento in usados if f'id="{elemento}"' not in TEMPLATE)
    assert faltantes == [], f"app.js busca identificadores que no están en el marcado: {faltantes}"


def test_la_hoja_de_estilos_es_la_del_sistema_de_diseno():
    css = (BASE_DIR / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    # Los colores clave del sistema «Aventura IA Playful Clean».
    for color in ("#630ed4", "#7c3aed", "#24005b", "#fef7ff", "#ede9fe", "#f59e0b"):
        assert color.lower() in css.lower(), f"Falta el color del sistema: {color}"


def test_las_tipografias_del_diseno_estan_incluidas_y_se_usan():
    css = (BASE_DIR / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    assert "@font-face" in css
    assert "Rubik.ttf" in css and "NunitoSans.ttf" in css

    for archivo in ("Rubik.ttf", "NunitoSans.ttf", "Fredoka-SemiBold.ttf"):
        assert (BASE_DIR / "static" / "assets" / "fonts" / archivo).is_file(), archivo


def test_los_botones_respetan_el_tamano_minimo_tactil():
    """UI_COPY.md §5 y DESIGN.md: mínimo 48 px, ideal 56 px."""
    css = (BASE_DIR / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    assert "min-height: 56px" in css
    assert "min-height: 52px" in css  # campo de texto


def test_se_respeta_la_preferencia_de_menos_movimiento():
    css = (BASE_DIR / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css


# ------------------------------------------------- ocultar y mostrar elementos


def test_la_regla_global_de_hidden_es_obligatoria():
    """Sin `[hidden] { display: none !important }` los elementos ocultos se ven.

    Los componentes declaran `display: flex` o `inline-flex`, y eso gana sobre el
    `display: none` que el navegador aplica a `[hidden]`. Este fallo hacía que
    «Repetir» y «Continuar» aparecieran antes de tomar la foto.
    """
    css = (BASE_DIR / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    assert re.search(r"\[hidden\]\s*\{[^}]*display:\s*none\s*!important", css), (
        "Falta la regla global [hidden] { display: none !important } en styles.css"
    )


def test_los_componentes_que_alternan_visibilidad_respetan_hidden():
    """Todo componente que `app.js` muestra u oculta debe poder ocultarse de verdad."""
    css = (BASE_DIR / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    assert re.search(r"\[hidden\]\s*\{[^}]*!important", css)

    # El envoltorio del aviso no debe poder tapar el `hidden` con su propio display.
    envoltorio = re.search(r"\.alert-overlay\s*\{([^}]*)\}", css)
    assert envoltorio, "Falta la regla .alert-overlay"
    assert "display:" not in envoltorio.group(1), (
        "El envoltorio del aviso no debe declarar display: se encarga de la posición, "
        "y un display de autor anularía el atributo hidden"
    )


def test_el_aviso_de_error_es_fijo_y_siempre_visible():
    """Reproduce el fallo real: con la página desplazada el aviso no se veía."""
    css = (BASE_DIR / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    regla = re.search(r"\.alert-overlay\s*\{([^}]*)\}", css).group(1)

    assert "position: fixed" in regla, "El aviso debe ser fijo para verse siempre"
    assert "bottom:" in regla
    assert "z-index:" in regla
    # La barra superior sí es sticky y eso es correcto; lo que no debe serlo es el aviso.
    assert "position: sticky" not in regla, "El aviso no debe volver a ser sticky"


def test_el_aviso_de_error_esta_en_un_envoltorio_separado():
    """El `hidden` va en el envoltorio y el aspecto en el aviso de dentro."""
    assert 'class="alert-overlay" id="generate-error"' in TEMPLATE
    assert 'class="alert alert--floating"' in TEMPLATE


def test_se_ofrece_reintentar_siempre():
    assert 'id="btn-generate-retry"' in TEMPLATE
    assert "Intentar de nuevo" in TEMPLATE


def _etiqueta_de_boton(element_id: str) -> str:
    """Devuelve la etiqueta de apertura `<button …>` del identificador indicado."""
    encontrado = re.search(r"<button[^>]*id=\"" + re.escape(element_id) + r"\"[^>]*>", TEMPLATE)
    assert encontrado, f"No se encontró el botón {element_id}"
    return encontrado.group(0)


def _boton_completo(element_id: str) -> str:
    """Devuelve el botón entero, incluido su texto, hasta la etiqueta de cierre."""
    encontrado = re.search(
        r"<button[^>]*id=\"" + re.escape(element_id) + r"\"[^>]*>.*?</button>",
        TEMPLATE,
        re.S,
    )
    assert encontrado, f"No se encontró el botón completo {element_id}"
    return encontrado.group(0)


@pytest.mark.parametrize("element_id", ["btn-repeat", "btn-continue"])
def test_los_botones_de_camara_empiezan_ocultos(element_id: str):
    """Al entrar en la pantalla solo debe verse «Tomar foto»."""
    assert "hidden" in _etiqueta_de_boton(element_id)


def test_el_boton_de_tomar_foto_empieza_visible():
    assert "hidden" not in _etiqueta_de_boton("btn-capture")


def test_el_boton_de_continuar_no_esta_visible_al_arrancar():
    """No se puede continuar sin foto: el botón debe estar oculto de inicio."""
    etiqueta = _etiqueta_de_boton("btn-continue")
    assert " hidden" in etiqueta or 'hidden="' in etiqueta


def test_los_estados_de_los_botones_de_camara_son_coherentes_en_el_codigo():
    """Comprueba la secuencia: inicio → captura → repetir o continuar."""
    app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")

    # Empieza la cámara: solo «Tomar foto».
    inicio = re.search(r"async function enterCamera\(\)(.*?)\n  \}", app_js, re.S).group(1)
    assert re.search(r"btnCapture\.hidden = false", inicio)
    assert re.search(r"btnRepeat\.hidden = true", inicio)
    assert re.search(r"btnContinue\.hidden = true", inicio)

    # Después de capturar: se oculta «Tomar foto» y aparecen «Repetir» y «Continuar».
    captura = re.search(r"async function capturePhoto\(\)(.*?)\n  \}", app_js, re.S).group(1)
    assert re.search(r"btnCapture\.hidden = true", captura)
    assert re.search(r"btnRepeat\.hidden = false", captura)
    assert re.search(r"btnContinue\.hidden = false", captura)

    # Si falla la cámara no debe quedar ningún botón suelto.
    error = re.search(r"function showCameraError\(.*?\)(.*?)\n  \}", app_js, re.S).group(1)
    assert re.search(r"btnCapture\.hidden = true", error)
    assert re.search(r"btnRepeat\.hidden = true", error)
    assert re.search(r"btnContinue\.hidden = true", error)


def test_repetir_vuelve_a_mostrar_solo_el_boton_de_tomar_foto():
    """«Repetir» reutiliza `enterCamera`, que restablece el estado inicial."""
    app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert re.search(r"dom\.btnRepeat\.addEventListener\('click', enterCamera\)", app_js)


# --------------------------------------------------------- aviso de error


def test_el_boton_de_reinicio_es_visible_y_explicito():
    """En la pantalla final debe haber un botón claro para empezar con otro niño.

    Antes era un botón fantasma, discreto y fácil de no ver: el operador podía
    quedarse buscando cómo volver al inicio.
    """
    boton = _boton_completo("btn-next")

    assert "Siguiente participante" in boton, "Se mantiene el texto de UI_COPY.md"
    assert "Empezar de nuevo" in boton, "Debe quedar claro que reinicia el flujo"
    assert "btn--ghost" not in boton, "No debe ser un botón fantasma"
    assert "hidden" not in _etiqueta_de_boton("btn-next"), "Debe verse siempre en la pantalla final"


def test_la_pantalla_final_explica_que_hace_el_boton_de_reinicio():
    assert "Borra la foto" in TEMPLATE
    assert "vuelve al inicio" in TEMPLATE


def test_el_reinicio_borra_todo_lo_del_participante():
    """Debe dejar el estado limpio: foto, resultado, nombre, elección y progreso."""
    app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    reinicio = re.search(r"function nextParticipant\(\)(.*?)\n  \}", app_js, re.S).group(1)

    obligatorio = {
        "Camera.stop()": "apagar la cámara",
        "revokePhotoUrl()": "liberar la foto del navegador",
        "revokeResultUrl()": "liberar la imagen del resultado",
        "state.photo = null": "olvidar la foto",
        "state.selectedStyle = null": "olvidar el personaje elegido",
        "state.controller.abort()": "cancelar una generación en curso",
        "state.progress = 0": "reiniciar la barra de progreso",
        "paintProgress()": "repintar la barra",
        "dom.resultImage.removeAttribute('src')": "quitar la imagen del resultado",
        "dom.snapshot.removeAttribute('src')": "quitar la vista previa",
        "dom.selectPhoto.removeAttribute('src')": "quitar la miniatura",
        "dom.inputName.value = ''": "borrar el nombre",
        "clearNameError()": "limpiar el error del nombre",
        "hideError()": "ocultar el aviso de error",
        "showScreen('welcome')": "volver a la bienvenida",
    }
    faltan = [motivo for fragmento, motivo in obligatorio.items() if fragmento not in reinicio]
    assert faltan == [], f"El reinicio no hace: {faltan}"

    # Y debe quitar la marca de seleccionada de todas las tarjetas.
    assert "forEachStyleCard" in reinicio
    assert "remove('is-selected')" in reinicio


def test_el_reinicio_se_dispara_desde_el_boton_de_la_pantalla_final():
    app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert re.search(r"\$\('btn-next'\)\.addEventListener\('click', nextParticipant\)", app_js)


def test_el_reinicio_no_conserva_la_foto_para_el_siguiente():
    """Es un reinicio completo, no como «Probar otro personaje», que sí la conserva."""
    app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    reinicio = re.search(r"function nextParticipant\(\)(.*?)\n  \}", app_js, re.S).group(1)
    otro = re.search(r"function tryAnotherStyle\(\)(.*?)\n  \}", app_js, re.S).group(1)

    assert "state.photo = null" in reinicio
    assert "state.photo = null" not in otro, "«Probar otro personaje» debe conservar la foto"


def test_el_boton_de_elegir_personaje_no_se_ofrece_cuando_no_ayuda():
    """Con la cuota agotada o el servidor ocupado, cambiar de personaje no sirve."""
    app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert "CODES_WITHOUT_STYLE_OPTION" in app_js
    assert re.search(
        r"CODES_WITHOUT_STYLE_OPTION\s*=\s*\[[^\]]*'PROVIDER_RATE_LIMIT'", app_js
    ), "La cuota agotada debe estar entre los códigos sin opción de cambiar de personaje"
    assert re.search(r"btnGenerateOther\.hidden\s*=", app_js)


def test_ocultar_el_aviso_limpia_el_estado_de_reintento():
    """Un `dataset.retry` viejo haría que «Intentar de nuevo» fuera al sitio equivocado."""
    app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    ocultar = re.search(r"function hideError\(\)(.*?)\n  \}", app_js, re.S).group(1)

    assert "delete dom.generateError.dataset.retry" in ocultar
    assert "delete dom.generateError.dataset.code" in ocultar


def test_el_reintento_lee_el_destino_antes_de_ocultar_el_aviso():
    """Si se leyera después, `hideError` ya habría borrado el destino."""
    app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    funcion = re.search(r"function retryFromError\(\)(.*?)\n  \}", app_js, re.S).group(1)

    posicion_lectura = funcion.index("dataset.retry")
    posicion_ocultar = funcion.index("hideError()")
    assert posicion_lectura < posicion_ocultar, (
        "retryFromError debe leer dataset.retry antes de llamar a hideError"
    )


# ------------------------------------------------- interruptor de proveedor


def _render(client) -> str:
    response = client.get("/")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def _con_proveedor(settings, proveedor: str):
    from app import create_app

    configurado = settings.__class__(
        **{
            **settings.__dict__,
            "provider": proveedor,
            "cloudflare_account_id": "cuenta-de-prueba",
            "cloudflare_api_token": "token-de-prueba",
            "cloudflare_model": "@cf/black-forest-labs/flux-2-klein-9b",
            "gemini_api_key": "clave-de-prueba",
            "gemini_model": "gemini-nano-banana-2.1",
        }
    )
    app = create_app(configurado)
    app.config.update(TESTING=True)
    return app


@pytest.mark.parametrize("proveedor", ["cloudflare", "gemini"])
def test_el_proveedor_activo_no_aparece_en_la_interfaz(settings, proveedor: str):
    """Cambiar de proveedor no debe verse: la interfaz es idéntica."""
    app = _con_proveedor(settings, proveedor)
    html = _render(app.test_client())

    assert "cloudflare" not in html.lower()
    assert "gemini" not in html.lower()
    assert "@cf/" not in html
    assert proveedor not in html


def test_la_interfaz_es_identica_con_cualquier_proveedor(settings):
    """El HTML de las dos configuraciones debe ser exactamente el mismo."""
    html_cloudflare = _render(_con_proveedor(settings, "cloudflare").test_client())
    html_gemini = _render(_con_proveedor(settings, "gemini").test_client())
    assert html_cloudflare == html_gemini


def test_ningun_proveedor_explicito_aparece_en_los_recursos_del_cliente():
    """Fuera de los comentarios: el navegador no debe saber quién genera."""
    for carpeta in ("static", "templates"):
        for ruta in (BASE_DIR / carpeta).rglob("*"):
            if not ruta.is_file() or ruta.suffix not in {".js", ".css", ".html"}:
                continue
            contenido = ruta.read_text(encoding="utf-8").lower()
            assert "cloudflare" not in contenido, ruta
            assert "gemini" not in contenido, ruta


def test_el_modo_demostracion_si_se_anuncia(settings):
    """`demo_mode` es la única excepción: la especificación obliga a avisarlo."""
    app = _con_proveedor(settings, "mock")
    html = _render(app.test_client())

    assert 'id="demo-badge"' in html
    assert "Modo demostración" in html


def test_health_informa_del_proveedor_para_los_logs_y_la_operacion(settings):
    """El contrato de API.md §2 se mantiene, pero la interfaz no lo pinta."""
    app = _con_proveedor(settings, "gemini")
    datos = app.test_client().get("/api/health").get_json()

    assert datos["provider"] == "gemini"
    assert datos["demo_mode"] is False
    assert datos["status"] == "ok"


def test_health_avisa_si_faltan_credenciales_sin_revelar_valores(settings):
    sin_clave = settings.__class__(**{**settings.__dict__, "provider": "gemini", "gemini_api_key": None})
    from app import create_app

    app = create_app(sin_clave)
    app.config.update(TESTING=True)
    datos = app.test_client().get("/api/health").get_json()

    assert datos["status"] == "error"
    assert "GEMINI_API_KEY" in datos.get("message", "")


def test_la_importacion_del_proveedor_gemini_no_depende_del_sdk():
    """El módulo debe importarse aunque `google-genai` no esté instalado."""
    import importlib

    modulo = importlib.import_module("services.gemini_provider")
    assert hasattr(modulo, "GeminiProvider")
