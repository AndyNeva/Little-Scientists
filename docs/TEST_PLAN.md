# TEST_PLAN.md — Plan de pruebas

Cubre la Fase 9 de `TASKS.md` y los criterios de `SPEC.md` §12. Las pruebas automáticas usan `IMAGE_PROVIDER=mock`: no consumen cuota ni usan fotografías reales.

---

## 1. Estrategia

| Nivel | Qué cubre | Cómo |
|---|---|---|
| Automatizadas | Catálogo, validación, composición, rutas, fábrica de proveedores, privacidad | `pytest` con `mock` y `monkeypatch` |
| Manuales | Cámara real, interfaz, descarga, calidad visual con el proveedor real | Checklist de §4 |
| Ensayo general | Flujo completo en el equipo de la feria | §5 |

Regla: las pruebas con el proveedor real usan **imágenes no personales** (ilustraciones con licencia o adultos que dieron su consentimiento).

---

## 2. Pruebas automatizadas (`pytest`)

### `tests/test_transformations.py`
- [ ] El catálogo contiene exactamente los ocho `id` de `SPEC.md` §3.
- [ ] Los `id` son únicos.
- [ ] Los títulos predeterminados son únicos.
- [ ] Los prompts de estilo son únicos y no vacíos.
- [ ] `build_prompt` incluye el bloque común y el bloque del estilo.
- [ ] `build_prompt` con un `id` inexistente lanza error.
- [ ] `GET /api/transformations` no contiene el campo del prompt.

### `tests/test_image_composer.py`
- [ ] Devuelve un PNG válido.
- [ ] El alto final = alto original + franja; el ancho no cambia.
- [ ] Los píxeles de la zona de la imagen original no se modifican (el título no cubre la imagen).
- [ ] Sin nombre usa el título predeterminado.
- [ ] Con nombre usa `«{nombre}, {título}»`.
- [ ] Acepta tildes y ñ sin errores (`José`, `Núñez`, `Peña`).
- [ ] Un texto largo se ajusta o recorta sin salirse de la imagen.
- [ ] Convierte correctamente imágenes con canal alfa o en modo paleta.

### `tests/test_provider_factory.py`
- [ ] `mock` devuelve un `ImageGenerator`.
- [ ] Un valor desconocido lanza el error de configuración.
- [ ] `cloudflare` sin credenciales produce `PROVIDER_NOT_CONFIGURED`.
- [ ] `mock.generate` devuelve bytes de una imagen decodificable.

### `tests/test_routes.py`
- [ ] `GET /` responde 200.
- [ ] `GET /api/health` devuelve `status: ok`, `provider` y `demo_mode`.
- [ ] `POST /api/generate` válido → 200, `image/png`, `Cache-Control: no-store`, `X-Demo-Mode: true`.
- [ ] Sin foto → 400 `MISSING_PHOTO`.
- [ ] Archivo de texto con extensión `.png` → 400 `INVALID_IMAGE`.
- [ ] Estilo inexistente o ausente → 400 `INVALID_STYLE`.
- [ ] Nombre con caracteres no permitidos o demasiado largo → 400 `INVALID_NAME`.
- [ ] Foto por encima del límite → 413 `IMAGE_TOO_LARGE`.
- [ ] Una generación en curso → segunda solicitud 409 `BUSY`.
- [ ] Un proveedor simulado que lanza timeout → 504 `PROVIDER_TIMEOUT`.
- [ ] Un proveedor simulado con límite de uso → 429 `PROVIDER_RATE_LIMIT`.
- [ ] Un proveedor simulado sin imagen → 502 `PROVIDER_BAD_RESPONSE`.
- [ ] Un campo de prompt enviado por el cliente se ignora.
- [ ] Ninguna respuesta de error contiene claves ni trazas.
- [ ] `POST /api/reset` → 404.

### `tests/test_privacy.py`
- [ ] Tras una generación, el directorio de trabajo y el temporal no tienen archivos nuevos.
- [ ] Los logs capturados (`caplog`) no contienen el nombre ni bytes de la imagen.
- [ ] El código fuente de `static/` y `templates/` no contiene la clave de API configurada ni las palabras `API_KEY` / `API_TOKEN` con valores.
- [ ] `.gitignore` excluye `.env`.

---

## 3. Escenarios de aceptación (Dado / Cuando / Entonces)

