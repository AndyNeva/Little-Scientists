# Aventura IA — Transformación de fotos con IA para feria universitaria

Aplicación web que toma una fotografía con la webcam, la transforma en un personaje
fantástico con un proveedor de IA y permite descargar el resultado en PNG con el
nombre del participante.

- **Público:** niños y niñas de escuela, con un operador adulto.
- **Privacidad:** el servidor no guarda fotografías, imágenes ni nombres. La foto
  vive solo en la memoria del navegador (`docs/SPEC.md` §10).
- **Estado:** funcional y probado de extremo a extremo con los dos proveedores de IA
  y con el modo demostración. Falta el ensayo general en el equipo de la feria
  (`docs/TASKS.md` §13).

---

## 1. Requisitos

- Windows, macOS o Linux con Python 3.10 o superior.
- Un navegador actualizado (Chrome, Edge o Firefox) y una webcam.
- Conexión a internet **solo** si se usa un proveedor real de IA.
- Para desplegarlo: Docker con el plugin `docker compose` (ver §4).

## 2. Instalación en tu computadora

```powershell
# 1. Entrar en la carpeta del proyecto
cd "ruta\a\Little-Scientists"

# 2. Crear y activar un entorno virtual (recomendado)
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate        # macOS / Linux

# 3. Instalar dependencias
python -m pip install -r requirements.txt

# 4. Crear la configuración local a partir de la plantilla
Copy-Item .env.example .env        # Windows
# cp .env.example .env             # macOS / Linux
```

## 3. Arrancar

### En tu computadora (para desarrollar o probar)

```powershell
python app.py
```

Después, abrir en el navegador:

```
http://localhost:5000
```

Comprobar que todo está listo en `http://localhost:5000/api/health`. Debe responder:

```json
{"status": "ok", "provider": "mock", "demo_mode": true}
```

Si el puerto 5000 está ocupado, cambiar `PORT` en `.env` y volver a arrancar.

> ⚠️ **Un solo servidor a la vez.** En Windows, Werkzeug enlaza el puerto con
> `SO_REUSEADDR`, así que **dos servidores pueden escuchar en el mismo puerto** y las
> peticiones se reparten entre ellos: verás el diseño viejo o un proveedor distinto
> del que dice `.env`. Comprueba con
> `netstat -ano | Select-String ':5000.*LISTENING'` (debe salir **una sola línea**) y
> cierra los sobrantes. Otra señal: si al recargar la página no aparece ninguna línea
> `GET /` en la terminal del servidor, estás hablando con otro proceso.

> 💡 **Mientras iteras el diseño:** los cambios en `templates/` y en los archivos CSS
> **no se recargan solos**. Reinicia el servidor, o pon `FLASK_DEBUG=1` en `.env`
> (solo en desarrollo, nunca en la feria).

## 4. Desplegar en un servidor, con Docker

```bash
cp .env.example .env     # y editar las credenciales
docker compose up -d --build
curl http://127.0.0.1:5000/api/health
```

**Guía completa para quien administra el servidor: [docs/DEPLOY.md](docs/DEPLOY.md)**
(incluye la configuración, la comprobación de credenciales, la operación diaria y
los problemas frecuentes).

> ⚠️ **La cámara necesita `localhost` o HTTPS.** El navegador solo permite usar la
> webcam en un contexto seguro. Si la aplicación se sirve desde **otro** equipo y se
> entra por dirección IP (`http://192.168.1.50:5000`) o por un nombre de red sin
> certificado, **la cámara queda bloqueada** y no se pueden tomar fotos. Lo más
> simple es abrirla en el mismo computador que tiene la webcam; la alternativa con
> HTTPS está explicada en [docs/DEPLOY.md](docs/DEPLOY.md) §4.

## 5. Proveedores de IA

**Para cambiar de proveedor se toca una sola línea de `.env` y se reinicia:**

```dotenv
IMAGE_PROVIDER=cloudflare    # o gemini, o mock
```

| `IMAGE_PROVIDER` | Qué hace |
|---|---|
| `mock` | **Modo demostración.** Genera una imagen sintética, ignora la foto y no envía nada a internet. Sirve para probar y como contingencia. |
| `cloudflare` | Cloudflare Workers AI con `@cf/black-forest-labs/flux-2-klein-9b`. **Verificado de extremo a extremo** (3–5 s por imagen). |
| `gemini` | Gemini con `gemini-nano-banana-2.1`. **Verificado de extremo a extremo** (15–18 s). Respeta la proporción de la foto en lugar de devolver un cuadrado. |

**El cambio no se ve en la pantalla.** El participante ve lo mismo con cualquiera de
los tres; el proveedor activo solo aparece en la terminal y en el campo `provider` de
`GET /api/health`, que es para el operador. La única excepción es «Modo
demostración», que la especificación obliga a avisar.

> ⚠️ **Cuota.** Los proveedores reales se pagan por uso. Cloudflare en plan gratuito
> da para unas **6 imágenes al día** (10.000 neuronas, se reinician a las 00:00 UTC);
> con Gemini funciona sin plan de pago, pero su límite está por confirmar. Antes de
> la feria hay que decidir el plan y cuántas imágenes reales se harán. La aplicación
> avisa en la terminal cuando se agota la cuota y dice qué alternativas hay
> configuradas.

### Comprobar las credenciales

```powershell
python preflight_cloudflare.py   # mide una generación real con Cloudflare
python preflight_gemini.py       # mide una generación real con Gemini
```

