"""Configuración de la aplicación.

Todas las variables se leen del entorno (`.env`), nunca del código ni del cliente.
`.env.example` documenta cada una con su valor por defecto, y
`docs/DEPLOY.md` explica cuáles son obligatorias según el proveedor.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Carga .env si existe. Nunca se registra su contenido.
load_dotenv(BASE_DIR / ".env")

PROVIDERS_VALIDOS = ("cloudflare", "gemini", "mock")


class ConfigError(Exception):
    """Configuración inválida o incompleta. La capa de rutas la traduce a PROVIDER_NOT_CONFIGURED."""


def _env_str(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def _env_int(name: str, default: int) -> int:
    raw = _env_str(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ConfigError(f"La variable {name} debe ser un número entero.") from exc
    return parsed


def _env_float(name: str, default: float) -> float:
    raw = _env_str(name)
    if raw is None:
        return default
    try:
        parsed = float(raw)
    except ValueError as exc:
        raise ConfigError(f"La variable {name} debe ser un número.") from exc
    return parsed


@dataclass(frozen=True)
class Settings:
    """Configuración inmutable de una ejecución."""

    provider: str
    request_timeout_seconds: float
    max_upload_mb: int
    max_name_length: int
    port: int
    host: str
    debug: bool

    cloudflare_account_id: str | None
    cloudflare_api_token: str | None
    cloudflare_model: str | None

    gemini_api_key: str | None
    gemini_model: str | None

    # Preparación de la imagen antes de enviarla al proveedor.
    input_max_side_px: int
    input_jpeg_quality: int

    #: Lado mayor de la foto que se envía a Gemini. Se puede subir sin tocar código.
    gemini_input_max_side_px: int = 1024

    #: Modelo de Gemini por defecto: genera y **edita** imágenes a partir de una
    #: foto de entrada. Confirmado en la documentación oficial.
    gemini_default_model: str = "gemini-nano-banana-2.1"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def demo_mode(self) -> bool:
        """`mock` es a la vez doble de pruebas y modo demostración."""
        return self.provider == "mock"

    def missing_credentials(self) -> list[str]:
        """Variables que faltan para el proveedor activo, sin exponer sus valores.

        Se usa para informar en los logs de la terminal y en `/api/health`; nunca
        se envía ningún valor al navegador.
        """
        if self.provider == "cloudflare":
            return [
                name
                for name, value in (
                    ("CLOUDFLARE_ACCOUNT_ID", self.cloudflare_account_id),
                    ("CLOUDFLARE_API_TOKEN", self.cloudflare_api_token),
                )
                if not value
            ]
        if self.provider == "gemini":
            return ["GEMINI_API_KEY"] if not self.gemini_api_key else []
        return []


def load_settings() -> Settings:
    provider = (_env_str("IMAGE_PROVIDER", "mock") or "mock").lower()
    if provider not in PROVIDERS_VALIDOS:
        raise ConfigError(
            "IMAGE_PROVIDER no es válido. Valores admitidos: "
            + ", ".join(PROVIDERS_VALIDOS)
            + "."
        )

    return Settings(
        provider=provider,
        request_timeout_seconds=_env_float("REQUEST_TIMEOUT_SECONDS", 60.0),
        max_upload_mb=_env_int("MAX_UPLOAD_MB", 8),
        max_name_length=_env_int("MAX_NAME_LENGTH", 20),
        port=_env_int("PORT", 5000),
        host=_env_str("HOST", "127.0.0.1") or "127.0.0.1",
        debug=(_env_str("FLASK_DEBUG", "0") or "0") in {"1", "true", "True"},
        cloudflare_account_id=_env_str("CLOUDFLARE_ACCOUNT_ID"),
        cloudflare_api_token=_env_str("CLOUDFLARE_API_TOKEN"),
        cloudflare_model=_env_str("CLOUDFLARE_MODEL"),
        gemini_api_key=_env_str("GEMINI_API_KEY"),
        gemini_model=_env_str("GEMINI_MODEL"),
        input_max_side_px=_env_int("INPUT_MAX_SIDE_PX", 1024),
        input_jpeg_quality=_env_int("INPUT_JPEG_QUALITY", 90),
        gemini_input_max_side_px=_env_int("GEMINI_INPUT_MAX_SIDE_PX", 1024),
        gemini_default_model=_env_str("GEMINI_DEFAULT_MODEL", "gemini-nano-banana-2.1")
        or "gemini-nano-banana-2.1",
    )
