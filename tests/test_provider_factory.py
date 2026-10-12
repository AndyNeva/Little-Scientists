"""Pruebas de la factoría de proveedores (TEST_PLAN.md §2)."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from services.image_generator import ImageGenerator, ProviderError, ProviderNotConfigured
from services.mock_provider import MockProvider
from services.provider_factory import build_provider
from data.transformations import TRANSFORMATIONS, build_prompt


def test_mock_devuelve_un_image_generator(settings):
    provider = build_provider(settings)
    assert isinstance(provider, ImageGenerator)
    assert provider.name == "mock"


def test_valor_desconocido_lanza_error_de_configuracion(settings):
    broken = settings.__class__(**{**settings.__dict__, "provider": "otro"})
    with pytest.raises(ProviderNotConfigured):
        build_provider(broken)


def test_cloudflare_sin_credenciales_no_esta_configurado(settings):
    broken = settings.__class__(**{**settings.__dict__, "provider": "cloudflare"})
    provider = build_provider(broken)
    with pytest.raises(ProviderNotConfigured):
        provider.generate(b"datos", "prompt")


def test_cloudflare_con_credenciales_construye_el_proveedor(settings):
    """Con credenciales, la factoría devuelve el proveedor real y el modelo validado."""
    from services.cloudflare_provider import MODEL, CloudflareProvider

    configurado = settings.__class__(
        **{
            **settings.__dict__,
            "provider": "cloudflare",
            "cloudflare_account_id": "cuenta-de-prueba",
            "cloudflare_api_token": "token-de-prueba",
            "cloudflare_model": None,
        }
    )
    provider = build_provider(configurado)

    assert isinstance(provider, CloudflareProvider)
    assert provider.name == "cloudflare"
    assert provider._model == MODEL


def test_cloudflare_sin_modelo_usa_el_validado(settings):
    """No hace falta fijar CLOUDFLARE_MODEL: el valor por defecto es el modelo validado."""
    from services.cloudflare_provider import MODEL, CloudflareProvider

    sin_modelo = settings.__class__(
        **{
            **settings.__dict__,
            "provider": "cloudflare",
            "cloudflare_account_id": "cuenta",
            "cloudflare_api_token": "token",
            "cloudflare_model": "",
        }
    )
    assert build_provider(sin_modelo)._model == MODEL


def test_cloudflare_respeta_el_modelo_configurado(settings):
    elegido = settings.__class__(
        **{
            **settings.__dict__,
            "provider": "cloudflare",
            "cloudflare_account_id": "cuenta",
            "cloudflare_api_token": "token",
            "cloudflare_model": "@cf/otro/modelo",
        }
    )
    assert build_provider(elegido)._model == "@cf/otro/modelo"


def test_gemini_sin_credenciales_no_esta_configurado(settings):
    broken = settings.__class__(**{**settings.__dict__, "provider": "gemini"})
    with pytest.raises(ProviderNotConfigured):
        build_provider(broken).generate(b"datos", "prompt")


def test_mock_generate_devuelve_imagen_decodificable():
    payload = MockProvider().generate(b"", "superhero character")
    with Image.open(io.BytesIO(payload)) as image:
        assert image.format == "PNG"
        assert image.width > 0 and image.height > 0


def test_mock_generate_es_reproducible_por_prompt():
    provider = MockProvider(size=(128, 128))
    assert provider.generate(b"", "prompt estable") == provider.generate(b"", "prompt estable")


def test_mock_generate_produce_imagenes_distintas_por_estilo():
    """TASKS.md Fase 8: cada estilo debe producir una transformación distinta."""
    provider = MockProvider(size=(128, 128))
    salidas = {style["id"]: provider.generate(b"", build_prompt(style["id"])) for style in TRANSFORMATIONS}

    assert len(set(salidas.values())) == len(TRANSFORMATIONS)
    assert len(salidas) == 8


def test_mock_usa_la_paleta_del_estilo_del_prompt():
    """Dos estilos cuyos prompts comparten palabras no deben confundirse."""
    from services.mock_provider import _palette_for

    ocean = _palette_for(build_prompt("ocean"))
    explorer = _palette_for(build_prompt("explorer"))
    astronaut = _palette_for(build_prompt("astronaut"))

    assert ocean != explorer
    assert ocean != astronaut
    assert explorer != astronaut


def test_mock_ignora_la_fotografia():
    """El modo demostración no usa la foto: la salida no depende de la entrada."""
    provider = MockProvider(size=(96, 96))
    assert provider.generate(b"foto-de-una-persona", "wizard") == provider.generate(b"", "wizard")


def test_provider_error_base_tiene_codigo():
    assert ProviderError().code == "PROVIDER_ERROR"