Ninguno imprime las claves: solo su longitud y sus primeros caracteres, así que su
salida se puede compartir sin riesgo.

**Nunca** se deben poner claves en el código, en JavaScript ni en el repositorio:
viven solo en `.env`, que está en `.gitignore`.

## 6. Pruebas

```powershell
python -m pytest
```

Las pruebas cubren catálogo, validación, composición del título, rutas, privacidad,
los dos proveedores y la interfaz. **No consumen cuota ni usan fotografías reales**:
los proveedores se simulan. El detalle está en
[`docs/TEST_PLAN.md`](docs/TEST_PLAN.md) §2.

## 7. Estructura del proyecto

```text
├── app.py                      # fábrica de la aplicación Flask
├── config.py                   # variables de entorno y el interruptor de proveedor
├── preflight_cloudflare.py     # comprueba las credenciales de Cloudflare
├── preflight_gemini.py         # comprueba las credenciales de Gemini
├── requirements.txt
├── pytest.ini
├── .env.example                # plantilla sin secretos
├── Dockerfile                  # imagen de la aplicación
├── docker-compose.yml          # ejecución con Docker
├── .dockerignore               # las credenciales nunca entran en la imagen
│
├── docs/                       # documentación completa
│   ├── SPEC.md                 # qué y por qué: alcance, requisitos, privacidad
│   ├── TASKS.md                # plan de ejecución por fases y estado real
│   ├── API.md                  # contrato de rutas y códigos de error
│   ├── PROMPTS.md              # prompts de los ocho estilos y rúbrica
│   ├── UI_COPY.md              # textos de la interfaz y mensajes de error
│   ├── TEST_PLAN.md            # pruebas automáticas y ensayo general
│   ├── DEPLOY.md               # cómo poner la aplicación en un servidor
│   └── design/
│       └── DESIGN.md           # sistema de diseño «Aventura IA Playful Clean»
│
├── api/routes.py               # rutas HTTP (contrato en docs/API.md)
├── data/transformations.py     # catálogo de los ocho estilos y prompts
├── services/
│   ├── image_generator.py      # interfaz común y errores de proveedor
│   ├── provider_factory.py     # selección del proveedor (el interruptor)
│   ├── mock_provider.py        # modo demostración
│   ├── cloudflare_provider.py  # Cloudflare Workers AI
│   ├── gemini_provider.py      # Gemini
│   ├── image_preparation.py    # validación y reducción de la foto
│   ├── name_validation.py      # reglas del nombre opcional
│   └── image_composer.py       # franja de título con Pillow
│
├── templates/index.html        # las cinco pantallas
├── static/css/styles.css       # sistema de diseño «Aventura IA Playful Clean»
├── static/js/camera.js         # stream, captura, detener pistas
├── static/js/app.js            # pantallas, estado, peticiones, limpieza
├── static/assets/fonts/        # Fredoka, Rubik y Nunito Sans (OFL) + licencias
└── tests/                      # pruebas automáticas
```

### Interfaz

El diseño sigue el sistema **«Aventura IA Playful Clean»** definido en
[`docs/design/DESIGN.md`](docs/design/DESIGN.md): morados luminosos, superficies
lavanda, formas de píldora y botones con borde inferior extruido. Las tipografías
(Rubik para títulos, Nunito Sans para el texto) van incluidas en el proyecto con
licencia OFL, así que no hace falta internet para verlo bien.

Se mantienen los requisitos de accesibilidad de
[`docs/UI_COPY.md`](docs/UI_COPY.md) §5: botones de 56 px como mínimo, alto
contraste, foco visible, texto alternativo y respeto por la preferencia de reducir
movimiento.

## 8. Documentación

Toda la documentación está en **`docs/`**:

| Documento | Contenido |
|---|---|
| [`docs/SPEC.md`](docs/SPEC.md) | Qué y por qué: alcance, requisitos, privacidad, riesgos. |
| [`docs/TASKS.md`](docs/TASKS.md) | Plan de ejecución por fases y estado real de cada una. |
| [`docs/API.md`](docs/API.md) | Contrato de rutas, validaciones y códigos de error. |
| [`docs/PROMPTS.md`](docs/PROMPTS.md) | Prompts de los ocho estilos y rúbrica de evaluación. |
| [`docs/UI_COPY.md`](docs/UI_COPY.md) | Textos de la interfaz y mensajes de error. |
| [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md) | Pruebas automáticas, escenarios y ensayo general. |
| [`docs/DEPLOY.md`](docs/DEPLOY.md) | Cómo poner la aplicación en un servidor: instalación, variables, operación y problemas frecuentes. |
| [`docs/design/DESIGN.md`](docs/design/DESIGN.md) | Sistema de diseño de la interfaz. |

## 9. Si algo falla

Los problemas más comunes:

| Síntoma | Causa probable |
|---|---|
| «Abre la aplicación desde localhost» | Se entró por una IP o un nombre de red, no por `localhost`. La cámara exige contexto seguro (§4). |
| La cámara no aparece | Falta permiso del navegador o la webcam está en uso por otra aplicación. |
| «Algo no está listo todavía» | `IMAGE_PROVIDER` o sus credenciales están mal en `.env`. |
| «Hay muchas aventuras en preparación» | Cuota del proveedor agotada. La terminal dice qué alternativas hay configuradas. |
| «No hay conexión» | El servidor no está corriendo en la terminal. |
| Veo el diseño viejo o el proveedor equivocado | Hay más de un servidor escuchando en el puerto (§3). |
