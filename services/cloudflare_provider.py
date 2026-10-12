"""Proveedor Cloudflare Workers AI.

Modelo: **`@cf/black-forest-labs/flux-2-klein-9b`** (FLUX.2 [klein] 9B, Black Forest Labs).

Por qué este modelo y no otro (`docs/PROVIDER_VALIDATION.md`): el caso de uso
necesita **generación condicionada por imagen** (transformar la foto del
participante), no texto a imagen. FLUX.2 [klein] 9B es el modelo del catálogo de
Workers AI que cumple eso y **está operativo**:

- admite imágenes de referencia en los campos `input_image_0` … `input_image_3`;
- se le llama con `multipart/form-data`;
- en las pruebas aceptó entradas de hasta 1400 px y devuelve 1024×1024;
- latencia medida: **3–5 s** por generación.

Fuente: <https://developers.cloudflare.com/workers-ai/models/flux-2-klein-9b/>.

### Modelos descartados (medido, no supuesto)

| Modelo | Resultado |
|---|---|
| `@cf/black-forest-labs/flux-2-dev` | **HTTP 500** en todas las pruebas (3 intentos, con y sin imagen). El servicio está caído aunque figure en el catálogo. Además limita la imagen de entrada a <512×512, lo que degradaría el rostro. |
| `@cf/black-forest-labs/flux-2-klein-4b` | Funciona y conserva la cara, pero la escena es mucho más plana y pobre que la del 9B. |
| `bria/fibo-edit-1.5` | No existe en el catálogo de Workers AI. |
| `flux-1-schnell`, `stable-diffusion-xl-base-1.0`, `dreamshaper-8-lcm` | Funcionan, pero son **solo texto a imagen**: no aceptan la foto del participante. |

Autenticación: `Authorization: Bearer <CLOUDFLARE_API_TOKEN>`, con un token que
tenga los permisos `Workers AI - Read` y `Workers AI - Edit` de la cuenta
indicada en `CLOUDFLARE_ACCOUNT_ID`.
"""

from __future__ import annotations

import base64
import binascii
import io
import logging
import random

import requests
from PIL import Image

from services.image_generator import (
    ImageGenerator,
    ProviderBadResponse,
    ProviderError,
    ProviderNotConfigured,
    ProviderRateLimit,
    ProviderTimeout,
)

logger = logging.getLogger("feria_ia")

API_BASE = "https://api.cloudflare.com/client/v4/accounts"

#: Modelo validado y operativo. El nombre debe llevar el prefijo `@cf/` tal cual.
MODEL = "@cf/black-forest-labs/flux-2-klein-9b"

#: Lado mayor al que se reduce la foto antes de enviarla. Medido: el modelo acepta
#: entradas mayores, así que se conserva el detalle facial.
MAX_INPUT_SIDE_PX = 1024

#: Campos de imagen que admite el modelo, en orden.
INPUT_IMAGE_FIELDS = ("input_image_0", "input_image_1", "input_image_2", "input_image_3")

_STEPS = 25
_GUIDANCE = 3.5

#: Códigos HTTP del proveedor traducidos a los códigos de `docs/API.md` §5.
_STATUS_MAP = {
    400: ("PROVIDER_BAD_RESPONSE", ProviderBadResponse),
    401: ("PROVIDER_NOT_CONFIGURED", ProviderNotConfigured),
    403: ("PROVIDER_NOT_CONFIGURED", ProviderNotConfigured),
    404: ("PROVIDER_BAD_RESPONSE", ProviderBadResponse),
    408: ("PROVIDER_TIMEOUT", ProviderTimeout),
    429: ("PROVIDER_RATE_LIMIT", ProviderRateLimit),
}


#: Lado del lienzo que se pide al modelo. Medido: klein-9b devuelve 1024×1024
#: aunque se le pase una foto vertical u horizontal, así que se pide explícito.
OUTPUT_SIDE_PX = 1024


def _shrink_for_model(image_bytes: bytes, max_side: int = MAX_INPUT_SIDE_PX) -> bytes:
    """Reduce la foto si supera `max_side`, conservando la proporción.

    Se conserva el detalle facial: medido que el modelo acepta entradas grandes.
    """
    with Image.open(io.BytesIO(image_bytes)) as opened:
        opened.load()
        image = opened.convert("RGB")
        longest = max(image.size)
        if longest <= max_side:
            return image_bytes
        scale = max_side / longest
        resized = image.resize(
            (max(int(image.width * scale), 1), max(int(image.height * scale), 1)),
            Image.LANCZOS,
        )
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=92, optimize=True)
        return buffer.getvalue()


def _extract_image(result: object) -> bytes | None:
    """Saca los bytes de imagen de la respuesta, sin depender de un solo formato.

    La respuesta puede traer base64 (campo `image`) o llegar como bytes crudos.
    """
    if isinstance(result, (bytes, bytearray)):
        return bytes(result)
    if not isinstance(result, dict):
        return None

    for key in ("image", "images", "output"):
        value = result.get(key)
        candidate = value[0] if isinstance(value, list) and value else value
        if isinstance(candidate, (bytes, bytearray)):
            return bytes(candidate)
        if isinstance(candidate, str) and candidate.strip():
            payload = candidate.strip()
            # Formatos tipo data URL: "data:image/png;base64,AAAA…"
            if payload.startswith("data:") and "," in payload:
                payload = payload.split(",", 1)[1]
            try:
                return base64.b64decode(payload, validate=True)
            except (binascii.Error, ValueError):
                continue
    return None


