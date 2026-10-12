"""Pruebas de privacidad (TEST_PLAN.md §2).

Comprueban que el servidor no conserva fotografías, no registra datos del
participante y no expone claves al navegador.
"""

from __future__ import annotations

import io
import logging
import os
import time
from pathlib import Path

import pytest

import api.routes as routes
from services.image_generator import ProviderError
from services.mock_provider import MockProvider
from tests.conftest import make_test_image_bytes

BASE_DIR = Path(__file__).resolve().parent.parent

#: Clave ficticia y reconocible: si aparece en una respuesta, la prueba falla.
FAKE_SECRET = "clave-ficticia-para-pruebas-9f3a1c"


class _RecordingHandler(logging.Handler):
    """Captura lo que el logger de la aplicación registra de verdad.

    El logger `feria_ia` no propaga (así las trazas de Werkzeug no arrastran
    datos), así que se engancha aquí un manejador propio.
    """

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())

    @property
    def text(self) -> str:
        return "\n".join(self.messages)


@pytest.fixture
def app_logs():
    """Engancha un manejador al logger de la aplicación y lo retira al terminar."""
    logger = logging.getLogger("feria_ia")
    handler = _RecordingHandler()
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


#: Archivos y carpetas que Python y pytest escriben solos, sin relación con la
#: aplicación. Se ignoran para que la prueba no dependa de cuándo se importó un
#: módulo: contar un `.pyc` recién creado hacía la comprobación inestable.
_IGNORAR = ("__pycache__", ".pytest_cache", ".pyc", ".pyo")


def _snapshot(paths) -> dict[str, float]:
    """Catálogo de los archivos relevantes bajo `paths`, con su fecha."""
    snapshot: dict[str, float] = {}
    for root in paths:
        for base, _dirs, files in os.walk(root):
            if any(ignorado in base for ignorado in _IGNORAR):
                continue
            for name in files:
                if any(name.endswith(ignorado) for ignorado in _IGNORAR):
                    continue
                full = Path(base) / name
                try:
                    snapshot[str(full)] = full.stat().st_mtime
                except OSError:
                    continue
    return snapshot


def _post_generate(client, photo: bytes, style_id: str = "astronaut", name: str | None = None):
    data = {"photo": (io.BytesIO(photo), "foto.jpg"), "style_id": style_id}
    if name is not None:
        data["name"] = name
    return client.post("/api/generate", data=data, content_type="multipart/form-data")


def test_tras_generar_no_hay_archivos_nuevos(app, sample_photo):
    """El servidor no escribe fotografías ni resultados en disco."""
    watched = [BASE_DIR, Path(app.instance_path) if app.instance_path else BASE_DIR]
    before = _snapshot(watched)

    response = _post_generate(app.test_client(), sample_photo, name="Ana")

    assert response.status_code == 200
    after = _snapshot(watched)

    nuevos = set(after) - set(before)
    modificados = {ruta for ruta in set(after) & set(before) if after[ruta] != before[ruta]}
    assert after == before, f"La generación tocó el disco. Nuevos: {nuevos} | Modificados: {modificados}"


def test_los_logs_no_contienen_el_nombre_ni_bytes_de_la_imagen(app, sample_photo, app_logs):
    """Los logs registran solo ruta, estilo, código y duración."""
    name = "Valentina"

    response = _post_generate(app.test_client(), sample_photo, style_id="ocean", name=name)

    assert response.status_code == 200
    messages = app_logs.text

    assert name not in messages
    assert "style=ocean" in messages
    assert "code=OK" in messages
    assert "duration_ms=" in messages
    for forbidden in ("photo", "foto.jpg", "bytes", "base64"):
        assert forbidden not in messages.lower()


