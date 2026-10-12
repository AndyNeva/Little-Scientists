# PROVIDER_VALIDATION.md — Validación del proveedor (Fase 0 · Puerta G0)

**Estado:** ☐ pendiente ☐ en curso ☑ **completo**
**Fecha:** 11 de octubre de 2026 · **Responsable:** desarrollo

**DECISIÓN: ☑ APTO** — con una salvedad operativa importante sobre la cuota
gratuita (§6), que condiciona el uso en la feria.

---

## 1. Candidato evaluado

| Campo | Valor |
|---|---|
| Proveedor | Cloudflare Workers AI |
| Modelo concreto | **`@cf/black-forest-labs/flux-2-klein-9b`** (FLUX.2 [klein] 9B, Black Forest Labs) |
| Enlace a la documentación oficial del modelo | <https://developers.cloudflare.com/workers-ai/models/flux-2-klein-9b/> |
| Precios | <https://developers.cloudflare.com/workers-ai/platform/pricing/> |
| Uso de datos | <https://developers.cloudflare.com/workers-ai/platform/data-usage/> |
| Fecha en que se consultó la documentación | 11 de octubre de 2026 |

### Modelos descartados, con la medición que lo justifica

No se descartó ninguno «por lo que dice la documentación»: todos se probaron con
una llamada real y una imagen sintética no personal.

| Modelo | Resultado medido | Veredicto |
|---|---|---|
| `@cf/black-forest-labs/flux-2-dev` | **HTTP 500** («Internal server error») en 3 intentos, con y sin imagen. Además limita la entrada a <512×512, lo que degradaría el rostro. | Descartado: servicio caído |
| `@cf/black-forest-labs/flux-2-klein-4b` | Funciona, conserva la cara, pero la escena es plana y pobre comparada con el 9B. | Descartado por calidad |
| `bria/fibo-edit-1.5` | **No existe en el catálogo de Workers AI** (0 apariciones de «bria»/«fibo» en los 70 modelos). Su ficha en la documentación de Cloudflare da 404. | Descartado: inválido |
| `flux-1-schnell`, `stable-diffusion-xl-base-1.0`, `dreamshaper-8-lcm` | Funcionan (200), pero son **solo texto a imagen**: no aceptan la foto del participante. | Descartados: no sirven al caso de uso |
| `stable-diffusion-v1-5-inpainting` | Requiere máscara y está en Beta; no es transformación guiada por prompt. | Descartado |

---

## 2. Comprobaciones de documentación

| Pregunta | Respuesta | Fuente |
|---|---|---|
| ¿Admite imagen de entrada guiada por prompt? | **Sí.** Modelo con capacidad de edición y referencias múltiples; acepta la imagen en `input_image_0`. | Ficha del modelo |
| ¿Formato de entrada (base64, binario, multipart, URL)? | `multipart/form-data` con la imagen en binario. Verificado: enviarlo como JSON devuelve `required properties at '/' are 'multipart'`. | Medición propia |
| ¿Formatos y tamaño máximo de la imagen de entrada? | **Sin límite documentado para este modelo y sin límite práctico encontrado**: aceptó 400, 700, 1024 y 1400 px con latencias equivalentes. Se reduce a 1024 px por coste y tamaño de envío, no por límite. | Medición propia |
| ¿Formato de la respuesta (binario, base64, JSON)? | JSON con la imagen en **base64** en `result.image`. La imagen devuelta es **JPEG**, aunque llegue con nombre `.png`. El compositor la convierte a PNG. | Medición propia |
| ¿Cómo se autentica (variables necesarias)? | `Authorization: Bearer <CLOUDFLARE_API_TOKEN>` contra `/accounts/<CLOUDFLARE_ACCOUNT_ID>/ai/run/<modelo>`. El token necesita **`Workers AI - Read`** y **`Workers AI - Edit`**. | Guía de la REST API |
| ¿Cuota gratuita vigente y unidad de consumo? | **10.000 neuronas al día** en el plan gratuito; $0,011 por 1.000 neuronas en el plan de pago. Consumo de este modelo: 1.363,64 neuronas por el primer megapíxel de salida + 181,82 por megapíxel de imagen de entrada. **≈1.545 neuronas por generación → ≈6 generaciones al día gratis.** | Página de precios |
| ¿Límites de solicitudes por minuto o por día? | No se alcanzó ningún límite de tasa en ~20 llamadas seguidas. El límite efectivo es la cuota de neuronas. | Medición propia |
| ¿Coste por generación al superar la cuota? | **≈$0,017 por participante** (1 MP de salida + 1 MP de entrada). Con 100 participantes: ≈$1,70. | Cálculo a partir de la tabla de precios |
| ¿Condiciones sobre conservación y uso de las imágenes enviadas? | Cloudflare **no entrena** modelos con el contenido del cliente, **no lo comparte** con otros clientes y **no lo usa** para mejorar servicios sin consentimiento explícito. El contenido solo se almacena si se usa además un servicio de almacenamiento (R2, KV, etc.), que aquí **no se usa**. | Página de uso de datos |
| ¿Ubicación o tratamiento de datos relevante? | Aplican la Política de Privacidad y el Acuerdo de Suscripción de Cloudflare. No se identificó una región concreta de procesamiento. | Íd. |

