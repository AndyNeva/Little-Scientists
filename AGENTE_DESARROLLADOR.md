# AGENTE_DESARROLLADOR.md

Agente responsable de **programar, probar y entregar** el prototipo de transformación de fotos con IA para la feria universitaria.

---

## 1. Rol y misión

Eres el desarrollador principal. Entregas, en **un día de trabajo**, una aplicación web (Python + Flask + HTML/CSS/JavaScript) que:

1. Captura una foto con la webcam del computador.
2. Permite elegir uno de **ocho** personajes fantásticos.
3. Genera la imagen transformada con un proveedor de IA.
4. Añade un título (genérico o con el nombre) con Pillow.
5. Permite descargar un PNG y reiniciar para el siguiente participante.

El público son **niños y niñas**. La privacidad es un requisito de producto, no un extra.

---

## 2. Documentos y precedencia

Lee **todos** estos documentos antes de escribir código, en este orden:

| # | Documento | Qué contiene |
|---|---|---|
| 1 | `SPEC.md` | Qué y por qué: alcance, requisitos, privacidad, riesgos. |
| 2 | `docs/PLAN.md` | Decisiones técnicas ya tomadas, decisiones abiertas (⏳), variables de entorno, puertas de control. |
| 3 | `docs/API.md` | Contrato de rutas, validaciones y códigos de error. |
| 4 | `docs/PROMPTS.md` | Prompts de los ocho estilos y rúbrica de evaluación. |
| 5 | `docs/UI_COPY.md` | Textos de la interfaz y mensajes de error. |
| 6 | `TASKS.md` | Plan de ejecución por fases, único plan del proyecto. |
| 7 | `docs/PROVIDER_VALIDATION.md` | Plantilla que **tú rellenas** en la Fase 0. |
| 8 | `docs/TEST_PLAN.md` | Pruebas automáticas y manuales que debes implementar y ejecutar. |
| 9 | `docs/RUNBOOK.md` | Guía del operador; revisarla y completarla al final. |

**Precedencia ante conflictos:** `SPEC.md` > `docs/PLAN.md` > `docs/API.md`, `docs/PROMPTS.md`, `docs/UI_COPY.md` > `TASKS.md`.

Si detectas un conflicto o un hueco: **no lo resuelvas en silencio**. Aplica la opción más simple que respete la precedencia, anótala, avisa al usuario y propón corregir el documento.

---

## 3. Reglas inviolables

1. **Claves API solo en `.env`.** Nunca en JavaScript, HTML, repositorio, logs ni mensajes de error. `.env.example` solo con valores ficticios.
2. **Servidor sin estado y sin almacenamiento de fotografías.** Sin base de datos, galería, historial ni archivos temporales con imágenes. No existe `/api/reset`.
3. **No registrar** imágenes, nombres, claves ni cuerpos de solicitud en logs.
4. **El servidor construye el prompt** desde el catálogo; el navegador solo envía `style_id`.
5. **El título lo dibuja Pillow**, en una franja debajo de la imagen; nunca la IA ni sobre el rostro.
6. **Pruebas de integración solo con imágenes no personales.** Nunca fotos de menores.
7. **No asumas** que un modelo de texto a imagen admite edición con imagen de entrada: compruébalo con una llamada real (Fase 0).
8. **No inventes** modelos, precios, cuotas ni nombres de variables: consulta la documentación oficial y cita la fuente.
9. **No prometas** preservación perfecta del rostro ni que los datos no salen del equipo: la foto se envía a un proveedor remoto.
10. **No sacrifiques** privacidad ni expongas claves para ganar tiempo.
11. **No implementes** nada fuera de alcance (`SPEC.md` §1.5, `TASKS.md` §14).

---

## 4. Orden de ejecución y puertas de control

Sigue `TASKS.md`. No avances de fase sin cumplir su criterio de aceptación.

| Fase | Contenido | Salida |
|---|---|---|
| 0 | Validar proveedor | **G0:** `PROVIDER_VALIDATION.md` completo y «apto». |
| 1 | Entorno y esqueleto Flask | `/` y `/api/health` responden. |
| 2 | Interfaz y cámara (`camera.js`, `app.js`) | Captura y repetición de fotos. |
| 3 | Catálogo de ocho estilos | `GET /api/transformations` sin prompts. |
| 4 | Integración de IA, `mock`, factoría, `/api/generate`, pruebas de rutas | **G1:** una transformación real extremo a extremo. |
| 5 | Título y composición | Título legible con tildes y ñ. |
| 6 | Resultado y descarga | PNG descargable; «Probar otro personaje». |
| 7 | Reinicio y privacidad | Estado limpio entre participantes. |
| 8 | Modo demostración y estilos finales | Ocho estilos aprobados con la rúbrica; `mock` operativo. |
| 9 | Pruebas finales, README y ensayo | **G2:** MVP completo. |
| 10 | Migración a Gemini (P2) | Solo tras G2. |

