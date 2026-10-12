# ENTREGA.md — Qué datos pasar y cómo ejecutar el sistema

Documento para **entregar** el proyecto a la persona que lo va a ejecutar en el
servidor de la feria. Contiene solo lo imprescindible para arrancarlo.

- La instalación detallada: [`DEPLOY.md`](DEPLOY.md)
- La operación durante el evento: [`RUNBOOK.md`](RUNBOOK.md)

> ⚠️ **Las credenciales no se envían por correo ni por chat.** Se pasan por un medio
> acordado (gestor de contraseñas, sobre cerrado, mensaje cifrado) y **nunca** se
> suben al repositorio. El archivo `.env` está en `.gitignore` precisamente para eso.

---

## 1. Lo mínimo para verlo funcionar (sin ninguna credencial)

```bash
git clone https://github.com/AndyNeva/Little-Scientists.git
cd Little-Scientists
cp .env.example .env     # dejar IMAGE_PROVIDER=mock
docker compose up -d --build
```

Abrir en el navegador **`http://localhost:5000`**.

Con `mock` funciona todo el flujo (cámara, personajes, título, descarga) salvo la
imagen real: muestra una ilustración sintética y avisa con «Modo demostración».
**No envía fotografías a internet y no gasta cuota.**

Esta es la forma recomendada de comprobar que el servidor está bien antes de
meter credenciales.

---

## 2. Variables de entorno

Todas van en el archivo `.env`. En Docker se pueden pasar también desde
`docker-compose.yml`, que ya lee estas mismas variables del entorno.

### 2.1 Obligatoria

| Variable | Valores | Qué hace |
|---|---|---|
| `IMAGE_PROVIDER` | `mock` · `cloudflare` · `gemini` | Elige quién genera la imagen. **Es el único cambio necesario para cambiar de proveedor**, y no se refleja en la interfaz. |

### 2.2 Si `IMAGE_PROVIDER=cloudflare` (3–5 s por imagen)

| Variable | Obligatoria | Ejemplo | Notas |
|---|---|---|---|
| `CLOUDFLARE_ACCOUNT_ID` | **Sí** | `4e97f1ac0c7978bdcced4ca249aa720e` | El de la cuenta dueña del token. **Sin espacios.** |
| `CLOUDFLARE_API_TOKEN` | **Sí** | `cfut_…` | Secreto. Necesita los permisos **`Workers AI - Read`** y **`Workers AI - Edit`**. |
| `CLOUDFLARE_MODEL` | No | `@cf/black-forest-labs/flux-2-klein-9b` | Si se deja vacío, usa este mismo. El prefijo `@cf/` forma parte del nombre. |

### 2.3 Si `IMAGE_PROVIDER=gemini` (15–18 s por imagen)

| Variable | Obligatoria | Ejemplo | Notas |
|---|---|---|---|
| `GEMINI_API_KEY` | **Sí** | `AQ.Ab8…` | Secreto. Se obtiene en <https://aistudio.google.com/apikey>. |
| `GEMINI_MODEL` | No | `gemini-nano-banana-2.1` | Si se deja vacío, usa este mismo. |
| `GEMINI_INPUT_MAX_SIDE_PX` | No | `1024` | Lado mayor de la foto que se envía. |

### 2.4 Ajustes generales (todas opcionales)

| Variable | Por defecto | Cuándo cambiarla |
|---|---|---|
| `PORT` | `5000` | Si el puerto 5000 está ocupado en el servidor. |
| `HOST` | `127.0.0.1` | **En Docker se pone `0.0.0.0`**; `docker-compose.yml` ya lo hace. |
| `REQUEST_TIMEOUT_SECONDS` | `60` | Si el proveedor tarda más de lo normal de forma habitual. |
| `MAX_UPLOAD_MB` | `8` | Tamaño máximo de la fotografía. |
| `MAX_NAME_LENGTH` | `20` | Longitud máxima del nombre del participante. |
| `INPUT_MAX_SIDE_PX` | `1024` | Resolución a la que se reduce la foto antes de enviarla. |
| `INPUT_JPEG_QUALITY` | `90` | Calidad del JPEG que se envía. |
| `FLASK_DEBUG` | `0` | Poner `1` **solo** en desarrollo: recarga al guardar. Nunca en la feria. |
| `LOG_LEVEL` | `INFO` | `DEBUG` para diagnosticar problemas. |
| `GEMINI_DEFAULT_MODEL` | `gemini-nano-banana-2.1` | Solo si el modelo por defecto de Gemini cambia. |

