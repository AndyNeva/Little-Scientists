"""Interfaz común de los proveedores de generación de imágenes.

Contrato de `API.md` §7 y `SPEC.md` §6.1. Los adaptadores traducen sus errores a
las excepciones de este módulo; el resto de la aplicación nunca ve la estructura
interna de un proveedor concreto.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ProviderError(Exception):
    """Error de proveedor traducible a un código `PROVIDER_*` de API.md §5.

    `code` debe ser uno de los códigos de `API.md` §5. `message` es informativo
    para depurar y nunca contiene credenciales ni datos de la solicitud.
    """

    code = "PROVIDER_ERROR"
    http_status = 502

    def __init__(self, message: str = "Error del proveedor de imágenes.") -> None:
        super().__init__(message)
        self.message = message


class ProviderNotConfigured(ProviderError):
    code = "PROVIDER_NOT_CONFIGURED"
    http_status = 500


class ProviderRateLimit(ProviderError):
    code = "PROVIDER_RATE_LIMIT"
    http_status = 429


class ProviderTimeout(ProviderError):
    code = "PROVIDER_TIMEOUT"
    http_status = 504


class ProviderBadResponse(ProviderError):
    code = "PROVIDER_BAD_RESPONSE"
    http_status = 502


class ImageGenerator(ABC):
    """Interfaz que deben cumplir todos los proveedores."""

    #: Nombre del proveedor tal como lo informa `GET /api/health`.
    name: str = "desconocido"

    @abstractmethod
    def generate(self, image_bytes: bytes, prompt: str) -> bytes:
        """Devuelve los bytes de una imagen generada.

        Debe lanzar excepciones derivadas de `ProviderError`.
        """
        raise NotImplementedError
