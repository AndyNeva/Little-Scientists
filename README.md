# Transformación de fotos con IA — prototipo para feria universitaria

Aplicación web local que toma una fotografía con la webcam, la transforma en un
personaje fantástico con un proveedor de IA y permite descargar el resultado en
PNG con el nombre del participante.

- **Público:** niños y niñas de escuela, con un operador adulto.
- **Privacidad:** el servidor no guarda fotografías ni nombres. La foto vive solo
  en la memoria del navegador. Ver `SPEC.md` §10.
- **Estado:** MVP en construcción. La integración con el proveedor real está
  pendiente de la puerta **G0** (`PROVIDER_VALIDATION.md`); funciona en **modo
  demostración** (`IMAGE_PROVIDER=mock`).

---

## 1. Requisitos

- Windows, macOS o Linux con Python 3.10 o superior.
- Un navegador actualizado (Chrome, Edge o Firefox) y una webcam.
- Conexión a internet **solo** si se usa un proveedor real de IA.

## 2. Instalación

```powershell
# 1. Entrar en la carpeta del proyecto
cd "ruta\a\Transformacion_Little_Scientist"

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

### En un servidor, con Docker (recomendado para la feria)

```bash
cp .env.example .env     # y editar las credenciales
docker compose up -d --build
curl http://127.0.0.1:5000/api/health
```

**Guía completa para quien administra el servidor: [docs/DEPLOY.md](docs/DEPLOY.md).**

Comprobar que todo está listo:

```
http://localhost:5000/api/health
```

Debe responder `{"status": "ok", "provider": "mock", "demo_mode": true}`.

> **Importante:** usar `http://localhost:5000` y no la IP de la máquina. El acceso
> a la cámara (`getUserMedia`) exige un contexto seguro, y `localhost` lo es. Si la
> aplicación se sirve desde **otro** equipo, **hace falta HTTPS** o el navegador
> bloqueará la webcam. Las dos alternativas están explicadas en
> [docs/DEPLOY.md](docs/DEPLOY.md) §4.

Si el puerto 5000 está ocupado, cambiar `PORT` en `.env` y volver a arrancar.

> ⚠️ **Un solo servidor a la vez.** En Windows, Werkzeug enlaza el puerto con
> `SO_REUSEADDR`, así que **dos servidores pueden escuchar en el mismo puerto** y las
> peticiones se reparten entre ellos: verás el diseño viejo o un proveedor distinto.
> Comprueba con `netstat -ano | Select-String ':5000.*LISTENING'` (debe salir una
> sola línea) y cierra los sobrantes. Además, los cambios en `templates/` y en los
> archivos CSS **no se recargan solos**: hay que reiniciar, o poner `FLASK_DEBUG=1`
> en `.env` mientras se itera. Detalle en `docs/RUNBOOK.md` §2.

## 4. Modo demostración y proveedores

**Para cambiar de proveedor se toca una sola línea de `.env` y se reinicia:**

```dotenv
IMAGE_PROVIDER=cloudflare    # o gemini, o mock
```

| `IMAGE_PROVIDER` | Qué hace |
|---|---|
| `mock` | **Modo demostración.** Genera una imagen sintética, ignora la foto y no envía nada a internet. Sirve para probar y como contingencia. |
| `cloudflare` | Cloudflare Workers AI, con el modelo `@cf/black-forest-labs/flux-2-klein-9b`. **Verificado de extremo a extremo** (3–5 s por imagen). |
| `gemini` | Gemini, con `gemini-nano-banana-2.1`. **Verificado de extremo a extremo** (15–18 s). Respeta la proporción de la foto en lugar de devolver un cuadrado. |

**El cambio no se ve en la pantalla.** El participante ve lo mismo con cualquiera de
los tres; el proveedor activo solo aparece en la terminal y en `GET /api/health`,
que es para el operador. La única excepción es «Modo demostración», que la
especificación obliga a avisar.

> ⚠️ **Cuota.** Los proveedores reales se pagan por uso. Cloudflare en plan gratuito
> da para unas **6 imágenes al día**; Gemini genera sin plan de pago, pero su límite
> está por confirmar. Antes de la feria hay que decidir el plan y cuántas imágenes
> reales se harán. Ver `docs/RUNBOOK.md` §5.

### Comprobar las credenciales

```powershell
python preflight_cloudflare.py   # mide una generación real con Cloudflare
python preflight_gemini.py       # mide una generación real con Gemini
```

Ninguno imprime las claves, así que puedes compartir su salida sin riesgo.

**Nunca** se deben poner claves en el código, en JavaScript ni en el repositorio:
viven solo en `.env`, que está en `.gitignore`.

## 5. Pruebas

```powershell
python -m pytest
```

Las pruebas cubren catálogo, validación, composición del título, rutas, privacidad,
el proveedor de Cloudflare, el de Gemini y la interfaz. **No consumen cuota ni usan
fotografías reales**: los proveedores se simulan. El detalle está en
`docs/TEST_PLAN.md` §2.

## 6. Estructura del proyecto

