"""Comprobación previa de las credenciales de Gemini.

Responde a una sola pregunta: **¿funciona `GEMINI_API_KEY` con el modelo de
imágenes?** Hace una llamada real de generación con una imagen sintética no
personal, así que consume cuota mínima y es la única forma de confirmarlo.

Uso:

    python preflight_gemini.py           # comprobación completa (genera una imagen)
    python preflight_gemini.py --rapido  # solo valida la clave, sin generar

Nunca imprime la clave: solo su longitud y sus primeros caracteres.
"""

from __future__ import annotations

import io
import sys
import time

from PIL import Image, ImageDraw

import config

OK = "[OK]"
FALLO = "[FALLO]"
AVISO = "[AVISO]"


def _preparar_salida() -> None:
    """Evita UnicodeEncodeError en consolas de Windows con codificación heredada."""
    for flujo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(flujo, "reconfigure", None)
        if callable(reconfigurar):
            try:
                reconfigurar(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def _mask(valor: str | None) -> str:
    if not valor:
        return "(vacío)"
    return f"{valor[:6]}...{valor[-4:]} ({len(valor)} caracteres)"


def _imagen_sintetica() -> bytes:
    """Figura humana esquemática: no representa a ninguna persona real."""
    imagen = Image.new("RGB", (700, 700), (150, 190, 230))
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rectangle([0, 500, 700, 700], fill=(150, 180, 130))
    dibujo.ellipse([230, 130, 470, 370], fill=(236, 205, 175))
    dibujo.chord([220, 110, 480, 340], 180, 360, fill=(80, 55, 35))
    dibujo.ellipse([290, 230, 320, 260], fill="white")
    dibujo.ellipse([302, 238, 314, 252], fill=(50, 35, 25))
    dibujo.ellipse([380, 230, 410, 260], fill="white")
    dibujo.ellipse([392, 238, 404, 252], fill=(50, 35, 25))
    dibujo.arc([320, 280, 380, 330], 0, 180, fill=(160, 90, 90), width=6)
    dibujo.rounded_rectangle([200, 370, 500, 640], radius=40, fill=(90, 130, 210))
    buffer = io.BytesIO()
    imagen.save(buffer, format="JPEG", quality=92)
    return buffer.getvalue()


def comprobar(rapido: bool = False) -> int:
    settings = config.load_settings()
    clave = (settings.gemini_api_key or "").strip()
    modelo = (settings.gemini_model or "").strip() or "gemini-nano-banana-2.1"

    print("=" * 68)
    print("Comprobación de credenciales de Gemini")
    print("=" * 68)
    print(f"Proveedor configurado : {settings.provider}")
    print(f"GEMINI_API_KEY        : {_mask(clave)}")
    print(f"GEMINI_MODEL          : {modelo}")
    print()

    problemas = 0

    if not clave:
        print(f"{FALLO} No hay GEMINI_API_KEY en .env.")
        print("        Obtén una en https://aistudio.google.com/apikey")
        print("        y cambia IMAGE_PROVIDER=gemini cuando la tengas.")
        return 1

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print(f"{FALLO} Falta el SDK. Instálalo con:")
        print("        python -m pip install google-genai")
        return 1
    print(f"{OK} El SDK oficial google-genai está instalado.")

    try:
        cliente = genai.Client(
            api_key=clave,
            http_options=types.HttpOptions(timeout=int(settings.request_timeout_seconds * 1000)),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"{FALLO} No se pudo construir el cliente: {type(exc).__name__}")
        return 1

    if rapido:
        print(f"{AVISO} Modo rápido: no se genera ninguna imagen.")
        print("        No se puede confirmar el modelo de imágenes sin llamarlo.")
        print()
        print("=" * 68)
        print("RESULTADO: la clave está configurada. Ejecuta sin --rapido para")
        print("           verificar de verdad la generación de imágenes.")
        print("=" * 68)
        return 0

    # La prueba decisiva: generar una imagen editando la foto sintética.
    print()
    print("Prueba decisiva: generar una imagen a partir de la foto de prueba...")
    foto = _imagen_sintetica()
    prompt = (
        "Edit the attached photo following these instructions:\n"
        "Transform the person in this photo into a friendly astronaut child, "
        "colorful storybook illustration style, keep the face recognizable."
    )

    inicio = time.perf_counter()
    try:
        respuesta = cliente.models.generate_content(
            model=modelo,
            contents=[
                types.Part.from_text(text=prompt),
                types.Part.from_bytes(data=foto, mime_type="image/jpeg"),
            ],
        )
    except Exception as exc:  # noqa: BLE001
        texto = f"{type(exc).__name__}: {exc}"[:300]
        print(f"{FALLO} La llamada falló: {texto}")
        bajo = texto.lower()
        if any(m in bajo for m in ("429", "quota", "rate")):
            print("        Es un problema de cuota o de límite de uso.")
            print("        Nota: Google retiró la generación de imágenes del plan gratuito.")
        elif any(m in bajo for m in ("401", "403", "api key", "permission", "unauthenticated")):
            print("        Revisa que la clave sea válida y que la API de Gemini esté habilitada.")
        elif any(m in bajo for m in ("404", "not found", "not supported")):
            print(f"        Puede que el modelo '{modelo}' no exista para esta cuenta.")
            print("        Prueba GEMINI_MODEL=gemini-3.1-flash-image en .env")
        return 1

    transcurrido = time.perf_counter() - inicio

    imagen_bytes = None
    texto_devuelto = ""
    for parte in getattr(respuesta, "parts", None) or []:
        if getattr(parte, "text", None):
            texto_devuelto = str(parte.text)[:200]
        inline = getattr(parte, "inline_data", None)
        if inline is not None and getattr(inline, "data", None):
            datos = inline.data
            imagen_bytes = bytes(datos) if isinstance(datos, (bytes, bytearray)) else None
            break

    if not imagen_bytes:
        print(f"{FALLO} La respuesta no contenía imagen ({transcurrido:.1f} s).")
        if texto_devuelto:
            print(f"        Texto devuelto: {texto_devuelto}")
        return 1

    try:
        with Image.open(io.BytesIO(imagen_bytes)) as salida:
            tamano = salida.size
            formato = salida.format
            salida.convert("RGB").save("prueba_gemini.png")
    except Exception:  # noqa: BLE001
        print(f"{FALLO} Los datos devueltos no son una imagen válida.")
        return 1

    print(f"{OK} Imagen generada en {transcurrido:.1f} s.")
    print(f"     Formato: {formato} | tamaño: {tamano[0]}x{tamano[1]} | {len(imagen_bytes)//1024} KB")
    print("     Guardada como prueba_gemini.png (imagen sintética, sin personas reales).")
    print()
    print("=" * 68)
    print("RESULTADO: credenciales de Gemini correctas y modelo operativo.")
    print("Para usarlo, deja IMAGE_PROVIDER=gemini en .env y reinicia la aplicación.")
    print("=" * 68)
    return 0 if problemas == 0 else 1


if __name__ == "__main__":
    _preparar_salida()
    sys.exit(comprobar(rapido="--rapido" in sys.argv))