class CloudflareProvider(ImageGenerator):
    name = "cloudflare"

    def __init__(
        self,
        account_id: str | None,
        api_token: str | None,
        model: str | None = None,
        timeout_seconds: float = 60.0,
        session: requests.Session | None = None,
    ) -> None:
        self._account_id = (account_id or "").strip()
        self._api_token = (api_token or "").strip()
        # Se admite cambiar de modelo, pero por defecto el validado.
        self._model = (model or "").strip() or MODEL
        self._timeout = timeout_seconds
        self._session = session or requests.Session()

    # ------------------------------------------------------------------ interno

    def _require_configuration(self) -> None:
        missing = [
            name
            for name, value in (
                ("CLOUDFLARE_ACCOUNT_ID", self._account_id),
                ("CLOUDFLARE_API_TOKEN", self._api_token),
            )
            if not value
        ]
        if missing:
            raise ProviderNotConfigured(
                "Falta configuración de Cloudflare: " + ", ".join(missing) + "."
            )

    @property
    def _url(self) -> str:
        return f"{API_BASE}/{self._account_id}/ai/run/{self._model}"

    def _translate_status(self, status: int, body: str) -> ProviderError:
        """Traduce el error del proveedor a un código de `docs/API.md`, sin filtraciones."""
        provider_code = ""
        try:
            payload = requests.models.complexjson.loads(body)
            errors = payload.get("errors") or []
            if errors and isinstance(errors[0], dict):
                provider_code = str(errors[0].get("message") or "")
        except (ValueError, AttributeError):
            provider_code = ""

        if status in _STATUS_MAP:
            code, exception = _STATUS_MAP[status]
            if status in (401, 403):
                return exception(
                    "Cloudflare rechazó las credenciales (HTTP "
                    f"{status}). Revisa que CLOUDFLARE_ACCOUNT_ID sea el de la cuenta "
                    "dueña del token y que el token tenga los permisos "
                    "«Workers AI - Read» y «Workers AI - Edit»."
                )
            if status == 429:
                return exception("Cloudflare indica límite de uso o cuota agotada.")
            if status == 400:
                return exception("Cloudflare rechazó la solicitud (HTTP 400).")
            if status == 404:
                return exception(
                    "Cloudflare no encontró el modelo o la cuenta indicados (HTTP 404)."
                )
            return exception(
                f"Cloudflare agotó el tiempo de espera (HTTP {status})."
            )

        if status >= 500:
            return ProviderBadResponse(
                f"Cloudflare devolvió un error de servidor (HTTP {status})."
            )
        suffix = f" Detalle del proveedor: {provider_code[:120]}" if provider_code else ""
        return ProviderError(f"Cloudflare devolvió HTTP {status}.{suffix}")

    # ------------------------------------------------------------------- público

    def generate(self, image_bytes: bytes, prompt: str) -> bytes:
        self._require_configuration()

        try:
            prepared = _shrink_for_model(image_bytes)
        except (OSError, ValueError) as exc:
            raise ProviderBadResponse("La fotografía no se pudo preparar para el modelo.") from exc

        form = {
            "prompt": prompt,
            INPUT_IMAGE_FIELDS[0]: ("foto.jpg", prepared, "image/jpeg"),
            # Medido: el modelo devuelve 1024×1024 aunque la foto sea vertical u
            # horizontal. Se pide explícito para no depender del valor por defecto
            # y que el compositor del título reciba siempre el mismo lienzo.
            "width": str(OUTPUT_SIDE_PX),
            "height": str(OUTPUT_SIDE_PX),
            "steps": str(_STEPS),
            "guidance": str(_GUIDANCE),
            "seed": str(random.randint(0, 2**31 - 1)),
        }
        headers = {"Authorization": f"Bearer {self._api_token}"}

        try:
            response = self._session.post(
                self._url,
                headers=headers,
                files=form,
                timeout=self._timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise ProviderTimeout("Cloudflare no respondió dentro del tiempo de espera.") from exc
        except requests.exceptions.RequestException as exc:
            raise ProviderError("No se pudo contactar con Cloudflare.") from exc

        if response.status_code != 200:
            raise self._translate_status(response.status_code, response.text)

        content_type = (response.headers.get("Content-Type") or "").lower()
        if content_type.startswith("image/"):
            return response.content

        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderBadResponse("Cloudflare no devolvió JSON ni una imagen.") from exc

        if payload.get("success") is False:
            errors = payload.get("errors") or []
            detail = str(errors[0].get("message")) if errors and isinstance(errors[0], dict) else ""
            raise ProviderBadResponse(
                "Cloudflare rechazó la generación." + (f" Detalle: {detail[:120]}" if detail else "")
            )

        extracted = _extract_image(payload.get("result"))
        if not extracted:
            raise ProviderBadResponse("La respuesta de Cloudflare no contiene una imagen.")

        # Comprobación explícita de que lo recibido es realmente una imagen.
        try:
            with Image.open(io.BytesIO(extracted)) as check:
                check.verify()
        except Exception as exc:  # noqa: BLE001 - cualquier fallo significa respuesta inservible
            raise ProviderBadResponse(
                "Los datos devueltos por Cloudflare no son una imagen válida."
            ) from exc

        return extracted
