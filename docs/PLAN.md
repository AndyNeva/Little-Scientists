# PLAN.md — Decisiones técnicas

**Estado:** propuesta. Las decisiones marcadas ⏳ están abiertas y requieren confirmación antes o durante la fase indicada.
**Relación:** `SPEC.md` dice *qué*; este documento dice *cómo*; `TASKS.md` dice *en qué orden*.

---

## 1. Decisiones resueltas

| ID | Decisión | Motivo | Alternativa descartada |
|---|---|---|---|
| D-01 | **Servidor sin estado.** La fotografía vive solo en la memoria del navegador; el servidor la procesa y no guarda nada. No existe `POST /api/reset`. | Privacidad por defecto y menos código. | Sesión de Flask con foto en servidor. |
| D-02 | `POST /api/generate` devuelve el **PNG final como binario** en la misma respuesta. | Sin archivos ni URLs temporales en el servidor. | Guardar en disco y devolver una URL. |
| D-03 | Frontend en **JavaScript sin framework ni build**, en dos archivos: `camera.js` (stream, captura, detener pistas) y `app.js` (pantallas, estado, peticiones, limpieza). | Rapidez y claridad de responsabilidades. | React/Vue; un único archivo. |
| D-04 | Proveedores tras la interfaz `ImageGenerator`, elegidos con `IMAGE_PROVIDER` ∈ {`cloudflare`, `gemini`, `mock`}. | Migrar a Gemini sin tocar rutas ni interfaz. | Llamadas directas desde las rutas. |
| D-05 | **`mock` es a la vez doble de pruebas y modo demostración.** Genera con Pillow una imagen sintética colorida, ignora la fotografía y el título se añade igual. `GET /api/health` informa del proveedor activo y la interfaz muestra «Modo demostración» si es `mock`. | Una sola pieza cubre pruebas, desarrollo sin cuota y contingencia. | Imágenes pregeneradas por estilo. |
| D-06 | Los prompts se **redactan en `docs/PROMPTS.md`** (en inglés) y se implementan en `data/transformations.py`. El servidor construye el prompt; el navegador solo envía el `style_id`. | Los modelos suelen responder mejor en inglés; evita inyección de prompts. | Prompts enviados desde el cliente. |
| D-07 | **Título con Pillow, en una franja añadida debajo de la imagen** (el lienzo crece). Sin nombre: título predeterminado. Con nombre: `«{nombre}, {título}»`. | Garantiza que el texto nunca cubre el rostro y que tildes y ñ salgan bien. | Texto sobre la imagen; texto escrito por la IA. |
| D-08 | **Nombre:** opcional, 1 a 20 caracteres tras recortar espacios; solo letras Unicode, espacios, guion y apóstrofo. No se usa como identificador ni nombre de archivo. | Evita texto problemático y desbordes. | Texto libre. |
| D-09 | **Formato único de error** JSON `{"error": {"code", "message"}}` con códigos fijos (ver `docs/API.md`), mapeados a textos en `docs/UI_COPY.md`. | El frontend no depende del proveedor. | Mensajes ad hoc. |
| D-10 | **Logs solo de eventos:** ruta, estilo, código de resultado y duración. Nunca imágenes, nombres, claves ni cuerpos de solicitud. | Privacidad de menores. | Logs detallados para depurar. |
| D-11 | **Una generación a la vez** en el servidor (bloqueo no bloqueante → error `BUSY`) y botón deshabilitado en el cliente. | Protege la cuota gratuita y evita duplicados. | Cola de solicitudes. |
| D-12 | **Despliegue local:** `python app.py` en `127.0.0.1`. `localhost` es contexto seguro para la cámara; no se requiere HTTPS. | Un solo computador. | Servir en red local (exigiría HTTPS). |
| D-13 | **Dependencias mínimas:** `Flask`, `requests`, `Pillow`, `python-dotenv`, `pytest`, más `google-genai` para el proveedor de Gemini. | Menos superficie y arranque rápido. | Añadir SDKs innecesarios. |
| D-14 | **Tipografía** con licencia libre incluida en `static/assets/fonts/`: Fredoka (título de la imagen generada), Rubik y Nunito Sans (interfaz). Todas OFL y con tildes y ñ verificadas. | Legible para niños y sin depender de fuentes del sistema ni de internet. | Fuente del sistema o CDN remoto. |
| D-15 | **Dos proveedores intercambiables** (`cloudflare` y `gemini`) tras la misma interfaz, más `mock`. Se cambia con `IMAGE_PROVIDER`; el cambio **no se refleja en la interfaz**. | Permite migrar o reaccionar a una caída sin tocar rutas, plantillas ni JavaScript. | Un solo proveedor cableado. |
| D-16 | **El proveedor activo solo se anuncia en los registros de la terminal y en `GET /api/health`.** La pantalla nunca lo muestra; la única excepción es «Modo demostración», que la especificación obliga a avisar. | Cumple el requisito del proyecto y evita explicar a un niño qué es una API. | Mostrar el proveedor en la interfaz. |
| D-17 | **Sistema de diseño «Aventura IA Playful Clean»**, definido en `stitch_extract/.../DESIGN.md`: morados `#630ED4` / `#7C3AED`, texto `#24005B`, superficies lavanda, tipografías Rubik y Nunito Sans, formas de píldora y botones con borde inferior extruido. | Interfaz moderna, consistente y accesible, ya validada visualmente. | Estilos propios improvisados. |
| D-18 | **`google-genai` es dependencia opcional.** Solo se importa al construir el proveedor de Gemini, así que la aplicación funciona sin el SDK cuando se usa Cloudflare o la demostración. | Evita que una dependencia pesada bloquee el arranque. | Importar el SDK siempre. |