| # | Escenario | Resultado esperado |
|---|---|---|
| E-01 | **Dado** una cámara disponible, **cuando** se pulsa *Empezar aventura* y se concede el permiso, **entonces** se ve la vista previa. | Vista previa activa. |
| E-02 | **Dado** la vista previa, **cuando** se pulsa *Tomar foto* y luego *Repetir*, **entonces** vuelve la vista previa. | Se puede repetir sin recargar. |
| E-03 | **Dado** el permiso denegado, **cuando** se intenta usar la cámara, **entonces** aparece el mensaje de `UI_COPY.md` §2. | Mensaje claro y botón de reintento. |
| E-04 | **Dado** una foto aceptada, **cuando** se elige cada uno de los ocho estilos y se pulsa *Transformarme*, **entonces** se genera una imagen por estilo. | Ocho resultados distintos. |
| E-05 | **Dado** un nombre vacío, **cuando** se genera, **entonces** la imagen muestra el título predeterminado. | Título correcto. |
| E-06 | **Dado** el nombre «Peña», **cuando** se genera, **entonces** la imagen muestra «Peña, {título}» con la ñ bien dibujada. | Título correcto. |
| E-07 | **Dado** una generación en curso, **cuando** se pulsa *Transformarme* otra vez, **entonces** no se envía una segunda solicitud. | Un solo envío. |
| E-08 | **Dado** un resultado, **cuando** se pulsa *Descargar imagen*, **entonces** se descarga un PNG con nombre seguro. | `mi_personaje.png` válido. |
| E-09 | **Dado** un resultado, **cuando** se pulsa *Probar otro personaje*, **entonces** se vuelve a la selección con la misma foto. | Sin volver a capturar. |
| E-10 | **Dado** un resultado, **cuando** se pulsa *Siguiente participante*, **entonces** vuelve la bienvenida, la cámara se apaga y no queda foto, nombre ni selección. | Estado limpio. |
| E-11 | **Dado** que el proveedor falla, **cuando** se pulsa *Intentar de nuevo*, **entonces** se reintenta sin recargar la aplicación. | Reintento posible. |
| E-12 | **Dado** `IMAGE_PROVIDER=mock`, **cuando** se completa el flujo, **entonces** se muestra «Modo demostración» y el resultado es sintético. | Contingencia operativa. |
| E-13 | **Dado** el código del navegador, **cuando** se inspecciona (fuentes y red), **entonces** no aparece ninguna clave de API. | Sin secretos en el cliente. |

---

## 4. Checklist manual

### Cámara y navegador
- [ ] La webcam funciona en el equipo, navegador y resolución de la feria.
- [ ] Al terminar un participante, la luz de la cámara se apaga.
- [ ] Funciona abierta desde `http://localhost:<puerto>`.

### Calidad visual (con el proveedor real)
- [ ] Rúbrica de `docs/PROMPTS.md` §4 aplicada a los ocho estilos.
- [ ] Probado con distintos tonos de piel, iluminación, gafas y peinados.
- [ ] El rostro es reconocible y el resultado es apropiado para niños.
- [ ] Cada estilo produce una transformación distinta.
- [ ] Latencia media medida y anotada: ____ s.

### Interfaz
- [ ] Botones grandes y legibles a distancia.
- [ ] Textos según `docs/UI_COPY.md`.
- [ ] Probado en pantalla táctil (si aplica).

### Errores simulados
- [ ] Sin internet (desconectar la red).
- [ ] Credencial inválida.
- [ ] Cuota agotada o límite de uso simulado.
- [ ] Tiempo de espera excedido.

### Privacidad
- [ ] Tras *Siguiente participante* no hay rastro del anterior en pantalla.
- [ ] No hay archivos nuevos con fotografías en la carpeta del proyecto.
- [ ] `git status` no muestra `.env` ni imágenes.

---

## 5. Ensayo general (día previo a la feria)

En el computador, navegador, webcam y red reales:

1. Arrancar la aplicación siguiendo solo el `README.md`.
2. Completar el flujo entero **al menos tres veces seguidas** con personas adultas voluntarias.
3. Probar un estilo distinto cada vez, con y sin nombre.
4. Simular un fallo del proveedor y pasar al modo demostración siguiendo `RUNBOOK.md` §5.
5. Volver al proveedor real.
6. Anotar problemas y tiempos.

**Criterio:** una persona que no desarrolló la aplicación completa el flujo sin ayuda técnica ni errores bloqueantes.

---

## 6. Registro de resultados

| Fecha | Prueba o escenario | Resultado | Notas / acción |
|---|---|---|---|
| | | | |
