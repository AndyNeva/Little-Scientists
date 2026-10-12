"""Rutas HTTP de la API. Contrato completo en `docs/API.md`.

El servidor no mantiene estado de sesión y nunca escribe en disco. Los logs
registran solo ruta, estilo, código de resultado y duración: nunca imágenes,
nombres, claves ni cuerpos de solicitud.
"""

from __future__ import annotations

import logging
import threading
import time

from flask import Blueprint, Response, current_app, jsonify, render_template, request

import config
from data.transformations import build_prompt, get_style, public_catalog
from services.image_composer import build_title, compose_with_title
from services.image_generator import ProviderError
from services.image_preparation import InvalidImageError, prepare_for_provider
from services.name_validation import InvalidNameError, normalize_name
from services.provider_factory import build_provider

api = Blueprint("api", __name__)

logger = logging.getLogger("feria_ia")

#: Una sola generación a la vez. El bloqueo no bloquea: si está ocupado se
#: responde BUSY.
_generation_lock = threading.Lock()


#: Mensajes seguros por código de error (`docs/API.md` §1 y §5). Los mensajes de los
#: adaptadores pueden contener detalles internos, así que nunca se reenvían tal
#: cual: el cliente recibe siempre este texto fijo.
SAFE_MESSAGES: dict[str, str] = {
    "MISSING_PHOTO": "No se envió ninguna fotografía.",
    "INVALID_IMAGE": "El archivo no es una imagen JPEG, PNG o WebP.",
    "INVALID_STYLE": "El estilo no existe en el catálogo.",
    "INVALID_NAME": "El nombre no cumple las reglas permitidas.",
    "IMAGE_TOO_LARGE": "La fotografía supera el tamaño máximo permitido.",
    "BUSY": "Ya hay una generación en curso.",
    "PROVIDER_NOT_CONFIGURED": "El proveedor de imágenes no está configurado.",
    "PROVIDER_RATE_LIMIT": "El proveedor alcanzó su límite de uso.",
    "PROVIDER_TIMEOUT": "El proveedor tardó demasiado en responder.",
    "PROVIDER_BAD_RESPONSE": "El proveedor no devolvió una imagen utilizable.",
    "PROVIDER_ERROR": "Error de comunicación con el proveedor de imágenes.",
    "INTERNAL_ERROR": "Algo salió mal durante la generación.",
}


def _error(code: str, http_status: int, message: str) -> tuple[Response, int]:
    """Formato único de error (API.md §1 y D-09). Nunca incluye datos sensibles."""
    return jsonify({"error": {"code": code, "message": message}}), http_status


def _safe_message(code: str, fallback: str = "") -> str:
    return SAFE_MESSAGES.get(code) or fallback or "Algo salió mal."


def _log_provider_failure(category: str, exc: BaseException) -> None:
    """Registra la clase del error y un mensaje saneado.

    Se eliminan del mensaje los valores de las credenciales configuradas para que
    una clave nunca llegue al log.
    """
    settings: config.Settings = current_app.config["SETTINGS"]
    text = str(exc)
    for secret in (
        settings.cloudflare_api_token,
        settings.cloudflare_account_id,
        settings.gemini_api_key,
    ):
        if secret:
            text = text.replace(secret, "«oculto»")
    if len(text) > 300:
        text = text[:300] + "…"
    logger.warning("fallo de proveedor category=%s type=%s detail=%s", category, type(exc).__name__, text)

    if getattr(exc, "code", "") == "PROVIDER_RATE_LIMIT":
        _log_quota_hint(settings)


def _log_quota_hint(settings: config.Settings) -> None:
    """Cuando se agota la cuota, dice en la terminal qué hacer.

    Sin esto, el operador ve «límite de uso agotado» y no sabe si esperar, cambiar
    de proveedor o pasar a modo demostración. El proveedor activo solo se nombra
    aquí, en los registros, nunca en la pantalla.
    """
    alternativas = [p for p in config.PROVIDERS_VALIDOS if p != settings.provider]
    disponibles = []
    for proveedor in alternativas:
        if proveedor == "cloudflare" and settings.cloudflare_api_token and settings.cloudflare_account_id:
            disponibles.append("cloudflare")
        elif proveedor == "gemini" and settings.gemini_api_key:
            disponibles.append("gemini")
        elif proveedor == "mock":
            disponibles.append("mock (modo demostración)")

    if disponibles:
        logger.warning(
            "Cuota agotada con el proveedor «%s». Alternativas ya configuradas: %s. "
            "Se cambia con IMAGE_PROVIDER en .env y reiniciando.",
            settings.provider,
            ", ".join(disponibles),
        )
    else:
        logger.warning(
            "Cuota agotada con el proveedor «%s» y no hay ninguna alternativa "
            "configurada. Añade credenciales o usa IMAGE_PROVIDER=mock.",
            settings.provider,
        )

    if settings.provider == "cloudflare":
        logger.warning(
            "Nota: la cuota gratuita de Cloudflare son 10.000 neuronas al día "
            "(unas 6 imágenes) y se reinicia a las 00:00 UTC."
        )


def _settings() -> config.Settings:
    return current_app.config["SETTINGS"]