---

## 2. Decisiones abiertas ⏳

| ID | Pregunta | Propuesta | Se resuelve en |
|---|---|---|---|
| Q-01 | ¿Qué modelo concreto de Cloudflare se usará? | **Resuelto:** `@cf/black-forest-labs/flux-2-klein-9b`, validado con llamada real en la Fase 0. | Fase 0 ✅ |
| Q-02 | ¿Qué modelo de Gemini se usará? | **Resuelto:** `gemini-nano-banana-2.1`, verificado con llamada real (15–18 s, respeta la proporción de la entrada). | Fase 10 ✅ |
| Q-03 | ¿Cuál es el tiempo de espera? | **Resuelto para Cloudflare:** latencia medida de 3–5 s; se mantiene 60 s por defecto porque no estorba. | Fase 0 ✅ |
| Q-04 | ¿Resolución de entrada al proveedor? | **Resuelto:** 1024 px de lado mayor, JPEG calidad 90; Cloudflare reduce por su cuenta y Gemini acepta 1024. | Fase 0 ✅ |
| Q-05 | ¿Cómo se activa el modo demostración? | Manualmente, con `IMAGE_PROVIDER=mock` y reinicio (unos segundos). | Fase 8 |
| Q-06 | ¿Títulos neutros en género? Algunos títulos son masculinos («Capitán», «Guardián»). | Mantener los de `SPEC.md`; decidir si se ofrecen variantes neutras. | Antes de la Fase 5 |
| Q-07 | ¿Título final de `royalty`? | «Realeza de Fantasía» (ya aplicado en `SPEC.md`). | Antes de la Fase 5 |
| Q-08 | ¿Cómo se gestionan y cuándo se borran las imágenes descargadas, y qué autorización se pide? | Lo define el responsable de la feria. | Antes del evento |
| Q-09 | ¿Qué equipo se usará (sistema, navegador, webcam, internet, ¿pantalla táctil?)? | Confirmar con el responsable. | Antes de la Fase 9 |

---

## 3. Flujo de datos

```text
Navegador                         Flask                          Proveedor
 getUserMedia → canvas → Blob
 (foto en memoria)
 style_id + nombre + foto  ──►  validar entrada
                                 construir prompt (catálogo)
                                 reducir/corregir imagen  ──►  generate(bytes, prompt)
                                                          ◄──  bytes de imagen
                                 componer franja de título
 PNG final (no-store)      ◄──  responder binario
 mostrar / descargar
 «Siguiente participante» → detener cámara, borrar Blob y URLs
```

El servidor no escribe en disco ni conserva referencias tras responder.

---

## 4. Variables de entorno y el interruptor de proveedor

**Para cambiar de proveedor solo se toca una línea de `.env`:**

```dotenv
IMAGE_PROVIDER=cloudflare    # o gemini, o mock (modo demostración)
```

Después hay que reiniciar la aplicación (unos segundos). **El cambio no se refleja
en la interfaz**: el participante ve exactamente lo mismo. El proveedor activo solo
aparece en los registros de la terminal y en el campo `provider` de
`GET /api/health`, que es para el operador (D-16).

| Variable | Obligatoria | Valor por defecto | Notas |
|---|---|---|---|
| `IMAGE_PROVIDER` | Sí | `mock` | `cloudflare`, `gemini` o `mock`. Es el interruptor (D-15). |
| `CLOUDFLARE_ACCOUNT_ID` | Si `cloudflare` | — | El de la cuenta dueña del token. |
| `CLOUDFLARE_API_TOKEN` | Si `cloudflare` | — | Secreto. Necesita permisos de Workers AI. |
| `CLOUDFLARE_MODEL` | No | `@cf/black-forest-labs/flux-2-klein-9b` | Modelo validado en la Fase 0 (Q-01). |
| `GEMINI_API_KEY` | Si `gemini` | — | Secreto. Se obtiene en Google AI Studio. |
| `GEMINI_MODEL` | No | `gemini-nano-banana-2.1` | Modelo de generación y edición (Q-02). |
| `GEMINI_INPUT_MAX_SIDE_PX` | No | `1024` | Lado mayor de la foto que se envía a Gemini. |
| `REQUEST_TIMEOUT_SECONDS` | No | `60` | Q-03. |
| `MAX_UPLOAD_MB` | No | `8` | Límite de la fotografía. |
| `MAX_NAME_LENGTH` | No | `20` | Ver D-08. |
| `PORT` | No | `5000` | Cambiar si el puerto está ocupado. |
| `INPUT_MAX_SIDE_PX` | No | `1024` | Lado mayor antes de enviar la foto al proveedor. |
| `LOG_LEVEL` | No | `INFO` | Nivel de los registros de la terminal. |

`.env.example` lista todas las variables con valores ficticios. Por defecto
`IMAGE_PROVIDER=mock` evita gastar cuota por accidente.

### Comprobación de credenciales

| Proveedor | Comando |
|---|---|
| Cloudflare | `python preflight_cloudflare.py` |
| Gemini | `python preflight_gemini.py` |

Ninguno de los dos imprime las claves: solo su longitud y sus primeros caracteres,
así que su salida se puede compartir sin riesgo.

---

## 5. Puertas de control

| Puerta | Condición | Bloquea |
|---|---|---|
| **G0** | `PROVIDER_VALIDATION.md` completo y «apto». | Cualquier integración con el proveedor. |
| **G1** | Una foto produce una transformación real de extremo a extremo. | Completar los ocho prompts y el pulido. |
| **G2** | Definición de terminado cumplida y ensayo general hecho. | La migración a Gemini y cualquier extra. |
