"""Composición final con Pillow: franja de título debajo de la imagen.

Decisiones: franja de título debajo de la imagen y tipografía libre con soporte de
tildes; requisitos: `docs/SPEC.md` §7.2 y `docs/API.md` §4 paso 6.

El título lo dibuja **siempre** este módulo, nunca la IA, y la franja se añade
debajo de la imagen (el lienzo crece), de modo que el texto nunca cubre el rostro.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
BUNDLED_FONT_DIR = BASE_DIR / "static" / "assets" / "fonts"

#: Nombres esperados de la tipografía incluida (licencia libre OFL).
#: Si el archivo existe se usa esta; si no, se recurre a las fuentes del sistema.
_BUNDLED_FONT_CANDIDATES = (
    "Fredoka-Bold.ttf",
    "Fredoka-SemiBold.ttf",
    "Fredoka-Medium.ttf",
    "Fredoka.ttf",
    "Baloo2.ttf",
    "Nunito-Bold.ttf",
)

#: Peso que se pide a las tipografías variables, en la escala estándar 100–900:
#: 600 = semibold. Fredoka y Baloo 2 usan esa misma escala y ambas ofrecen la
#: instancia «SemiBold», así que no hace falta reescalar. Sin esto, Pillow
#: instancia la fuente en su peso por defecto y el título sale demasiado fino.
_FONT_WEIGHT = 600

_SYSTEM_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\verdanab.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\comicbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
)

# Color de acento por estilo; el fondo de la franja es oscuro para dar contraste.
_ACCENTS: dict[str, str] = {
    "superhero": "#ffb300",
    "royalty": "#ffd54f",
    "astronaut": "#80d8ff",
    "explorer": "#aed581",
    "wizard": "#b388ff",
    "inventor": "#4dd0e1",
    "knight": "#ffcc80",
    "ocean": "#4dd0e1",
}
_DEFAULT_ACCENT = "#ffd166"
_BAND_BG = "#101828"
_TEXT_COLOR = "#ffffff"

#: Longitud máxima del texto dibujado; por encima se recorta con puntos suspensivos.
MAX_TITLE_CHARS = 60
_MAX_LINES = 2


class FontError(RuntimeError):
    """No hay ninguna tipografía utilizable para dibujar el título."""


def resolve_font_path() -> str | None:
    """Primera tipografía disponible: incluida en el proyecto, si no del sistema."""
    for name in _BUNDLED_FONT_CANDIDATES:
        candidate = BUNDLED_FONT_DIR / name
        if candidate.is_file():
            return str(candidate)
    for candidate in _SYSTEM_FONT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return None


def _apply_variation(font: ImageFont.FreeTypeFont) -> None:
    """Fija el peso del título en las tipografías variables (Fredoka, Baloo 2).

    Pillow instancia las fuentes variables en su peso por defecto (300 en Fredoka,
    400 en Baloo 2), demasiado fino para un título infantil. Se pide primero la
    instancia con nombre «SemiBold» y, si no existe, se ajusta el eje numérico.
    """
    try:
        names = font.get_variation_names()
    except (AttributeError, OSError):
        names = ()
    if names:
        for wanted_name in ("SemiBold", "Medium", "Bold"):
            if any(
                (n.decode("utf-8", "ignore") if isinstance(n, bytes) else n) == wanted_name
                for n in names
            ):
                try:
                    font.set_variation_by_name(wanted_name)
                    return
                except (OSError, ValueError):
                    break

    try:
        axes = font.get_variation_axes()
    except (AttributeError, OSError):
        return

    wanted: list[float] = []
    for axis in axes:
        default = float(axis.get("default", 0) or 0)
        name = axis.get("name") or b""
        if isinstance(name, bytes):
            name = name.decode("utf-8", "ignore")
        if name.lower().replace(" ", "") in {"weight", "wght"}:
            low = float(axis.get("minimum", default))
            high = float(axis.get("maximum", default))
            wanted.append(min(max(float(_FONT_WEIGHT), low), high))
        else:
            wanted.append(default)

    try:
        font.set_variation_by_axes(wanted)
    except (OSError, ValueError, TypeError):
        pass


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(size, 8)
    path = resolve_font_path()
    if path is not None:
        try:
            font = ImageFont.truetype(path, size=size)
            _apply_variation(font)
            return font
        except OSError:
            pass
    try:
        # Pillow ≥ 9.2 admite tamaño en la fuente por defecto (soporta acentos y ñ).
        return ImageFont.load_default(size=size)
    except TypeError:  # pragma: no cover - Pillow muy antiguo
        font = ImageFont.load_default()
        if font is None:  # pragma: no cover
            raise FontError("No hay ninguna tipografía disponible.")
        return font


def build_title(name: str | None, default_title: str) -> str:
    """Sin nombre → título predeterminado; con nombre → «{nombre}, {título}»."""
    clean_name = (name or "").strip()
    if not clean_name:
        return default_title
    return f"{clean_name}, {default_title}"


def _fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    base_size: int,
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, list[str]]:
    """Reduce el tamaño y, si hace falta, reparte el texto en dos líneas centradas."""
    min_size = max(int(base_size * 0.55), 10)

    for size in range(base_size, min_size - 1, -1):
        font = _load_font(size)
        lines = _wrap(draw, text, font, max_width, max_lines=_MAX_LINES)
        if all(draw.textlength(line, font=font) <= max_width for line in lines):
            return font, lines

    font = _load_font(min_size)
    lines = _wrap(draw, text, font, max_width, max_lines=_MAX_LINES)
    return font, [_truncate(draw, line, font, max_width) for line in lines]


def _wrap(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    """Reparte en como mucho `max_lines` líneas, respetando palabras cuando se puede."""
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=font) > max_width and len(lines) + 1 < max_lines:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)

    # Si aún sobra texto en la última línea, se recorta aquí.
    return lines[:max_lines]


def _truncate(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    ellipsis = "…"
    trimmed = text
    while trimmed and draw.textlength(trimmed + ellipsis, font=font) > max_width:
        trimmed = trimmed[:-1]
    return (trimmed.rstrip() + ellipsis) if trimmed else ellipsis


def compose_with_title(
    image_bytes: bytes,
    title: str,
    style_id: str | None = None,
) -> bytes:
    """Añade una franja con el título debajo de la imagen y devuelve un PNG.

    - El alto final = alto original + alto de la franja; el ancho no cambia.
    - La zona de la imagen original se copia sin modificar ningún píxel.
    """
    clean_title = (title or "").strip()[:MAX_TITLE_CHARS] or "Personaje"

    with Image.open(io.BytesIO(image_bytes)) as opened:
        opened.load()
        # Modos con alfa, máscara o paleta se aplanan para exportar PNG sin sorpresas.
        if opened.mode in ("RGBA", "LA", "P", "PA"):
            source = opened.convert("RGBA")
            flattened = Image.new("RGB", source.size, (255, 255, 255))
            flattened.paste(source, mask=source.split()[-1])
            base = flattened
        else:
            base = opened.convert("RGB")

    width, height = base.size
    band_height = max(int(height * 0.16), 64)
    base_size = max(int(band_height * 0.42), 14)

    canvas = Image.new("RGB", (width, height + band_height), _BAND_BG)
    canvas.paste(base, (0, 0))

    draw = ImageDraw.Draw(canvas)
    accent = ImageColor.getrgb(_ACCENTS.get(style_id or "", _DEFAULT_ACCENT))
    draw.rectangle([0, height, width, height + max(band_height // 12, 4)], fill=accent)

    font, lines = _fit_text(draw, clean_title, int(width * 0.92), base_size)
    text_color = ImageColor.getrgb(_TEXT_COLOR)

    line_height = int(base_size * 1.2)
    total_height = line_height * len(lines)
    text_top = height + (band_height - total_height) // 2

    for index, line in enumerate(lines):
        line_width = draw.textlength(line, font=font)
        draw.text(
            ((width - line_width) / 2, text_top + index * line_height),
            line,
            font=font,
            fill=text_color,
        )

    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()
