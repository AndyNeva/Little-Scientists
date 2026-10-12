"""Factoría de proveedores.

Selecciona el adaptador según `IMAGE_PROVIDER`. El resto de la aplicación depende
solo de la interfaz `ImageGenerator`.
"""

from __future__ import annotations

import config
from services.cloudflare_provider import CloudflareProvider
from services.gemini_provider import GeminiProvider
from services.image_generator import ImageGenerator, ProviderNotConfigured
from services.mock_provider import MockProvider


def build_provider(settings: config.Settings) -> ImageGenerator:
    """Construye el proveedor configurado.

    Lanza `ProviderNotConfigured` si `IMAGE_PROVIDER` no es válido o si faltan
    credenciales para el proveedor elegido.
    """
    provider = (settings.provider or "").lower()

    if provider == "mock":
        return MockProvider()
    if provider == "cloudflare":
        return CloudflareProvider(
            account_id=settings.cloudflare_account_id,
            api_token=settings.cloudflare_api_token,
            model=settings.cloudflare_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    if provider == "gemini":
        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            timeout_seconds=settings.request_timeout_seconds,
            input_max_side_px=settings.gemini_input_max_side_px,
        )

    raise ProviderNotConfigured(
        "IMAGE_PROVIDER no es válido. Valores admitidos: cloudflare, gemini, mock."
    )