def test_los_logs_de_error_no_incluyen_la_clave(app, sample_photo, app_logs, monkeypatch):
    """El registro de un fallo de proveedor nunca escribe la credencial."""
    settings = app.config["SETTINGS"]
    app.config["SETTINGS"] = settings.__class__(
        **{**settings.__dict__, "cloudflare_api_token": FAKE_SECRET}
    )

    class _Failing(MockProvider):
        def generate(self, image_bytes: bytes, prompt: str) -> bytes:
            raise ProviderError("fallo de red con " + FAKE_SECRET)

    monkeypatch.setattr(routes, "build_provider", lambda _settings: _Failing())

    response = _post_generate(app.test_client(), sample_photo)
    assert response.status_code == 502

    assert FAKE_SECRET not in app_logs.text
    assert "«oculto»" in app_logs.text or "fallo de red con" in app_logs.text


def test_el_codigo_del_navegador_no_contiene_la_clave_configurada(app, sample_photo):
    """E-13: ninguna clave aparece en las fuentes del cliente ni en la red."""
    settings = app.config["SETTINGS"]
    app.config["SETTINGS"] = settings.__class__(
        **{**settings.__dict__, "cloudflare_api_token": FAKE_SECRET}
    )

    response = app.test_client().get("/")
    assert response.status_code == 200
    assert FAKE_SECRET not in response.get_data(as_text=True)

    for folder in ("static", "templates"):
        for path in (BASE_DIR / folder).rglob("*"):
            if path.is_file() and path.suffix in {".js", ".css", ".html"}:
                assert FAKE_SECRET not in path.read_text(encoding="utf-8"), path


def test_las_respuestas_de_imagen_no_se_cachean(client, sample_photo):
    response = _post_generate(client, sample_photo)
    assert response.headers["Cache-Control"] == "no-store"


def test_los_errores_no_incluyen_datos_de_la_solicitud(client):
    response = client.post(
        "/api/generate",
        data={"style_id": "astronaut", "name": "Ana"},
        content_type="multipart/form-data",
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "Ana" not in body
    assert "multipart" not in body.lower()


def test_gitignore_excluye_el_env():
    content = (BASE_DIR / ".gitignore").read_text(encoding="utf-8")
    lines = {line.strip() for line in content.splitlines()}
    assert ".env" in lines
    assert ".venv/" in lines


def test_env_example_solo_tiene_valores_ficticios():
    content = (BASE_DIR / ".env.example").read_text(encoding="utf-8")
    assert "pon_aqui_tu_token" in content
    assert "pon_aqui_tu_clave" in content
    # Sin credenciales con pinta real.
    assert "sk-" not in content
    assert "Bearer " not in content


def test_el_env_real_no_esta_en_el_repositorio():
    """Si existe `.env`, debe estar ignorado; el repositorio no lo incluye."""
    assert ".env" in (BASE_DIR / ".gitignore").read_text(encoding="utf-8")
    if (BASE_DIR / ".env").exists():
        # Solo se comprueba que no se trackea, sin leer su contenido.
        import subprocess

        result = subprocess.run(  # noqa: S603
            ["git", "check-ignore", ".env"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            assert ".env" in result.stdout


def test_no_hay_rutas_que_devuelvan_fotografias(client):
    """API.md §6: ninguna ruta lista, guarda o recupera fotografías."""
    for path in ("/api/photos", "/api/gallery", "/api/history", "/api/images"):
        assert client.get(path).status_code == 404


def test_el_prompt_del_catalogo_solo_se_construye_en_el_servidor(client, sample_photo, monkeypatch):
    """El navegador solo envía style_id: nada de prompts desde el cliente."""
    captured: dict = {}

    class _Capture(MockProvider):
        def generate(self, image_bytes: bytes, prompt: str) -> bytes:
            captured["prompt"] = prompt
            return make_test_image_bytes(size=(48, 48), image_format="PNG")

    monkeypatch.setattr(routes, "build_provider", lambda settings: _Capture())

    response = _post_generate(client, sample_photo, style_id="royalty")
    assert response.status_code == 200
    assert "fantasy royalty" in captured["prompt"]


@pytest.mark.parametrize("method", ["get", "post"])
def test_no_existe_reset_en_el_servidor(client, method):
    assert getattr(client, method)("/api/reset").status_code == 404
