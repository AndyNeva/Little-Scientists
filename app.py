"""Aplicación Flask del prototipo de transformación de fotos con IA.

Punto de entrada: `python app.py` (ver README.md). Servidor **sin estado**, que
no escribe fotografías en disco y no expone claves al navegador (PLAN.md D-01,
D-02 y D-12).
"""

from __future__ import annotations

import logging
import os

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

import config
from api.routes import api
from services.image_generator import ProviderError
from services.provider_factory import build_provider

logger = logging.getLogger("feria_ia")


def _configure_logging() -> None:
    """Logs solo de eventos (PLAN.md D-10).

    El nivel se controla con `LOG_LEVEL` (por defecto INFO). Nunca se registran
    imágenes, nombres, claves ni cuerpos de solicitud.
    """
    level_name = (os.environ.get("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s"))

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def create_app(settings: config.Settings | None = None) -> Flask:
    """Crea la aplicación. `settings` se inyecta en las pruebas."""
    app = Flask(__name__, static_folder="static", template_folder="templates")

    resolved = settings if settings is not None else config.load_settings()
    app.config["SETTINGS"] = resolved

    # Werkzeug corta cuerpos desmesurados antes de parsearlos. El margen cubre el
    # sobrecoste de multipart; el límite exacto del archivo lo comprueba la ruta.
    app.config["MAX_CONTENT_LENGTH"] = resolved.max_upload_bytes + (1024 * 1024)

    if app.config.get("TESTING"):
        app.config["PROPAGATE_EXCEPTIONS"] = True

    _configure_logging()
    app.register_blueprint(api)

    @app.errorhandler(RequestEntityTooLarge)
    def _too_large(_exc: RequestEntityTooLarge):
        return (
            jsonify(
                {
                    "error": {
                        "code": "IMAGE_TOO_LARGE",
                        "message": "La solicitud supera el tamaño máximo permitido.",
                    }
                }
            ),
            413,
        )

    @app.errorhandler(HTTPException)
    def _http_error(exc: HTTPException):
        """404 y 405 en JSON para las rutas de la API (API.md §6)."""
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "error": {
                            "code": "NOT_FOUND" if exc.code == 404 else "METHOD_NOT_ALLOWED",
                            "message": exc.description,
                        }
                    }
                ),
                exc.code or 500,
            )
        return exc

    @app.errorhandler(Exception)
    def _unexpected(exc: Exception):  # noqa: ANN001
        """Cualquier fallo inesperado se traduce sin filtrar trazas ni secretos."""
        if isinstance(exc, HTTPException):
            return _http_error(exc)
        logger.exception("Error inesperado en la aplicación")
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "Algo salió mal. Inténtalo otra vez.",
                        }
                    }
                ),
                500,
            )
        return ("Algo salió mal.", 500)

    return app


def _startup_report(app: Flask) -> None:
    """Avisa en la terminal del proveedor activo y de la configuración que falta."""
    settings: config.Settings = app.config["SETTINGS"]
    try:
        provider = build_provider(settings)
        logger.info(
            "Proveedor activo: %s%s",
            provider.name,
            " (modo demostración)" if settings.demo_mode else "",
        )
    except ProviderError as exc:
        logger.warning("Proveedor no utilizable todavía: %s", exc.message)


if __name__ == "__main__":
    settings = config.load_settings()
    application = create_app(settings)
    _startup_report(application)
    logger.info("Escucha en http://%s:%s", settings.host, settings.port)
    application.run(host=settings.host, port=settings.port, debug=settings.debug)
else:
    # Aplicación a nivel de módulo para servidores WSGI (gunicorn, uwsgi):
    # `gunicorn app:app`, como usa el Dockerfile. Crear la aplicación no lee
    # credenciales ni abre recursos: la configuración se resuelve por petición.
    app = create_app()
