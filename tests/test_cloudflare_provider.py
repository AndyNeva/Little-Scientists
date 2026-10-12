"""Pruebas del proveedor Cloudflare (`docs/TEST_PLAN.md` §2).

La capa HTTP está simulada: estas pruebas **no** consumen cuota ni envían
fotografías a internet.
"""

from __future__ import annotations

import base64
import io
import json

import pytest
import requests
from PIL import Image

from services.cloudflare_provider import (
    MODEL,
    CloudflareProvider,
    _extract_image,
    _shrink_for_model,
)
from services.image_generator import (
    ProviderBadResponse,
    ProviderError,
    ProviderNotConfigured,
    ProviderRateLimit,
    ProviderTimeout,
)
from tests.conftest import make_test_image_bytes

CUENTA = "3f9459c7ef76981d962a7ef9061103f5"
TOKEN = "token-de-prueba"


class _FakeResponse:
    def __init__(self, status_code: int = 200, json_body=None, content: bytes = b"", headers=None):
        self.status_code = status_code
        self._json = json_body
        self.content = content
        self.headers = headers or {}
        self.text = json.dumps(json_body) if json_body is not None else ""

    def json(self):
        if self._json is None:
            raise ValueError("sin JSON")
        return self._json


class _FakeSession:
    """Captura la petición para poder inspeccionarla y devuelve lo que se le indique."""

    def __init__(self, response: _FakeResponse | None = None, raise_error: Exception | None = None):
        self.response = response
        self.raise_error = raise_error
        self.calls: list[dict] = []

    def post(self, url, headers=None, files=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "files": files, "timeout": timeout})
        if self.raise_error is not None:
            raise self.raise_error
        return self.response


def _provider(session: _FakeSession, model: str | None = None) -> CloudflareProvider:
    return CloudflareProvider(
        account_id=CUENTA,
        api_token=TOKEN,
        model=model,
        timeout_seconds=45,
        session=session,
    )


def _png_bytes(size=(64, 64)) -> bytes:
    return make_test_image_bytes(size=size, image_format="PNG")


def _b64_image_payload(size=(48, 48)) -> dict:
    return {
        "result": {"image": base64.b64encode(_png_bytes(size)).decode()},
        "success": True,
        "errors": [],
        "messages": [],
    }


# --------------------------------------------------------------- configuración


def test_sin_credenciales_no_esta_configurado():
    provider = CloudflareProvider(account_id=None, api_token=None)
    with pytest.raises(ProviderNotConfigured):
        provider.generate(_png_bytes(), "prompt")


def test_sin_token_no_esta_configurado():
    provider = CloudflareProvider(account_id=CUENTA, api_token="")
    with pytest.raises(ProviderNotConfigured):
        provider.generate(_png_bytes(), "prompt")


def test_usa_el_modelo_validado_por_defecto():
    provider = CloudflareProvider(account_id=CUENTA, api_token=TOKEN)
    assert provider._model == MODEL
    assert MODEL == "@cf/black-forest-labs/flux-2-klein-9b"
    assert provider._url.endswith(f"/ai/run/{MODEL}")


def test_la_url_lleva_la_cuenta_y_el_endpoint_correctos():
    session = _FakeSession(_FakeResponse(200, _b64_image_payload()))
    _provider(session).generate(_png_bytes(), "prompt")

    url = session.calls[0]["url"]
    assert url == f"https://api.cloudflare.com/client/v4/accounts/{CUENTA}/ai/run/{MODEL}"


# ------------------------------------------------------- forma de la petición


def test_envia_multipart_con_la_imagen_en_input_image_0():
    session = _FakeSession(_FakeResponse(200, _b64_image_payload()))
    _provider(session).generate(_png_bytes(), "Transform into an astronaut")

    files = session.calls[0]["files"]
    assert "input_image_0" in files
    nombre, contenido, tipo = files["input_image_0"]
    assert nombre.endswith(".jpg") and tipo == "image/jpeg" and len(contenido) > 0
    assert files["prompt"] == "Transform into an astronaut"


def test_envia_autorizacion_bearer_y_tiempo_de_espera():
    session = _FakeSession(_FakeResponse(200, _b64_image_payload()))
    _provider(session).generate(_png_bytes(), "prompt")

    assert session.calls[0]["headers"]["Authorization"] == f"Bearer {TOKEN}"
    assert session.calls[0]["timeout"] == 45


def test_la_clave_no_aparece_en_la_url():
    session = _FakeSession(_FakeResponse(200, _b64_image_payload()))
    _provider(session).generate(_png_bytes(), "prompt")
    assert TOKEN not in session.calls[0]["url"]


