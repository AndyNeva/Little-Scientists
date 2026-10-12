"""Preparación de la fotografía recibida.

Requisitos: SPEC.md §7.1 y API.md §4 pasos 1–2. No se confía en la extensión ni
en el MIME declarado por el navegador: el contenido debe decodificarse como una
imagen real. Se corrige la orientación EXIF y se reduce la resolución si hace
falta (PLAN.md Q-04). Nada de esto se escribe en disco.
"""

from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

#: Formatos aceptados (API.md §4).
ALLOWED_FORMATS = ("JPEG", "PNG", "WEBP")

#: Se recodifica a JPEG para el proveedor: elimina metadatos EXIF y reduce el envío.
PROVIDER_IMAGE_FORMAT = "JPEG"


class InvalidImageError(ValueError):
    """El contenido no es una imagen decodificable o su formato no está permitido."""


def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA", "P"):
        converted = image.convert("RGBA")
        background = Image.new("RGB", converted.size, (255, 255, 255))
        background.paste(converted, mask=converted.split()[-1])
        return background
    return image.convert("RGB")


def prepare_for_provider(
    raw_bytes: bytes,
    max_side_px: int = 1024,
    jpeg_quality: int = 90,
) -> tuple[bytes, tuple[int, int], str]:
    """Valida, orienta, reduce y recodifica la fotografía.

    Devuelve `(bytes_jpeg, (ancho, alto), formato_original)`.
    Lanza `InvalidImageError` si el contenido no es una imagen admitida.
    """
    if not raw_bytes:
        raise InvalidImageError("El archivo llegó vacío.")

    try:
        with Image.open(io.BytesIO(raw_bytes)) as opened:
            detected_format = (opened.format or "").upper()
            if detected_format not in ALLOWED_FORMATS:
                raise InvalidImageError(
                    "Formato no admitido. Se aceptan JPEG, PNG o WebP."
                )
            opened.load()

            # Corrige la orientación según EXIF antes de reducir.
            oriented = ImageOps.exif_transpose(opened)
            rgb = _flatten_to_rgb(oriented)
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError("El archivo no es una imagen válida.") from exc

    if max_side_px > 0:
        longest = max(rgb.size)
        if longest > max_side_px:
            scale = max_side_px / longest
            new_size = (
                max(int(rgb.width * scale), 1),
                max(int(rgb.height * scale), 1),
            )
            rgb = rgb.resize(new_size, Image.LANCZOS)

    buffer = io.BytesIO()
    rgb.save(buffer, format=PROVIDER_IMAGE_FORMAT, quality=jpeg_quality, optimize=True)
    return buffer.getvalue(), rgb.size, detected_format