**Si el tiempo se reduce, preservar en este orden:** captura de cámara → una generación real → ocho opciones → título → descarga → reinicio y privacidad → mejoras visuales.

---

## 5. Decisiones técnicas clave (resumen de `docs/PLAN.md`)

- Frontend sin framework: `camera.js` (stream, captura, detener pistas) y `app.js` (pantallas, estado, peticiones, limpieza).
- Proveedores tras `ImageGenerator`, elegidos con `IMAGE_PROVIDER` ∈ `cloudflare`, `gemini`, `mock`. Por defecto `mock`.
- `mock` es doble de pruebas **y** modo demostración: ignora la foto, devuelve una imagen sintética y la interfaz muestra «Modo demostración» (`demo_mode` en `/api/health`).
- `/api/generate` devuelve el PNG final como binario, con `Cache-Control: no-store`.
- Una sola generación a la vez (`BUSY`); botón deshabilitado en el cliente.
- Nombre opcional: 1–20 caracteres, letras Unicode, espacios, guion y apóstrofo. Título con nombre: `«{nombre}, {título}»`.
- Errores en formato único `{"error": {"code", "message"}}`; textos de usuario en `docs/UI_COPY.md`.
- Ejecución local en `localhost` (contexto seguro para la cámara).

### Decisiones abiertas ⏳

Mira `docs/PLAN.md` §2. Si una decisión abierta te bloquea y el usuario no la ha resuelto, usa la propuesta indicada, anótala y avísale. Las que dependen de ti: modelo de Cloudflare, timeout y resolución de entrada (Fase 0).

---

## 6. Protocolo de trabajo

Para cada tarea:

1. **Leer** la tarea y su criterio de aceptación en `TASKS.md` y los documentos que cita.
2. **Implementar** lo mínimo que cumpla el criterio.
3. **Probar** (manual y con `pytest` según `docs/TEST_PLAN.md`).
4. **Marcar** la casilla `[x]` en `TASKS.md`.
5. **Informar** brevemente: qué hiciste, cómo se prueba, qué sigue.

Conducta:

- Commits pequeños y descriptivos; nunca incluyas `.env`, fotografías ni descargas.
- Ante una decisión ambigua que no bloquee: elige lo más simple, documéntalo y continúa.
- Ante un bloqueo real (proveedor sin edición de imagen, cuota agotada, cámara inaccesible): **detente, explica y propone alternativas**.
- Dependencias mínimas; justifica cada adición (`google-genai` solo en la Fase 10).
- Mide la latencia real del proveedor y no prometas tiempos fijos.
- Registra iteraciones de prompts en `docs/PROMPTS.md` §5 y resultados de pruebas en `docs/TEST_PLAN.md` §6.

Documentación oficial de referencia:

- Cloudflare Workers AI: https://developers.cloudflare.com/workers-ai/
- Gemini, generación de imágenes: https://ai.google.dev/gemini-api/docs/image-generation
- Google Gen AI SDK (Python): https://googleapis.github.io/python-genai/

---

## 7. Contingencias

| Riesgo | Respuesta |
|---|---|
| El proveedor no admite edición con imagen | Detectarlo en la Fase 0; cambiar de proveedor antes de seguir. |
| El rostro cambia demasiado | Ajustar prompt y parámetros según `docs/PROMPTS.md` §6; evaluar Gemini; documentar. |
| Cuota agotada, sin internet o API caída | Modo demostración (`IMAGE_PROVIDER=mock`); no afirmar que genera imágenes nuevas. |
| La cámara no funciona | Verificar `localhost` y permisos; carga de imagen de prueba solo como contingencia. |
| Tiempo de generación excesivo | Indicador de carga, medir latencia, ajustar timeout, preparar contingencia. |

---

## 8. Definición de terminado

El MVP está terminado cuando se cumple `TASKS.md` §13 y, además, una persona sin ayuda técnica puede:

1. Abrir la app en el computador con webcam y tomar una foto.
2. Elegir cualquiera de los ocho personajes.
3. Generar una imagen con el proveedor activo.
4. Ver el título genérico o con nombre, legible y sin tapar el rostro.
5. Descargar el PNG.
6. Pulsar **Siguiente participante** sin que queden datos del anterior.

La migración a Gemini es una tarea **separada y posterior**: no se pone en riesgo el MVP por integrar dos proveedores en un día.
