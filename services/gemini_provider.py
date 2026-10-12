"""Proveedor Gemini (Google Gen AI SDK).

Modelo por defecto: **`gemini-nano-banana-2.1`** (familia «Nano Banana»), la
capacidad nativa de generación y **edición conversacional de imágenes** de Gemini.
Se eligió porque el caso de uso necesita transformar una foto que ya existe, no
generar una imagen desde cero.

- Entradas admitidas: texto, imagen, vídeo y PDF. Salida: imagen y texto.
- Se le pasa la fotografía como parte `inline_data` junto al prompt.
- Todos los proveedores comparten la interfaz `ImageGenerator` (`docs/API.md` §7),
  así que cambiar de Cloudflare a Gemini es solo cambiar `IMAGE_PROVIDER`.

Fuentes (consultadas el 11 de octubre de 2026):

- Generación de imágenes: <https://ai.google.dev/gemini-api/docs/image-generation>
- Ficha del modelo: <https://ai.google.dev/gemini-api/docs/models/gemini-nano-banana-2.1>
- SDK de Python: <https://googleapis.github.io/python-genai/>

**El SDK es una dependencia opcional:** solo se importa al construir este
proveedor, de modo que la aplicación funciona con Cloudflare o `mock` aunque
`google-genai` no esté instalado.
"""

from __future__ import annotations

import io
import logging

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

#: Modelo por defecto. Se puede cambiar con `GEMINI_MODEL`.
DEFAULT_MODEL = "gemini-nano-banana-2.1"

#: Lado mayor de la foto que se envía a Gemini.
DEFAULT_INPUT_MAX_SIDE_PX = 1024

#: Instrucción que acompaña a la fotografía. Gemini recibe la imagen y el prompt
#: juntos; el prompt del estilo lo construye el servidor desde el catálogo.
_INPUT_INSTRUCTION = "Edit the attached photo following these instructions:"

#: Fragmentos que delatan un problema de cuota o de límite de uso en el mensaje
#: del SDK, que no siempre usa códigos HTTP.
_RATE_LIMIT_MARKERS = (
    "429",
    "resource_exhausted",
    "quota",
    "rate limit",
    "rate_limit",
    "too many requests",
)
_TIMEOUT_MARKERS = ("timeout", "timed out", "deadline exceeded", "504")
_AUTH_MARKERS = (
    "401",
    "403",
    "api key not valid",
    "api_key_invalid",
    "permission_denied",
    "unauthenticated",
    "invalid api key",
)
_BAD_REQUEST_MARKERS = ("400", "invalid_argument", "failed_precondition")


def _shrink(image_bytes: bytes, max_side: int) -> bytes:
    """Reduce la foto si supera `max_side`, conservando la proporción."""
    with Image.open(io.BytesIO(image_bytes)) as opened:
        opened.load()
        image = opened.convert("RGB")
        longest = max(image.size)
        if longest <= max_side:
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=92, optimize=True)
            return buffer.getvalue()
        scale = max_side / longest
        resized = image.resize(
            (max(int(image.width * scale), 1), max(int(image.height * scale), 1)),
            Image.LANCZOS,
        )
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=92, optimize=True)
        return buffer.getvalue()


def _part_image_bytes(part: object) -> bytes | None:
    """Extrae los bytes de imagen de una parte de la respuesta, si los lleva."""
    inline = getattr(part, "inline_data", None)
    if inline is None:
        return None
    data = getattr(inline, "data", None)
    if data is None:
        return None
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, str):
        # Algunas versiones del SDK entregan el contenido ya en base64.
        import base64
        import binascii

        try:
            return base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError):
            return None
    return None


def _extract_image(response: object) -> bytes | None:
    """Primera imagen de la respuesta, recorriendo sus partes."""
    parts = getattr(response, "parts", None)
    if parts is None:
        candidates = getattr(response, "candidates", None) or []
        parts = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts.extend(getattr(content, "parts", None) or [])

    for part in parts or []:
        data = _part_image_bytes(part)
        if data:
            return data
    return None


def _response_text(response: object) -> str:
    """Texto que devolvió el modelo, útil para el log cuando no hay imagen."""
    fragments: list[str] = []
    for part in getattr(response, "parts", None) or []:
        text = getattr(part, "text", None)
        if text:
            fragments.append(str(text))
    return " ".join(fragments)[:200]


