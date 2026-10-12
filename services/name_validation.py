"""Validación del nombre opcional del participante.

Reglas: `docs/API.md` §4 — tras recortar espacios, entre 1 y
`MAX_NAME_LENGTH` caracteres; solo letras Unicode, espacios, guion y apóstrofo.
No se usa como identificador de sesión ni como nombre de archivo.
"""

from __future__ import annotations

import unicodedata

#: Caracteres permitidos además de las letras: espacio, guion y apóstrofo (varias formas).
_EXTRA_ALLOWED = {" ", "-", "'", "\u2019", "\u02bc", "\u2010", "\u2011"}


class InvalidNameError(ValueError):
    """El nombre no cumple las reglas."""


def normalize_name(raw: str | None, max_length: int = 20) -> str:
    """Devuelve el nombre limpio, o cadena vacía si no se envió nombre.

    Lanza `InvalidNameError` si incumple las reglas.
    """
    if raw is None:
        return ""

    name = unicodedata.normalize("NFC", str(raw)).strip()
    # Se colapsan espacios repetidos para no dibujar huecos raros en el título.
    name = " ".join(name.split())

    if not name:
        return ""

    if len(name) > max_length:
        raise InvalidNameError(
            f"El nombre no puede superar {max_length} caracteres."
        )

    for character in name:
        if character in _EXTRA_ALLOWED:
            continue
        if character.isalpha():
            continue
        raise InvalidNameError("El nombre solo admite letras, espacios y guiones.")

    return name
