"""Configuración compartida de las pruebas.

Las pruebas usan `IMAGE_PROVIDER=mock`: no consumen cuota y no usan fotografías
reales (TEST_PLAN.md §1 y §2).
"""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from app import create_app  # noqa: E402

#: Color conocido en la esquina superior izquierda de las imágenes de prueba.
FIXTURE_TOP_LEFT = (12, 24, 36)


def make_test_image_bytes(
    size: tuple[int, int] = (320, 240),
    image_format: str = "JPEG",
    mode: str = "RGB",
    **save_kwargs,
) -> bytes:
    """Imagen de prueba no personal y determinista."""
    if mode == "P":
        image = Image.new("P", size)
        image.putpalette([i % 256 for i in range(768)])
    elif mode == "RGBA":
        image = Image.new(mode, size, (12, 24, 36, 255))
    elif mode == "LA":
        image = Image.new(mode, size, (12, 255))
    else:
        image = Image.new(mode, size, FIXTURE_TOP_LEFT)

    if mode in ("RGB", "RGBA"):
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, size[1] // 2, size[0], size[1]], fill=(200, 210, 90))

    buffer = io.BytesIO()
    image.save(buffer, format=image_format, **save_kwargs)
    return buffer.getvalue()


@pytest.fixture
def settings() -> config.Settings:
    """Configuración de prueba con el proveedor `mock`."""
    return config.Settings(
        provider="mock",
        request_timeout_seconds=5.0,
        max_upload_mb=8,
        max_name_length=20,
        port=5000,
        host="127.0.0.1",
        debug=False,
        cloudflare_account_id=None,
        cloudflare_api_token=None,
        cloudflare_model=None,
        gemini_api_key=None,
        gemini_model=None,
        input_max_side_px=512,
        input_jpeg_quality=85,
    )


@pytest.fixture
def app(settings: config.Settings):
    application = create_app(settings)
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_photo() -> bytes:
    return make_test_image_bytes()


@pytest.fixture(autouse=True)
def _capture_app_logs(caplog):
    """El logger de la aplicación no propaga, así que se engancha caplog a él.

    Así las pruebas pueden comprobar qué se registra realmente (PLAN.md D-10).
    """
    caplog.set_level(logging.INFO, logger="feria_ia")
