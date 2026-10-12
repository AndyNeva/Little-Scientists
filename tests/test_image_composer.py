"""Pruebas de la composición del título con Pillow (TEST_PLAN.md §2)."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from services.image_composer import (
    MAX_TITLE_CHARS,
    build_title,
    compose_with_title,
    resolve_font_path,
)
from tests.conftest import make_test_image_bytes


def _open(payload: bytes) -> Image.Image:
    return Image.open(io.BytesIO(payload))


def test_devuelve_png_valido():
    result = compose_with_title(make_test_image_bytes(image_format="PNG"), "Capitán Valiente", "superhero")
    with _open(result) as image:
        assert image.format == "PNG"


def test_alto_final_es_alto_original_mas_franja_y_ancho_no_cambia():
    original = make_test_image_bytes(size=(320, 240), image_format="PNG")
    result = compose_with_title(original, "Capitán Espacial", "astronaut")

    with _open(original) as before, _open(result) as after:
        assert after.width == before.width
        assert after.height > before.height


def test_imagen_original_no_se_modifica():
    """El título nunca cubre la imagen: los píxeles de arriba se copian tal cual."""
    original = make_test_image_bytes(size=(200, 160), image_format="PNG")
    result = compose_with_title(original, "Guardián del Reino", "knight")

    with _open(original) as before, _open(result) as after:
        original_rgb = before.convert("RGB")
        result_rgb = after.convert("RGB")
        assert result_rgb.size[0] == original_rgb.size[0]

        width, height = original_rgb.size
        for point in [(0, 0), (width - 1, 0), (0, height - 1), (width // 2, height // 2), (width - 1, height - 1)]:
            assert result_rgb.getpixel(point) == original_rgb.getpixel(point)


def test_sin_nombre_usa_titulo_predeterminado():
    assert build_title("", "Capitán Valiente") == "Capitán Valiente"
    assert build_title(None, "Capitán Valiente") == "Capitán Valiente"
    assert build_title("   ", "Capitán Valiente") == "Capitán Valiente"


def test_con_nombre_usa_nombre_coma_titulo():
    assert build_title("Ana", "Capitán Valiente") == "Ana, Capitán Valiente"
    assert build_title("  Ana  ", "Capitán Valiente") == "Ana, Capitán Valiente"


@pytest.mark.parametrize("name", ["José", "Núñez", "Peña", "María José", "O'Connor", "Ana-Lucía"])
def test_acepta_tildes_ene_y_guiones(name: str):
    title = build_title(name, "Genio del Futuro")
    result = compose_with_title(make_test_image_bytes(image_format="PNG"), title, "inventor")
    with _open(result) as image:
        assert image.format == "PNG"


def test_texto_largo_se_ajusta_sin_salirse_de_la_imagen():
    """El texto se reduce, se reparte o se recorta: nunca desborda el ancho."""
    from PIL import ImageDraw

    from services.image_composer import _fit_text, _load_font

    long_title = "Alejandra " * 12
    canvas = Image.new("RGB", (640, 120))
    draw = ImageDraw.Draw(canvas)

    font, lines = _fit_text(draw, long_title[:MAX_TITLE_CHARS], 600, base_size=40)
    assert lines
    for line in lines:
        assert draw.textlength(line, font=font) <= 600

    # Y la composición final tampoco falla con un texto absurdamente largo.
    result = compose_with_title(
        make_test_image_bytes(size=(300, 200), image_format="PNG"),
        long_title,
        "explorer",
    )
    with _open(result) as image:
        assert image.format == "PNG"


@pytest.mark.parametrize("mode", ["RGBA", "LA", "P"])
def test_convierte_imagenes_con_alfa_o_paleta(mode: str):
    source = make_test_image_bytes(size=(180, 140), image_format="PNG", mode=mode)
    result = compose_with_title(source, "Capitán del Océano", "ocean")
    with _open(result) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert image.height > 140


def test_titulo_vacio_no_falla():
    result = compose_with_title(make_test_image_bytes(image_format="PNG"), "   ", "wizard")
    with _open(result) as image:
        assert image.format == "PNG"


def test_hay_tipografia_disponible():
    """Debe existir una tipografía utilizable: incluida en el proyecto o del sistema."""
    assert resolve_font_path() is not None
