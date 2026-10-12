"""Catálogo de transformaciones y construcción del prompt.

Fuente de redacción: `PROMPTS.md` §2 y §3. El prompt se construye **solo en el
servidor** (PLAN.md D-06); el navegador únicamente envía `style_id`.
"""

from __future__ import annotations

from typing import Any, Mapping

#: Marcador interno que el servidor antepone al prompt (ver `build_prompt`).
STYLE_MARKER_PREFIX = "Style: "

# --- Bloque común (PROMPTS.md §2) -------------------------------------------------

COMMON_PROMPT = """Transform the person in this photo into the character described below.
Keep the person's recognizable facial features, apparent age, skin tone, hair
and expression. The person must still look like the same child, not an adult.
Show head and upper body, facing the camera, with the face fully visible and
unobstructed. Friendly, cheerful, colorful storybook illustration style that is
safe and appropriate for all ages. No weapons, no scary or violent elements.
Do not add any text, letters, numbers, logos or watermarks."""


class UnknownStyleError(KeyError):
    """El `style_id` no existe en el catálogo."""


# --- Catálogo (SPEC.md §3, PROMPTS.md §3, UI_COPY.md §1) --------------------------

TRANSFORMATIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "superhero",
        "label": "Superhéroe",
        "description": "Vuela con tu capa y salva el día.",
        "default_title": "Capitán Valiente",
        "style_prompt": (
            "Character: a friendly superhero in a bright, colorful costume with a "
            "flowing cape and a star emblem on the chest. No mask covering the face. "
            "Background: a sunny city skyline at sunrise."
        ),
    },
    {
        "id": "royalty",
        "label": "Princesa o príncipe",
        "description": "Un reino de fantasía te espera.",
        "default_title": "Realeza de Fantasía",
        "style_prompt": (
            "Character: fantasy royalty wearing rich, colorful royal clothes and a "
            "small golden crown or circlet. Background: a magical castle garden with "
            "soft sparkles. The outfit suits any child."
        ),
    },
    {
        "id": "astronaut",
        "label": "Astronauta",
        "description": "Explora el espacio con tu traje espacial.",
        "default_title": "Capitán Espacial",
        "style_prompt": (
            "Character: a young astronaut in a white and blue space suit, with the "
            "helmet held under the arm or the visor fully open so the face is clearly "
            "visible. Background: stars and a colorful planet."
        ),
    },
    {
        "id": "explorer",
        "label": "Explorador de aventuras",
        "description": "Descubre selvas y tesoros escondidos.",
        "default_title": "Explorador de Mundos",
        "style_prompt": (
            "Character: an adventure explorer with a safari hat, a backpack and "
            "binoculars around the neck. Background: a lush, friendly jungle with an "
            "old treasure map."
        ),
    },
    {
        "id": "wizard",
        "label": "Mago o maga",
        "description": "Haz magia con tu varita brillante.",
        "default_title": "Maestro de la Magia",
        "style_prompt": (
            "Character: a wizard in a starry robe and a pointed hat, holding a glowing "
            "magic wand with soft sparkles. Background: a cozy magical library with "
            "floating books."
        ),
    },
    {
        "id": "inventor",
        "label": "Inventor futurista",
        "description": "Crea robots e inventos del futuro.",
        "default_title": "Genio del Futuro",
        "style_prompt": (
            "Character: a futuristic inventor with goggles resting on the forehead and "
            "a tool belt. Background: a bright workshop with small friendly robots and "
            "glowing blueprints."
        ),
    },
    {
        "id": "knight",
        "label": "Caballero o guardiana",
        "description": "Protege un castillo de cuento.",
        "default_title": "Guardián del Reino",
        "style_prompt": (
            "Character: a storybook knight in shiny friendly armor, with the helmet "
            "held under the arm so the face is visible, and a decorative shield. No "
            "weapons. Background: a fairytale castle on a green hill."
        ),
    },
    {
        "id": "ocean",
        "label": "Explorador submarino",
        "description": "Sumérgete entre peces y corales.",
        "default_title": "Capitán del Océano",
        "style_prompt": (
            "Character: an underwater explorer in a retro-futuristic diving suit, with "
            "the helmet visor transparent or open. Background: a colorful coral reef "
            "with friendly fish and soft rays of light."
        ),
    },
)

_BY_ID: dict[str, dict[str, Any]] = {item["id"]: item for item in TRANSFORMATIONS}


def get_style(style_id: str) -> Mapping[str, Any]:
    """Devuelve el estilo del catálogo o lanza `UnknownStyleError`."""
    try:
        return _BY_ID[style_id]
    except (KeyError, TypeError) as exc:
        raise UnknownStyleError(style_id) from exc


def build_prompt(style_id: str) -> str:
    """Prompt final = bloque común + bloque del estilo (PROMPTS.md §3).

    Se antepone un marcador con el `style_id` ya validado. Es un detalle interno
    del servidor: el cliente no puede enviar ni alterar esta línea, y los
    proveedores pueden usarla para distinguir estilos (por ejemplo `mock`, que
    elige paleta y semilla a partir de ella).
    """
    style = get_style(style_id)
    return f"{STYLE_MARKER_PREFIX}{style['id']}\n{COMMON_PROMPT}\n{style['style_prompt']}"


def public_catalog() -> list[dict[str, str]]:
    """Catálogo para `GET /api/transformations`. **No expone el prompt** (API.md §3)."""
    return [
        {
            "id": item["id"],
            "label": item["label"],
            "description": item["description"],
            "default_title": item["default_title"],
        }
        for item in TRANSFORMATIONS
    ]
