"""Pruebas del proveedor Gemini (TEST_PLAN.md §2).

No hay clave de API todavía, así que la capa del SDK está simulada: estas pruebas
**no** llaman a Google ni gastan cuota.

Se cubren dos caminos:

1. **Cliente simulado**: se inyecta un cliente falso y se comprueba el contrato
   (entrada, extracción de la imagen, traducción de errores).
2. **SDK real instalado**: se comprueba que la construcción de las partes
   multimodales funciona con `google.genai.types` de verdad, que es lo que se
   rompería al cambiar de versión del SDK.
"""

from __future__ import annotations

import base64
import io
from types import SimpleNamespace

import pytest
from PIL import Image

from services.gemini_provider import (
    DEFAULT_MODEL,
    GeminiProvider,
    _extract_image,
    _shrink,
)
from services.image_generator import (
    ProviderBadResponse,
    ProviderError,
    ProviderNotConfigured,
    ProviderRateLimit,
    ProviderTimeout,
)
from tests.conftest import make_test_image_bytes

CLAVE = "clave-de-prueba-no-real"


# ------------------------------------------------------------------ utilidades


def _png_bytes(size=(64, 64)) -> bytes:
    return make_test_image_bytes(size=size, image_format="PNG")


def _respuesta_con_imagen(size=(48, 48)) -> SimpleNamespace:
    """Respuesta con la misma forma que la del SDK: objetos con `inline_data`."""
    parte_texto = SimpleNamespace(text="Aquí tienes tu personaje.", inline_data=None)
    parte_imagen = SimpleNamespace(
        text=None, inline_data=SimpleNamespace(data=_png_bytes(size), mime_type="image/png")
    )
    return SimpleNamespace(parts=[parte_texto, parte_imagen])