### 2.5 Plantilla lista para rellenar

```dotenv
# Quien genera las imágenes: mock | cloudflare | gemini
IMAGE_PROVIDER=mock

# --- Solo si IMAGE_PROVIDER=cloudflare ---
CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
CLOUDFLARE_MODEL=@cf/black-forest-labs/flux-2-klein-9b

# --- Solo si IMAGE_PROVIDER=gemini ---
GEMINI_API_KEY=
GEMINI_MODEL=gemini-nano-banana-2.1

# --- Ajustes generales (se pueden dejar así) ---
PORT=5000
HOST=0.0.0.0
REQUEST_TIMEOUT_SECONDS=60
MAX_UPLOAD_MB=8
MAX_NAME_LENGTH=20
LOG_LEVEL=INFO
```

---

## 3. Comprobar que las credenciales funcionan

Después de configurarlas y recrear el contenedor:

```bash
docker compose up -d --force-recreate

# Y la comprobación de verdad, con una llamada real:
docker compose exec aventura-ia python preflight_cloudflare.py
docker compose exec aventura-ia python preflight_gemini.py
```

Debe terminar en «credenciales correctas». **Estos scripts nunca muestran las
claves**, así que su salida se puede enviar por correo o chat sin riesgo.

También sirve el estado básico:

```bash
curl http://127.0.0.1:5000/api/health
# {"status":"ok","provider":"cloudflare","demo_mode":false}
```

---

## 4. ⚠️ Lo que hay que advertir a quien lo ejecute

1. **La cámara necesita `localhost` o HTTPS.** Si se accede por dirección IP
   (`http://192.168.1.50:5000`) o por un nombre de red sin certificado, **el
   navegador bloqueará la webcam**. Lo más simple es abrir la aplicación en el
   mismo computador que tiene la cámara, con `http://localhost:5000`. La
   alternativa con HTTPS está en [`DEPLOY.md`](DEPLOY.md) §4.

2. **La cuota se agota rápido.** El plan gratuito de Cloudflare da para unas **6
   imágenes al día**. Antes del evento hay que decidir el plan y cuántas imágenes
   reales se harán de verdad ([`RUNBOOK.md`](RUNBOOK.md) §5).

3. **Las fotografías se envían a un proveedor externo.** Con `mock` no salen del
   equipo; con `cloudflare` o `gemini`, sí. Son menores de edad: hacen falta la
   autorización de los representantes legales y la revisión de las condiciones de
   uso de datos del proveedor ([`RUNBOOK.md`](RUNBOOK.md) §7).

4. **Un solo servidor a la vez.** En Windows pueden quedar dos procesos escuchando
   el mismo puerto y las peticiones se reparten entre ellos. Comprobación y
   solución en [`RUNBOOK.md`](RUNBOOK.md) §2.

---

## 5. Resumen para enviar en un mensaje

> **Repositorio:** <https://github.com/AndyNeva/Little-Scientists>
>
> **Para verlo funcionar sin credenciales:**
> ```
> git clone https://github.com/AndyNeva/Little-Scientists.git
> cd Little-Scientists
> cp .env.example .env
> docker compose up -d --build
> ```
> Y abrir `http://localhost:5000` en el mismo computador donde está la webcam.
>
> **Para usar la IA real**, hay que rellenar en `.env`:
> - `IMAGE_PROVIDER` → `cloudflare` o `gemini`
> - Si es Cloudflare: `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_API_TOKEN`
> - Si es Gemini: `GEMINI_API_KEY`
>
> Después: `docker compose up -d --force-recreate` y comprobar que
> `/api/health` devuelve `"status": "ok"`.
>
> **Importante:** la cámara del navegador solo funciona en `localhost` o con
> HTTPS. Si se abre por IP sin certificado, la webcam queda bloqueada.
>
> Guía completa: `docs/DEPLOY.md`
