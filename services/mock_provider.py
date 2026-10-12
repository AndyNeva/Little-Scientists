"""Proveedor `mock`: imagen sintética con Pillow.

Doble de pruebas y **modo demostración**. Ignora la fotografía: la imagen
resultante no contiene ningún dato personal. Es la contingencia cuando el proveedor
real falla o se agota la cuota.
"""

from __future__ import annotations

import io
import random

from PIL import Image, ImageDraw

from services.image_generator import ImageGenerator

# Paleta por estilo: cada estilo devuelve una imagen claramente distinta
# (TASKS.md Fase 8: «Verificar que cada estilo produce una transformación distinta»).
_PALETTES: dict[str, tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]] = {
    "superhero": ((255, 87, 87), (255, 195, 0), (40, 40, 90)),
    "royalty": ((186, 104, 200), (255, 224, 130), (60, 20, 80)),
    "astronaut": ((33, 47, 89), (120, 190, 255), (255, 255, 255)),
    "explorer": ((46, 125, 50), (196, 150, 70), (255, 241, 190)),
    "wizard": ((63, 46, 138), (170, 140, 255), (255, 236, 179)),
    "inventor": ((0, 131, 143), (120, 220, 232), (255, 214, 102)),
    "knight": ((96, 110, 130), (200, 210, 225), (255, 205, 120)),
    "ocean": ((0, 105, 148), (0, 180, 180), (255, 170, 90)),
}
_DEFAULT_PALETTE = ((70, 110, 200), (255, 210, 120), (255, 255, 255))

#: El servidor antepone este marcador al prompt (ver `data/transformations.py`)
#: para que cada estilo tenga su propia semilla y su propia paleta. No es un
#: identificador que acepte el cliente: `style_id` se valida contra el catálogo
#: antes de construir el prompt.
STYLE_MARKER_PREFIX = "Style: "


def is_style_marker(line: str) -> bool:
    """Indica si una línea del prompt es el marcador de estilo que añade el servidor."""
    return line.startswith(STYLE_MARKER_PREFIX)


def _palette_for(prompt: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    style_id = ""
    for line in prompt.splitlines():
        if is_style_marker(line):
            style_id = line[len(STYLE_MARKER_PREFIX):].strip().lower()
            break
    return _PALETTES.get(style_id, _DEFAULT_PALETTE)


class MockProvider(ImageGenerator):
    """Genera una ilustración abstracta, colorida y sin datos personales."""

    name = "mock"

    def __init__(self, size: tuple[int, int] = (768, 768)) -> None:
        self._size = size

    def generate(self, image_bytes: bytes, prompt: str) -> bytes:
        primary, secondary, accent = _palette_for(prompt)

        # Semilla derivada del prompt: el mismo estilo da el mismo dibujo (pruebas
        # reproducibles) y estilos distintos dan dibujos distintos.
        rng = random.Random(hash(prompt) & 0xFFFFFFFF)

        width, height = self._size
        image = Image.new("RGB", self._size, primary)
        draw = ImageDraw.Draw(image)

        # Degradado vertical suave.
        for y in range(height):
            ratio = y / max(height - 1, 1)
            color = tuple(
                int(primary[channel] * (1 - ratio) + secondary[channel] * ratio)
                for channel in range(3)
            )
            draw.line([(0, y), (width, y)], fill=color)

        # Estrellas y círculos decorativos.
        for _ in range(60):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            radius = rng.randint(2, 9)
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=accent)

        for _ in range(6):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            radius = rng.randint(40, 140)
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=accent, width=6)

        # Silueta genérica: recuerda a un personaje sin representar a nadie.
        head_radius = width // 7
        head_center = (width // 2, int(height * 0.38))
        draw.ellipse(
            [
                head_center[0] - head_radius,
                head_center[1] - head_radius,
                head_center[0] + head_radius,
                head_center[1] + head_radius,
            ],
            fill=accent,
        )
        body_width = width // 3
        body_top = head_center[1] + head_radius - 10
        draw.rounded_rectangle(
            [
                width // 2 - body_width // 2,
                body_top,
                width // 2 + body_width // 2,
                int(height * 0.95),
            ],
            radius=40,
            fill=accent,
        )

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