def test_la_imagen_de_entrada_se_reduce_al_maximo_configurado():
    """El adaptador recorta la foto a `MAX_INPUT_SIDE_PX`, conservando proporción."""
    from services.cloudflare_provider import MAX_INPUT_SIDE_PX

    grande = make_test_image_bytes(size=(2000, 1000), image_format="JPEG")
    preparada = _shrink_for_model(grande)

    with Image.open(io.BytesIO(preparada)) as image:
        assert max(image.size) == MAX_INPUT_SIDE_PX
        # Se conserva la proporción 2:1.
        assert image.width == 2 * image.height

    # Una imagen ya pequeña no se toca.
    pequena = make_test_image_bytes(size=(300, 200), image_format="JPEG")
    assert _shrink_for_model(pequena) == pequena


def test_pide_el_lienzo_cuadrado_que_devuelve_el_modelo():
    """Medido: el modelo devuelve 1024×1024 aunque la foto sea vertical u horizontal."""
    session = _FakeSession(_FakeResponse(200, _b64_image_payload()))
    _provider(session).generate(make_test_image_bytes(size=(900, 600), image_format="JPEG"), "prompt")

    files = session.calls[0]["files"]
    assert files["width"] == "1024"
    assert files["height"] == "1024"


# ------------------------------------------------------------- interpretación


def test_devuelve_la_imagen_desde_base64():
    session = _FakeSession(_FakeResponse(200, _b64_image_payload()))
    resultado = _provider(session).generate(_png_bytes(), "prompt")

    with Image.open(io.BytesIO(resultado)) as image:
        assert image.format == "PNG"


def test_acepta_imagen_como_bytes_crudos():
    crudo = _png_bytes()
    session = _FakeSession(
        _FakeResponse(200, content=crudo, headers={"Content-Type": "image/png"})
    )
    assert _provider(session).generate(_png_bytes(), "prompt") == crudo


def test_acepta_data_url_base64():
    crudo = _png_bytes()
    data_url = "data:image/png;base64," + base64.b64encode(crudo).decode()
    assert _extract_image({"image": data_url}) == crudo


def test_rechaza_respuesta_sin_imagen():
    payload = {"result": {"otra_cosa": 1}, "success": True, "errors": [], "messages": []}
    session = _FakeSession(_FakeResponse(200, payload))
    with pytest.raises(ProviderBadResponse):
        _provider(session).generate(_png_bytes(), "prompt")


def test_rechaza_datos_que_no_son_imagen():
    payload = {"result": {"image": base64.b64encode(b"esto no es una imagen").decode()},
               "success": True, "errors": [], "messages": []}
    session = _FakeSession(_FakeResponse(200, payload))
    with pytest.raises(ProviderBadResponse):
        _provider(session).generate(_png_bytes(), "prompt")


def test_success_false_se_convierte_en_bad_response():
    payload = {"result": None, "success": False,
               "errors": [{"code": 7000, "message": "model error"}], "messages": []}
    session = _FakeSession(_FakeResponse(200, payload))
    with pytest.raises(ProviderBadResponse):
        _provider(session).generate(_png_bytes(), "prompt")


# ------------------------------------------------------------------- errores


@pytest.mark.parametrize(
    ("status", "esperado"),
    [
        (401, ProviderNotConfigured),
        (403, ProviderNotConfigured),
        (429, ProviderRateLimit),
        (408, ProviderTimeout),
        (400, ProviderBadResponse),
        (404, ProviderBadResponse),
        (500, ProviderBadResponse),
        (503, ProviderBadResponse),
    ],
)
def test_codigos_http_se_traducen(status: int, esperado):
    session = _FakeSession(_FakeResponse(status, {"success": False, "errors": [{"message": "x"}]}))
    with pytest.raises(esperado):
        _provider(session).generate(_png_bytes(), "prompt")


def test_el_401_explica_que_revisar():
    session = _FakeSession(_FakeResponse(401, {"success": False, "errors": []}))
    with pytest.raises(ProviderNotConfigured) as info:
        _provider(session).generate(_png_bytes(), "prompt")

    mensaje = str(info.value)
    assert "Workers AI" in mensaje and "CLOUDFLARE_ACCOUNT_ID" in mensaje
    assert TOKEN not in mensaje


def test_timeout_de_red_se_traduce():
    session = _FakeSession(raise_error=requests.exceptions.Timeout("agotado"))
    with pytest.raises(ProviderTimeout):
        _provider(session).generate(_png_bytes(), "prompt")


def test_error_de_red_se_traduce():
    session = _FakeSession(raise_error=requests.exceptions.ConnectionError("sin ruta"))
    with pytest.raises(ProviderError):
        _provider(session).generate(_png_bytes(), "prompt")


def test_foto_ilegible_no_se_envia():
    session = _FakeSession(_FakeResponse(200, _b64_image_payload()))
    with pytest.raises(ProviderBadResponse):
        _provider(session).generate(b"no soy una imagen", "prompt")
    assert session.calls == []