@api.get("/")
def index() -> str:
    """Pantalla principal: las cinco pantallas viven en la plantilla."""
    return render_template("index.html")


@api.get("/api/health")
def health() -> tuple[Response, int]:
    """Comprueba que el servidor funciona e informa del proveedor activo (API.md §2).

    El campo `provider` es para el operador y los registros: la interfaz **no** lo
    muestra, de modo que cambiar de proveedor no se refleja en la pantalla.
    """
    settings = _settings()
    message = ""

    missing = settings.missing_credentials()
    if missing:
        message = "Falta configuración del proveedor: " + ", ".join(missing) + "."
    else:
        try:
            build_provider(settings)
        except ProviderError as exc:
            message = exc.message

    payload = {
        "status": "ok" if message == "" else "error",
        "provider": settings.provider,
        "demo_mode": settings.demo_mode,
    }
    if message:
        payload["message"] = message
    return jsonify(payload), 200


@api.get("/api/transformations")
def transformations() -> Response:
    """Catálogo de estilos. **No expone el prompt** (API.md §3)."""
    return jsonify({"transformations": public_catalog()})


@api.post("/api/generate")
def generate() -> Response:
    """Recibe foto, estilo y nombre opcional; devuelve el PNG final (API.md §4)."""
    started = time.perf_counter()
    settings = _settings()
    style_id_for_log = "-"

    def finish(response: Response, code: str, status: int) -> Response:
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "generate style=%s code=%s status=%s duration_ms=%s",
            style_id_for_log,
            code,
            status,
            duration_ms,
        )
        response.headers["Cache-Control"] = "no-store"
        response.status_code = status
        return response

    def fail(code: str, status: int, message: str) -> Response:
        # Los códigos de proveedor usan siempre un texto fijo: nunca se reenvía el
        # mensaje del adaptador, que podría contener detalles internos.
        safe = _safe_message(code, message) if code.startswith("PROVIDER_") else message
        body, http_status = _error(code, status, safe)
        return finish(body, code, http_status)

    # 1. La fotografía es obligatoria.
    photo = request.files.get("photo")
    if photo is None:
        return fail("MISSING_PHOTO", 400, "No se envió ninguna fotografía.")

    # 2. El estilo debe existir en el catálogo (validado antes de gastar trabajo).
    style_id = (request.form.get("style_id") or "").strip()
    style_id_for_log = style_id or "-"
    try:
        style = get_style(style_id)
    except KeyError:
        return fail("INVALID_STYLE", 400, "El estilo no existe en el catálogo.")

    # 3. El nombre es opcional y se valida según D-08.
    try:
        name = normalize_name(request.form.get("name"), settings.max_name_length)
    except InvalidNameError:
        return fail(
            "INVALID_NAME",
            400,
            f"El nombre admite letras, espacios y guiones (hasta {settings.max_name_length}).",
        )

    # 4. Tamaño del archivo dentro del límite configurado.
    raw_bytes = photo.read()
    if len(raw_bytes) > settings.max_upload_bytes:
        return fail(
            "IMAGE_TOO_LARGE",
            413,
            f"La fotografía supera el máximo de {settings.max_upload_mb} MB.",
        )

    # 5. Se comprueba que el contenido sea realmente una imagen admitida.
    try:
        prepared, _size, _format = prepare_for_provider(
            raw_bytes,
            max_side_px=settings.input_max_side_px,
            jpeg_quality=settings.input_jpeg_quality,
        )
    except InvalidImageError:
        return fail("INVALID_IMAGE", 400, "El archivo no es una imagen JPEG, PNG o WebP.")

    # 6. El prompt lo construye el servidor desde el catálogo (D-06).
    prompt = build_prompt(style_id)

    # 7. Una sola generación a la vez.
    if not _generation_lock.acquire(blocking=False):
        return fail("BUSY", 409, "Ya hay una generación en curso.")

    try:
        provider = build_provider(settings)
    except ProviderError as exc:
        _generation_lock.release()
        _log_provider_failure("configuracion", exc)
        return fail(exc.code, exc.http_status, exc.message)

    try:
        try:
            generated = provider.generate(prepared, prompt)
        except ProviderError as exc:
            _log_provider_failure("generacion", exc)
            return fail(exc.code, exc.http_status, exc.message)
        except Exception as exc:  # noqa: BLE001 - se convierte en INTERNAL_ERROR sin filtrar detalles
            _log_provider_failure("inesperado", exc)
            return fail("INTERNAL_ERROR", 500, "Algo salió mal durante la generación.")

        # 8. El título lo dibuja Pillow en una franja debajo de la imagen.
        try:
            final = compose_with_title(
                generated,
                build_title(name, style["default_title"]),
                style_id=style_id,
            )
        except Exception as exc:  # noqa: BLE001
            _log_provider_failure("composicion", exc)
            return fail("INTERNAL_ERROR", 500, "No se pudo preparar la imagen final.")
    finally:
        _generation_lock.release()

    response = Response(final, mimetype="image/png")
    response.headers["X-Demo-Mode"] = "true" if settings.demo_mode else "false"
    return finish(response, "OK", 200)