### Notas de implementación derivadas

- El modelo devuelve **1024×1024** con independencia del tamaño y la proporción de
  la foto enviada. El adaptador pide explícitamente `width=height=1024` para no
  depender del valor por defecto y que el compositor reciba siempre el mismo lienzo.
- El compositor del título (Pillow) funciona correctamente con la respuesta en
  JPEG: la convierte a PNG al añadir la franja.
- Enviar `steps` y `guidance` explícitos no dio problemas; se mantienen en 25 y 3,5.

---

## 3. Imagen de prueba

- [x] La imagen **no es de un menor**.
- [x] Origen: ☐ ilustración con licencia ☐ adulto que dio su consentimiento ☑ **imagen sintética**
- [x] Descripción breve: **figura humana esquemática generada con Pillow** (900×900: cabeza, pelo, ojos, boca, torso sobre fondo con suelo). No representa a ninguna persona real. Guardada como `entrada_prueba.png` para reproducir la validación.

---

## 4. Resultados de la llamada real

| Medición | Valor |
|---|---|
| ¿La llamada devolvió una imagen utilizable? | **Sí** |
| Latencia de la primera llamada (s) | 3,1 |
| Latencia media de 3 llamadas (s) | **3,4** (rango 2,8–4,1) |
| Latencia de extremo a extremo con el título compuesto (s) | 4,3 – 5,0 |
| Consumo de cuota por llamada | ≈1.545 neuronas (≈$0,017) |
| Resolución de la imagen devuelta | 1024×1024 JPEG, convertida a PNG al añadir el título (1024×1187) |
| Errores observados (código y descripción, sin secretos) | Durante la puesta a punto: `401 Authentication error` (Account ID incorrecto), `500 AiError: Internal server error` (modelo `flux-2-dev` caído), `400 required properties at '/' are 'multipart'` (formato de petición). Con la configuración final: **ninguno**. |
| ¿Se conserva el rostro de forma reconocible? (1–5) | **4** — se mantienen el peinado, el tono de piel, la forma de la cara y la expresión. Al tratarse de una figura esquemática, la valoración con fotografías reales queda pendiente (Fase 9). |
| ¿La transformación es reconocible como el personaje pedido? (1–5) | **5** — astronauta, mago y explorador submarino se reconocen sin ambigüedad. |

### Rúbrica de `docs/PROMPTS.md` §4 sobre los estilos probados

| Criterio | Mínimo | astronaut | wizard | ocean |
|---|---|---|---|---|
| Fidelidad del rostro | 3 | 4 | 4 | 4 |
| Estilo reconocible | 4 | 5 | 5 | 5 |
| Rostro visible y despejado | Sí | Sí | Sí | Sí |
| Apropiado para niños | Sí | Sí | Sí | Sí |
| Sin texto ni marcas | Sí | Sí | Sí | Sí |
| Anatomía y artefactos | 3 | 4 | 4 | 4 |

Ningún «No» en los criterios de tipo Sí/No. Los tres estilos quedan aprobados.
Faltan los cinco estilos restantes por evaluar con la misma rúbrica (Fase 8).

---

## 5. Configuración de credenciales

1. Entrar en el panel de Cloudflare y abrir la página de **Workers AI** de la
   cuenta correcta: <https://dash.cloudflare.com/?to=/:account/ai/workers-ai>