class GeminiProvider(ImageGenerator):
    name = "gemini"

    def __init__(
        self,
        api_key: str | None,
        model: str | None = None,
        timeout_seconds: float = 60.0,
        input_max_side_px: int = DEFAULT_INPUT_MAX_SIDE_PX,
        client: object | None = None,
    ) -> None:
        self._api_key = (api_key or "").strip()
        self._model = (model or "").strip() or DEFAULT_MODEL
        self._timeout = timeout_seconds
        self._input_max_side_px = input_max_side_px or DEFAULT_INPUT_MAX_SIDE_PX
        #: Se puede inyectar un cliente ya construido (pruebas).
        self._client = client

    # ------------------------------------------------------------------ interno

    def _require_configuration(self) -> None:
        if not self._api_key:
            raise ProviderNotConfigured(
                "Falta configuración de Gemini: GEMINI_API_KEY."
            )

    def _build_client(self) -> object:
        """Construye el cliente del SDK oficial, con el tiempo de espera configurado."""
        if self._client is not None:
            return self._client

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise ProviderNotConfigured(
                "Falta el SDK de Gemini. Instálalo con: python -m pip install google-genai"
            ) from exc

        # El SDK mide el tiempo de espera en milisegundos.
        http_options = types.HttpOptions(timeout=int(self._timeout * 1000))
        self._client = genai.Client(api_key=self._api_key, http_options=http_options)
        return self._client

    def _translate_exception(self, exc: BaseException) -> ProviderError:
        """Traduce el error del SDK a los códigos de `docs/API.md` §5."""
        text = f"{type(exc).__name__}: {exc}".lower()

        if any(marker in text for marker in _RATE_LIMIT_MARKERS):
            return ProviderRateLimit("Gemini indica límite de uso o cuota agotada.")
        if any(marker in text for marker in _TIMEOUT_MARKERS):
            return ProviderTimeout("Gemini no respondió dentro del tiempo de espera.")
        if any(marker in text for marker in _AUTH_MARKERS):
            return ProviderNotConfigured(
                "Gemini rechazó las credenciales. Revisa que GEMINI_API_KEY sea una "
                "clave válida de Google AI Studio y que la API de Gemini esté habilitada."
            )
        if any(marker in text for marker in _BAD_REQUEST_MARKERS):
            return ProviderBadResponse("Gemini rechazó la solicitud.")
        return ProviderError("Error de comunicación con Gemini.")

    # ------------------------------------------------------------------- público

    def generate(self, image_bytes: bytes, prompt: str) -> bytes:
        self._require_configuration()

        try:
            prepared = _shrink(image_bytes, self._input_max_side_px)
        except (OSError, ValueError) as exc:
            raise ProviderBadResponse("La fotografía no se pudo preparar para el modelo.") from exc

        client = self._build_client()

        try:
            from google.genai import types
        except ImportError:  # pragma: no cover - ya se comprobó al construir el cliente
            types = None  # type: ignore[assignment]

        contents = self._build_contents(prepared, prompt, types)

        try:
            response = client.models.generate_content(model=self._model, contents=contents)
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - se traduce a un código conocido
            raise self._translate_exception(exc) from exc

        extracted = _extract_image(response)
        if not extracted:
            detalle = _response_text(response)
            raise ProviderBadResponse(
                "La respuesta de Gemini no contiene una imagen."
                + (f" Texto devuelto: {detalle}" if detalle else "")
            )

        try:
            with Image.open(io.BytesIO(extracted)) as check:
                check.verify()
        except Exception as exc:  # noqa: BLE001 - cualquier fallo deja la respuesta inservible
            raise ProviderBadResponse(
                "Los datos devueltos por Gemini no son una imagen válida."
            ) from exc

        return extracted

    def _build_contents(self, prepared: bytes, prompt: str, types: object) -> object:
        """Contenido multimodal: instrucción + prompt del estilo + la fotografía.

        Con el SDK disponible se envían objetos `types.Part`; sin él (pruebas con
        un cliente simulado) se envía una lista equivalente y legible.
        """
        texto = f"{_INPUT_INSTRUCTION}\n{prompt}"

        if types is None:
            return [texto, {"mime_type": "image/jpeg", "data": prepared}]

        return [
            types.Part.from_text(text=texto),
            types.Part.from_bytes(data=prepared, mime_type="image/jpeg"),
        ]