class _FakeModels:
    def __init__(self, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def generate_content(self, model=None, contents=None):
        self.calls.append({"model": model, "contents": contents})
        if self.error is not None:
            raise self.error
        return self.response


class _FakeClient:
    def __init__(self, response=None, error: Exception | None = None):
        self.models = _FakeModels(response=response, error=error)


def _provider(client=None, **kwargs) -> GeminiProvider:
    return GeminiProvider(api_key=CLAVE, client=client, **kwargs)


# --------------------------------------------------------------- configuración


def test_sin_clave_no_esta_configurado():
    with pytest.raises(ProviderNotConfigured) as info:
        GeminiProvider(api_key=None).generate(_png_bytes(), "prompt")
    assert "GEMINI_API_KEY" in str(info.value)


def test_clave_vacia_no_esta_configurado():
    with pytest.raises(ProviderNotConfigured):
        GeminiProvider(api_key="   ").generate(_png_bytes(), "prompt")


def test_sin_cliente_no_esta_configurado(settings):
    """Sin credencial y sin cliente, la factoría avisa en vez de fallar de forma opaca."""
    from services.provider_factory import build_provider

    gemini = settings.__class__(**{**settings.__dict__, "provider": "gemini"})
    with pytest.raises(ProviderNotConfigured):
        build_provider(gemini).generate(_png_bytes(), "prompt")


def test_usa_el_modelo_confirmado_por_defecto():
    provider = _provider(client=_FakeClient(_respuesta_con_imagen()))
    assert provider._model == DEFAULT_MODEL
    assert DEFAULT_MODEL == "gemini-nano-banana-2.1"


def test_respeta_el_modelo_configurado():
    provider = _provider(client=_FakeClient(_respuesta_con_imagen()), model="gemini-2.5-flash-image")
    assert provider._model == "gemini-2.5-flash-image"


# ------------------------------------------------------------------- contrato


def test_devuelve_la_imagen_de_la_respuesta():
    cliente = _FakeClient(_respuesta_con_imagen())
    resultado = _provider(client=cliente).generate(_png_bytes(), "prompt")

    with Image.open(io.BytesIO(resultado)) as image:
        assert image.format == "PNG"


def test_envia_el_modelo_y_el_prompt_al_sdk():
    cliente = _FakeClient(_respuesta_con_imagen())
    _provider(client=cliente).generate(_png_bytes(), "Transform into an astronaut")

    llamada = cliente.models.calls[0]
    assert llamada["model"] == DEFAULT_MODEL

    contenido = llamada["contents"]
    assert len(contenido) == 2
    # Con el SDK real las partes son objetos; con el simulado, dicts legibles.
    texto = getattr(contenido[0], "text", None) or contenido[0]
    assert "Transform into an astronaut" in texto
    assert "Edit the attached photo" in texto


def test_envia_la_foto_como_segunda_parte():
    cliente = _FakeClient(_respuesta_con_imagen())
    _provider(client=cliente).generate(_png_bytes(), "prompt")

    contenido = cliente.models.calls[0]["contents"]
    segunda = contenido[1]
    inline = getattr(segunda, "inline_data", None)
    if inline is None:
        assert segunda["mime_type"] == "image/jpeg"
        assert len(segunda["data"]) > 0
    else:
        assert inline.mime_type == "image/jpeg"
        assert len(inline.data) > 0


def test_la_clave_no_aparece_en_los_datos_enviados():
    cliente = _FakeClient(_respuesta_con_imagen())
    _provider(client=cliente).generate(_png_bytes(), "prompt")

    from services.gemini_provider import _INPUT_INSTRUCTION

    contenido = cliente.models.calls[0]["contents"]
    texto = getattr(contenido[0], "text", None) or contenido[0]
    assert CLAVE not in texto
    assert CLAVE not in _INPUT_INSTRUCTION


def test_la_foto_se_reduce_al_maximo_configurado():
    preparada = _shrink(make_test_image_bytes(size=(2200, 1100), image_format="JPEG"), 1024)
    with Image.open(io.BytesIO(preparada)) as image:
        assert max(image.size) == 1024
        assert image.width == 2 * image.height

    pequena = make_test_image_bytes(size=(300, 200), image_format="JPEG")
    assert len(_shrink(pequena, 1024)) > 0


def test_foto_ilegible_no_llega_al_sdk():
    cliente = _FakeClient(_respuesta_con_imagen())
    with pytest.raises(ProviderBadResponse):
        _provider(client=cliente).generate(b"no soy una imagen", "prompt")
    assert cliente.models.calls == []


# --------------------------------------------------------- extracción de imagen


def test_rechaza_respuesta_sin_imagen():
    respuesta = SimpleNamespace(parts=[SimpleNamespace(text="No puedo ayudarte con eso.", inline_data=None)])
    with pytest.raises(ProviderBadResponse) as info:
        _provider(client=_FakeClient(respuesta)).generate(_png_bytes(), "prompt")
    assert "Gemini" in str(info.value)


def test_rechaza_respuesta_sin_partes():
    with pytest.raises(ProviderBadResponse):
        _provider(client=_FakeClient(SimpleNamespace(parts=[]))).generate(_png_bytes(), "prompt")


def test_rechaza_datos_que_no_son_imagen():
    parte = SimpleNamespace(text=None, inline_data=SimpleNamespace(data=b"esto no es una imagen"))
    with pytest.raises(ProviderBadResponse):
        _provider(client=_FakeClient(SimpleNamespace(parts=[parte]))).generate(_png_bytes(), "prompt")


def test_acepta_candidatos_anidados():
    """Algunas respuestas traen la imagen dentro de `candidates[].content.parts`."""
    parte = SimpleNamespace(text=None, inline_data=SimpleNamespace(data=_png_bytes()))
    respuesta = SimpleNamespace(
        parts=None,
        candidates=[SimpleNamespace(content=SimpleNamespace(parts=[parte]))],
    )
    assert _extract_image(respuesta) is not None


def test_acepta_base64_en_texto():
    crudo = _png_bytes()
    parte = SimpleNamespace(text=None, inline_data=SimpleNamespace(data=base64.b64encode(crudo).decode()))
    assert _extract_image(SimpleNamespace(parts=[parte])) == crudo


# ------------------------------------------------------------------- errores


@pytest.mark.parametrize(
    ("mensaje", "esperado"),
    [
        ("429 RESOURCE_EXHAUSTED: quota exceeded", ProviderRateLimit),
        ("Quota exceeded for quota metric", ProviderRateLimit),
        ("504 Deadline Exceeded", ProviderTimeout),
        ("Request timed out", ProviderTimeout),
        ("401 UNAUTHENTICATED: API key not valid", ProviderNotConfigured),
        ("403 PERMISSION_DENIED", ProviderNotConfigured),
        ("400 INVALID_ARGUMENT", ProviderBadResponse),
        ("algo raro del servidor", ProviderError),
    ],
)
def test_errores_del_sdk_se_traducen(mensaje: str, esperado):
    cliente = _FakeClient(error=RuntimeError(mensaje))
    with pytest.raises(esperado):
        _provider(client=cliente).generate(_png_bytes(), "prompt")


def test_el_error_de_credenciales_explica_que_revisar():
    cliente = _FakeClient(error=RuntimeError("401 API key not valid"))
    with pytest.raises(ProviderNotConfigured) as info:
        _provider(client=cliente).generate(_png_bytes(), "prompt")

    mensaje = str(info.value)
    assert "GEMINI_API_KEY" in mensaje
    assert CLAVE not in mensaje


def test_ningun_error_del_proveedor_filtra_la_clave():
    for texto in ("429 cuota", "401 no válida", "timeout", "error raro"):
        cliente = _FakeClient(error=RuntimeError(f"{texto} con {CLAVE}"))
        with pytest.raises(ProviderError) as info:
            _provider(client=cliente).generate(_png_bytes(), "prompt")
        assert CLAVE not in str(info.value)


# ------------------------------------------------- integración con el SDK real


def test_las_partes_multimodales_funcionan_con_el_sdk_real():
    """Comprueba la integración real con `google.genai.types` (sin llamar a la API)."""
    types = pytest.importorskip("google.genai.types")

    provider = GeminiProvider(api_key=CLAVE, client=_FakeClient(_respuesta_con_imagen()))
    contents = provider._build_contents(_png_bytes(), "prompt de estilo", types)

    assert len(contents) == 2
    assert "prompt de estilo" in contents[0].text
    assert contents[1].inline_data.mime_type == "image/jpeg"
    assert bytes(contents[1].inline_data.data) == _png_bytes()


def test_el_sdk_declara_el_modelo_por_defecto_como_valido():
    """El nombre del modelo debe existir en la lista que publica el propio SDK."""
    genai = pytest.importorskip("google.genai")
    try:
        modelos = [m.name for m in genai.Client(api_key="falsa").models.list()]
    except Exception:
        pytest.skip("Requiere red o credenciales para listar modelos.")

    if modelos:
        assert any(DEFAULT_MODEL in (nombre or "") for nombre in modelos)