```text
├── app.py                     # fábrica de la aplicación Flask
├── config.py                  # variables de entorno y el interruptor de proveedor
├── preflight_cloudflare.py    # comprueba las credenciales de Cloudflare
├── preflight_gemini.py        # comprueba las credenciales de Gemini
├── requirements.txt
├── pytest.ini
├── .env.example               # plantilla sin secretos
├── docs/                      # decisiones, contratos y guía del operador
│   ├── PLAN.md
│   ├── API.md
│   ├── PROMPTS.md
│   ├── UI_COPY.md
│   ├── PROVIDER_VALIDATION.md
│   ├── TEST_PLAN.md
│   └── RUNBOOK.md
├── api/routes.py              # rutas HTTP (contrato en docs/API.md)
├── data/transformations.py    # catálogo de los ocho estilos y prompts
├── services/
│   ├── image_generator.py     # interfaz común y errores de proveedor
│   ├── provider_factory.py    # selección del proveedor (el interruptor)
│   ├── mock_provider.py       # modo demostración
│   ├── cloudflare_provider.py # Cloudflare Workers AI
│   ├── gemini_provider.py     # Gemini
│   ├── image_preparation.py   # validación y reducción de la foto
│   ├── name_validation.py     # reglas del nombre opcional
│   └── image_composer.py      # franja de título con Pillow
├── templates/index.html       # las cinco pantallas
├── static/css/styles.css      # sistema de diseño «Aventura IA Playful Clean»
├── static/js/camera.js        # stream, captura, detener pistas
├── static/js/app.js           # pantallas, estado, peticiones, limpieza
├── static/assets/fonts/       # Fredoka, Rubik y Nunito Sans (OFL) + licencias
└── tests/                     # pruebas automáticas
```

### Interfaz

El diseño sigue el sistema **«Aventura IA Playful Clean»** definido en
`stitch_extract/.../aventura_ia_playful_clean/DESIGN.md`: morados luminosos,
superficies lavanda, formas de píldora y botones con borde inferior extruido. Las
tipografías (Rubik para títulos, Nunito Sans para el texto) van incluidas en el
proyecto con licencia OFL, así que no hace falta internet para verlo bien.

Se mantienen los requisitos de accesibilidad de `docs/UI_COPY.md` §5: botones de
56 px como mínimo, alto contraste, foco visible, texto alternativo y respeto por la
preferencia de reducir movimiento.

## 7. Documentación

Los documentos de decisión y operación están en **`docs/`** (coincide con
`SPEC.md` §5.3):

| Documento | Contenido |
|---|---|
| [`docs/ENTREGA.md`](docs/ENTREGA.md) | **Qué variables pasar y cómo ejecutarlo** (para quien lo recibe). |
| [`docs/DEPLOY.md`](docs/DEPLOY.md) | **Cómo poner la aplicación en un servidor** (para quien lo administra). |
| [`docs/GITHUB.md`](docs/GITHUB.md) | Cómo subir el proyecto a GitHub y dar acceso al encargado. |
| [`docs/PLAN.md`](docs/PLAN.md) | Decisiones técnicas y variables de entorno. |
| [`docs/API.md`](docs/API.md) | Contrato de rutas, validaciones y códigos de error. |
| [`docs/PROMPTS.md`](docs/PROMPTS.md) | Prompts de los ocho estilos y rúbrica de evaluación. |
| [`docs/UI_COPY.md`](docs/UI_COPY.md) | Textos de la interfaz y mensajes de error. |
| [`docs/PROVIDER_VALIDATION.md`](docs/PROVIDER_VALIDATION.md) | Resultado de la Fase 0 (puerta G0). |
| [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md) | Pruebas automáticas, escenarios y ensayo general. |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Guía del operador para el día de la feria. |

En la raíz quedan los documentos de gobierno del proyecto: [`SPEC.md`](SPEC.md),
[`TASKS.md`](TASKS.md) y [`AGENTE_DESARROLLADOR.md`](AGENTE_DESARROLLADOR.md).

> ⚠️ **Pendiente de limpieza manual.** Los siete documentos de `docs/` todavía
> tienen una copia idéntica en la raíz: los permisos de Windows heredados en esta
> carpeta conceden a tu usuario solo lectura, así que no se pudieron borrar desde
> el entorno de desarrollo. Son duplicados exactos (mismo contenido y mismo hash).
> Para terminar la reorganización, borra las copias de la raíz:
>
> ```powershell
> Remove-Item PLAN.md, API.md, PROMPTS.md, UI_COPY.md, PROVIDER_VALIDATION.md, TEST_PLAN.md, RUNBOOK.md
> ```
>
> Hasta entonces, **la versión canónica es la de `docs/`**: cualquier corrección
> debe hacerse ahí.

## 8. Si algo falla

Consultar la tabla de contingencias de `RUNBOOK.md` §4. Los errores más comunes:

| Síntoma | Causa probable |
|---|---|
| «Abre la aplicación desde localhost» | Se entró por una IP o un nombre de red, no por `localhost`. |
| La cámara no aparece | Falta permiso del navegador o la webcam está en uso. |
| «Algo no está listo todavía» | `IMAGE_PROVIDER` o sus credenciales están mal en `.env`. |
| «No hay conexión» | El servidor no está corriendo en la terminal. |