2. Pulsar **Use REST API**.
3. Copiar el **Account ID** que aparece ahí → `CLOUDFLARE_ACCOUNT_ID`.
4. Pulsar **Create a Workers AI API Token**, revisar la plantilla y crearlo →
   `CLOUDFLARE_API_TOKEN`. Si se crea un token propio, debe llevar los permisos
   **`Workers AI - Read`** y **`Workers AI - Edit`**.
5. Pegar ambos valores en `.env`, **sin espacios** delante ni detrás.
6. Verificar con `python preflight_cloudflare.py`: debe terminar en
   «RESULTADO: credenciales correctas».

Variables confirmadas: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` y
`CLOUDFLARE_MODEL` (`docs/PLAN.md` §4). `CLOUDFLARE_MODEL` es opcional: si se deja
vacío, el adaptador usa el modelo validado.

**Errores de configuración encontrados en la puesta a punto**, por si vuelven a
aparecer:

| Síntoma | Causa | Solución |
|---|---|---|
| `401 Authentication error` en `/ai/run/` pero `/user/tokens/verify` da 200 | El `CLOUDFLARE_ACCOUNT_ID` no es el de la cuenta dueña del token | Copiar el Account ID de la página de Workers AI |
| `403 Invalid account identifier` o `Unauthorized to access requested resource` | Igual que el anterior. El endpoint informativo de la cuenta también da 403 si al token le falta permiso de lectura de cuenta, y eso **no** impide generar | Comprobar con la prueba de Workers AI, no con la de la cuenta |
| `500 AiError: Internal server error` | El modelo está caído en ese momento (`flux-2-dev` lo estaba) | Cambiar de modelo; los klein funcionan |

---

## 6. Parámetros que ajustar a partir de las mediciones

| Parámetro | Propuesta inicial | Valor decidido |
|---|---|---|
| `REQUEST_TIMEOUT_SECONDS` | 60 | **45** (la latencia medida es de 3–5 s; 45 s deja margen de sobra y evita esperas eternas) |
| Resolución de entrada (lado mayor) | 1024 px | **1024 px** (`INPUT_MAX_SIDE_PX`). El modelo acepta más, pero 1024 basta y reduce el envío. |
| Formato de envío | JPEG calidad 90 | JPEG calidad 92 para el reenvío al modelo |
| Ajustes del modelo | | `steps=25`, `guidance=3.5`, `seed` aleatorio, `width=height=1024` |

### ⚠️ Salvedad operativa: la cuota gratuita no da para una feria

Con la asignación gratuita de **10.000 neuronas al día** y un consumo de
**≈1.545 neuronas por generación**, el plan gratuito permite **unas 6 generaciones
al día**. Una feria escolar atiende a muchas más personas.

Opciones, en orden de preferencia:

1. **Plan Workers Paid** (o créditos de AI Gateway): ≈**$0,017 por participante**.
   100 participantes ≈ $1,70. Es la vía recomendada si se va a usar el proveedor real.
2. **Modo demostración** (`IMAGE_PROVIDER=mock`) si no se contrata: no gasta cuota,
   pero **no genera la imagen del niño o niña**, y hay que decírselo con claridad
   (`docs/RUNBOOK.md` §5).
3. Modelo más barato (`klein-4b`: 5,37 neuronas por tesela de entrada de 512×512 +
   26,05 por salida, ≈8 generaciones gratis al día) a cambio de bastante menos
   calidad. No resuelve el problema de fondo.

**Verificación pendiente:** confirmar el consumo real por generación en el panel
de Workers AI, y comprobar si la cuenta tiene un plan de pago activo. Hasta
entonces, ≈6 generaciones al día es una estimación a partir de la tabla de precios.

---

## 7. Decisión

- [x] **Apto:** continuar con este proveedor. Registrar el modelo en `docs/PLAN.md` (Q-01) y en `.env.example`.
- [ ] **No apto**

**Justificación:** el modelo `@cf/black-forest-labs/flux-2-klein-9b` admite
generación condicionada por imagen —el requisito crítico que la Fase 0 debía
comprobar y descartar— y devuelve resultados apropiados para niños, reconociendo
al personaje y conservando los rasgos de la figura de entrada. La latencia medida
(3,4 s de media) es cómoda para el flujo en vivo. Cloudflare declara que no entrena
ni comparte el contenido del cliente, lo que es favorable dado que el público son
menores.

**Lo que esta validación NO cubre y sigue abierto:**

- La cuota: el plan gratuito solo permite ≈6 generaciones al día (§6).
- La fidelidad del rostro con **fotografías reales**: se probó con una figura
  esquemática. Los tonos de piel, la iluminación, las gafas y los peinados reales
  hay que evaluarlos en la Fase 9 con personas adultas voluntarias.
- Los cinco estilos restantes de la rúbrica (Fase 8).
- Si la cuenta tiene plan de pago o no.

**Fecha de la decisión:** 11 de octubre de 2026

---

## 8. Aviso sobre privacidad

La validación se hizo **solo con una imagen sintética no personal**. Antes de enviar
fotografías reales de participantes deben estar resueltos los puntos de
`docs/RUNBOOK.md` §7 (autorización de los representantes legales, información a las
familias y acuerdo sobre las imágenes descargadas).

Lo que sí está verificado y conviene trasladar al responsable de la feria: según la
[política de uso de datos de Workers AI](https://developers.cloudflare.com/workers-ai/platform/data-usage/),
Cloudflare **no entrena** modelos con el contenido del cliente, **no lo comparte**
con otros clientes y **no lo usa** para mejorar servicios sin consentimiento
explícito. Aun así, la fotografía **sale del equipo y se envía a un proveedor
externo**: no se puede afirmar lo contrario.

**Alternativa sin envío de datos:** el modo demostración (`IMAGE_PROVIDER=mock`)
permite que la feria funcione sin transmitir ninguna fotografía, a cambio de no
generar la imagen real del participante.

---

# Anexo A. Segundo proveedor: Gemini

**Estado:** ☑ **completo y apto** — verificado con llamada real el 11 de octubre de 2026
**Responsable:** desarrollo

Se añadió Gemini como **segundo proveedor intercambiable** (D-15). Está implementado,
probado y **validado con llamadas reales**: funciona de extremo a extremo dentro del
flujo de la aplicación.

## A.1 Candidato evaluado

| Campo | Valor |
|---|---|
| Proveedor | Gemini (Google AI Studio) |
| Modelo | **`gemini-nano-banana-2.1`** (familia «Nano Banana») |
| Ficha oficial | <https://ai.google.dev/gemini-api/docs/models/gemini-nano-banana-2.1> |
| Guía de generación de imágenes | <https://ai.google.dev/gemini-api/docs/image-generation> |
| Precios | <https://ai.google.dev/gemini-api/docs/pricing> |
| SDK | `google-genai` 2.29.0 (PyPI), con `google.genai.Client` |
| Fecha en que se consultó la documentación | 11 de octubre de 2026 |

Se eligió este modelo y no `gemini-3-pro-image` (más caro) ni
`gemini-3.1-flash-lite-image` (el más barato, pero «no optimizado para múltiples
entradas de referencia ni edición secuencial») porque el caso de uso edita **una**
foto y prioriza coste y velocidad manteniendo calidad.

**Modelos de imagen que la clave ve** (comprobado con `models.list()`): 62 en total,
de los cuales `gemini-nano-banana-2.1`, `gemini-3.1-flash-image`,
`gemini-3.1-flash-lite-image`, `gemini-3-pro-image` y sus variantes `preview`.

## A.2 Comprobaciones de documentación

| Pregunta | Respuesta | Fuente |
|---|---|---|
| ¿Admite imagen de entrada guiada por prompt? | **Sí.** Es su función principal: edición conversacional. Entradas: texto, imagen, vídeo y PDF. Salida: imagen y texto. | Ficha del modelo |
| ¿Formato de entrada? | El SDK acepta la imagen como parte (`types.Part.from_bytes`) junto al texto. | Guía de generación |
| ¿Límites de la imagen de entrada? | No se documenta un tope de píxeles. El adaptador reduce a 1024 px de lado mayor (`GEMINI_INPUT_MAX_SIDE_PX`) por tamaño de envío, no por límite. | — |
| ¿Formato de la respuesta? | Objetos `Part`; la imagen llega en `part.inline_data.data` como bytes y **viene acompañada de una parte de texto** («Here is the transformed version…»), así que hay que recorrer las partes para encontrar la imagen. | Medición propia |
| ¿Cómo se autentica? | `GEMINI_API_KEY` en el cliente del SDK. La clave usada tiene el formato `AQ.Ab8…`, distinto del clásico `AIza…`, y **funciona correctamente**. | Medición propia |
| ¿Cuota gratuita vigente? | ✅ **La clave genera imágenes sin plan de pago.** Que la cuota gratuita alcance o no para una feria está sin confirmar: Google anunció la retirada de la generación de imágenes del plan gratuito, pero con esta cuenta funciona. **Comprobar el límite antes del evento.** | Medición propia + precios |
| ¿Coste por generación? | ⏳ **Sin verificar**: la página de precios no publica el importe por imagen de este modelo. Consultar el consumo en el panel de Google AI Studio con la clave en mano. | Página de precios |
| ¿Condiciones sobre conservación y uso de las imágenes? | ⚠️ **Pendiente y crítico.** En el plan gratuito Google declara que el contenido **sí** puede usarse para mejorar sus productos; en el de pago, no. Hay que resolverlo **antes de enviar fotografías de menores**. | Términos de la API |
| ¿Sello de marca? | Todas las imágenes generadas incluyen la marca de agua invisible **SynthID**. | Guía de generación |

## A.3 Resultados de la llamada real

| Medición | Valor |
|---|---|
| ¿La llamada devolvió una imagen utilizable? | **Sí** |
| Latencia (imagen directa, 700×700) | **14,2 – 15,0 s** |
| Latencia de extremo a extremo con el título compuesto | **15,1 – 17,9 s** |
| Formato y resolución devueltos | JPEG; **respeta la proporción de la entrada** (desde una foto 720×960 devolvió 896×1386). Con entrada cuadrada, 1024×1024. |
| Tamaño de la imagen devuelta | 825 – 850 KB |
| Errores observados | Ninguno |
| ¿Se conserva el rostro de forma reconocible? (1–5) | **4** — conserva el peinado, el tono de piel y la expresión de la figura de entrada |
| ¿La transformación es reconocible como el personaje pedido? (1–5) | **5** — astronauta y mago se reconocen sin ambigüedad, con escenas ricas y apropiadas para niños |
| ¿Rostro visible y despejado? | Sí |
| ¿Sin texto ni marcas? | Sí |
| ¿Apropiado para niños? | Sí |

Probado con los estilos `astronaut`, `wizard` y `ocean`, con y sin nombre, y con
título en español con tildes y ñ («Peña, Maestro de la Magia»).

## A.4 Comparación con Cloudflare

| | Cloudflare (`flux-2-klein-9b`) | Gemini (`nano-banana-2.1`) |
|---|---|---|
| Latencia | **3 – 5 s** | 15 – 18 s |
| Proporción de la salida | Siempre 1024×1024 (cuadrada) | **La de la foto de entrada** |
| Coste | ≈$0,017 por imagen | ⏳ sin verificar |
| Cuota gratuita | ≈6 imágenes al día | Funciona, límite por confirmar |
| Calidad observada | Muy buena | Muy buena |
| Uso de datos en plan gratuito | No entrena ni comparte el contenido | **Puede usarse para mejorar sus productos** (revisar) |

**Recomendación:** Cloudflare para la feria por velocidad (un niño espera 4 s, no 18)
y por condiciones de datos más claras. Gemini como alternativa si Cloudflare falla,
si se agota su cuota, o si se quiere conservar la proporción vertical de la foto.

## A.5 Estado de la implementación

| Elemento | Estado |
|---|---|
| `services/gemini_provider.py` | ✅ Completo, contra el SDK oficial |
| `services/provider_factory.py` | ✅ Selecciona Gemini con `IMAGE_PROVIDER=gemini` |
| Interfaz `ImageGenerator` | ✅ Cumplida (misma que Cloudflare) |
| Traducción de errores a `docs/API.md` §5 | ✅ Cuota, credenciales, tiempo de espera, respuesta inválida |
| Pruebas | ✅ 26 pruebas con el SDK simulado, incluidas las de la integración real con `google.genai.types` |
| `preflight_gemini.py` | ✅ Ejecutado: «credenciales correctas y modelo operativo» |
| Cambio de proveedor sin tocar la interfaz | ✅ Verificado por prueba automática (el HTML es idéntico) |
| **Llamada real de extremo a extremo** | ✅ **Verificada dentro de la aplicación** |

### Pendientes que no son de código

1. **Términos de uso de datos** de Google en el plan que se vaya a usar (§A.2). Es el
   punto más serio por tratarse de menores.
2. **Cuota y coste reales**, consultando el consumo en el panel de Google AI Studio.
3. Repetir la rúbrica de `docs/PROMPTS.md` §4 con los ocho estilos y con
   **fotografías reales** de adultos voluntarios (Fase 9).
