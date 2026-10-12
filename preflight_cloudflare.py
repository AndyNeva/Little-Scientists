"""Comprobación previa de las credenciales de Cloudflare.

Responde a una sola pregunta: **¿puede este token ejecutar Workers AI en esta
cuenta?** No genera ninguna imagen, así que no consume cuota de generación (solo
la llamada mínima de comprobación).

Uso:

    python preflight_cloudflare.py

Nunca imprime el token: solo su longitud y sus primeros caracteres. Se puede
compartir la salida sin riesgo.
"""

from __future__ import annotations

import sys

import requests

import config

OK = "[OK]"
FALLO = "[FALLO]"
AVISO = "[AVISO]"


def _preparar_salida() -> None:
    """Evita UnicodeEncodeError en consolas de Windows con codificación heredada.

    La consola puede estar en cp1252, que no sabe representar «≈». Sin esto, el
    script termina con una traza al imprimir el recordatorio de cuota.
    """
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
    return f"{valor[:6]}…{valor[-4:]} ({len(valor)} caracteres)"


def comprobar() -> int:
    settings = config.load_settings()
    cuenta = (settings.cloudflare_account_id or "").strip()
    token = (settings.cloudflare_api_token or "").strip()
    modelo = (settings.cloudflare_model or "").strip()

    print("=" * 68)
    print("Comprobación de credenciales de Cloudflare Workers AI")
    print("=" * 68)
    print(f"Proveedor configurado : {settings.provider}")
    print(f"CLOUDFLARE_ACCOUNT_ID : {_mask(cuenta)}")
    print(f"CLOUDFLARE_API_TOKEN  : {_mask(token)}")
    print(f"CLOUDFLARE_MODEL      : {modelo or '(sin valor)'}")
    print()

    problemas = 0
    cabeceras = {"Authorization": f"Bearer {token}"}

    # 1. ¿El token existe y está activo?
    try:
        respuesta = requests.get(
            "https://api.cloudflare.com/client/v4/user/tokens/verify",
            headers=cabeceras,
            timeout=30,
        )
        datos = respuesta.json()
        if respuesta.status_code == 200 and datos.get("success"):
            print(f"{OK} El token existe y está activo.")
        else:
            print(f"{FALLO} El token no es válido: HTTP {respuesta.status_code} {datos.get('errors')}")
            problemas += 1
    except requests.RequestException as exc:
        print(f"{FALLO} Sin conexión con api.cloudflare.com: {exc}")
        return 2

    # 2. ¿El token puede ver la cuenta configurada? Es solo informativo: este
    #    endpoint exige permiso de lectura de cuenta, que NO hace falta para
    #    ejecutar Workers AI. Por eso no cuenta como problema.
    try:
        respuesta = requests.get(
            f"https://api.cloudflare.com/client/v4/accounts/{cuenta}",
            headers=cabeceras,
            timeout=30,
        )
        if respuesta.status_code == 200 and respuesta.json().get("success"):
            nombre = respuesta.json().get("result", {}).get("name", "?")
            print(f"{OK} El token accede a la cuenta «{nombre}».")
        else:
            datos = respuesta.json()
            mensaje = (datos.get("errors") or [{}])[0].get("message", "")
            print(f"{AVISO} El token no puede leer los datos de la cuenta (HTTP {respuesta.status_code}): {mensaje}")
            print("        Es normal: requiere permiso de lectura de cuenta, que no hace")
            print("        falta para generar. Lo que decide es la prueba de abajo.")
    except requests.RequestException as exc:
        print(f"{AVISO} No se pudieron leer los datos de la cuenta: {exc}")

    # 3. ¿Qué cuentas ve el token? Ayuda a encontrar el ID correcto.
    try:
        respuesta = requests.get(
            "https://api.cloudflare.com/client/v4/accounts",
            headers=cabeceras,
            params={"per_page": 20},
            timeout=30,
        )
        if respuesta.status_code == 200:
            cuentas = respuesta.json().get("result") or []
            if cuentas:
                print(f"{OK} El token ve {len(cuentas)} cuenta(s):")
                for item in cuentas:
                    marca = "  <-- la configurada" if item.get("id") == cuenta else ""
                    print(f"       · {item.get('id')}  {item.get('name')}{marca}")
            else:
                print(f"{AVISO} El token no lista ninguna cuenta.")
                print("        Es normal si el token está limitado a un recurso concreto.")
                print("        El permiso de listar cuentas no hace falta para generar.")
    except requests.RequestException as exc:
        print(f"{AVISO} No se pudo listar cuentas: {exc}")

    # 4. La prueba decisiva: una llamada real y mínima a Workers AI.
    print()
    print("Prueba decisiva: ejecutar un modelo de Workers AI…")
    try:
        respuesta = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{cuenta}/ai/run/@cf/meta/llama-3.1-8b-instruct",
            headers={**cabeceras, "Content-Type": "application/json"},
            json={"prompt": "Responde solo: hola"},
            timeout=90,
        )
        if respuesta.status_code == 200 and respuesta.json().get("success"):
            print(f"{OK} Workers AI funciona con estas credenciales.")
            print("     Ya se puede probar el flujo completo: python app.py")
        else:
            datos = respuesta.json() if respuesta.headers.get("Content-Type", "").startswith("application/json") else {}
            mensaje = (datos.get("errors") or [{}])[0].get("message", respuesta.text[:120])
            print(f"{FALLO} Workers AI rechazó la llamada (HTTP {respuesta.status_code}): {mensaje}")
            if respuesta.status_code in (401, 403):
                print("       Revisa que el token tenga los permisos «Workers AI - Read»")
                print("       y «Workers AI - Edit», y que pertenezca a la cuenta indicada.")
            problemas += 1
    except requests.RequestException as exc:
        print(f"{FALLO} Error llamando a Workers AI: {exc}")
        problemas += 1

    print()
    print("=" * 68)
    if problemas == 0:
        print("RESULTADO: credenciales correctas. Se puede cerrar la Fase 0 (G0).")
        print()
        print("Recordatorio de cuota: con el plan gratuito (10.000 neuronas al dia) y")
        print("unas 1.545 neuronas por imagen, solo hay unas 6 generaciones al dia.")
        print("Para una feria hace falta el plan de pago: unos $0,017 por participante.")
    else:
        print(f"RESULTADO: {problemas} problema(s) por resolver antes de continuar.")
    print("=" * 68)
    return 1 if problemas else 0


if __name__ == "__main__":
    _preparar_salida()
    sys.exit(comprobar())
