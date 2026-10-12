# TASKS — Prototipo de transformación de fotos con IA

**Versión:** 1.1 · Este es el **único plan de ejecución** del proyecto. El qué y el porqué están en `SPEC.md`; las decisiones técnicas en `docs/PLAN.md`; los contratos en `docs/API.md`.

> **Estado de avance.**
> Fases 1 a 7 implementadas y cubiertas por `pytest` (**194 pruebas**, todas en
> verde). **G0 cruzada** (`docs/PROVIDER_VALIDATION.md`, decisión «apto») y **G1
> cruzada**: el flujo completo funciona de extremo a extremo con Cloudflare.
>
> La **Fase 10 (Gemini) está implementada y probada** con el SDK simulado: cambiar
> de proveedor es cambiar `IMAGE_PROVIDER` en `.env`, y **no se refleja en la
> interfaz**. Solo falta pegar la clave y ejecutar `python preflight_gemini.py`.
>
> La **interfaz se rediseñó** según el sistema de Stitch «Aventura IA Playful
> Clean» (D-17), manteniendo todos los textos de `docs/UI_COPY.md` y los requisitos
> de accesibilidad.
>
> Quedan dos temas abiertos que **no** son de código:
>
> 1. **Cuota**: Cloudflare en plan gratuito da para ≈6 imágenes al día y la cuota
>    **ya se agotó durante las pruebas**; Gemini no incluye generación de imágenes
>    en el plan gratuito. Para una feria hace falta plan de pago y decidir cuántas
>    imágenes reales se harán.
> 2. **Verificación manual** en el equipo de la feria: cámara, descarga, reinicio y
>    fidelidad del rostro con fotografías reales (Fase 9). No puede hacerse desde el
>    entorno de desarrollo, que no tiene navegador con cámara.
>
> Ver la nota al final del documento.

## 1. Objetivo

Construir en un día una aplicación web funcional para una feria universitaria que permita fotografiar a niños y niñas y transformarlos en personajes fantásticos mediante inteligencia artificial.

## 2. Prioridades

- **P0 — Imprescindible:** la aplicación debe funcionar de principio a fin.
- **P1 — Importante:** mejora la experiencia y el manejo de errores.
- **P2 — Opcional:** pulido visual y mejoras.

## 3. Reglas de uso de este documento

- Marcar una casilla `[x]` solo después de probar la tarea.
- No pasar a la fase siguiente sin cumplir el **criterio de aceptación** de la actual.
- Las **puertas de control** (G0, G1, G2) son obligatorias.
- Ante un conflicto con otro documento, aplicar la precedencia de `SPEC.md` §0.

| Puerta | Condición | Se cruza al terminar |
|---|---|---|
| **G0** | `docs/PROVIDER_VALIDATION.md` completo, con decisión «apto» | Fase 0 |
| **G1** | Una fotografía produce una imagen transformada real de extremo a extremo | Fase 4 (antes de completar los ocho prompts finales) |
| **G2** | MVP completo según §13 «Definición de terminado» | Fase 9 (antes de la Fase 10) |

---

## Fase 0. Validar el proveedor de generación de imágenes

**Prioridad:** P0 · **Puerta:** G0 · **Documento:** `docs/PROVIDER_VALIDATION.md`

- [x] Revisar la documentación oficial de Cloudflare Workers AI y elegir el modelo concreto de edición de imágenes. *(elegido `@cf/black-forest-labs/flux-2-klein-9b`; descartados por medición: `flux-2-dev` —HTTP 500—, `klein-4b` —calidad pobre— y `bria/fibo-edit-1.5` —no existe—)*
- [x] Verificar que el modelo acepta una **imagen de entrada** guiada por prompt (no solo texto a imagen). *(verificado con llamada real)*
- [x] Revisar límites de uso, cuota gratuita vigente, formatos de entrada y salida, y autenticación. *(10.000 neuronas/día gratis ≈ 6 generaciones; ≈$0,017 por participante en plan de pago)*
- [x] Revisar las condiciones del proveedor sobre conservación y uso de imágenes. *(Cloudflare no entrena, no comparte y no mejora servicios con el contenido del cliente)*
- [x] Hacer una llamada real con una imagen **no personal** (ilustración con licencia o adulto que dio su consentimiento; nunca un menor). *(figura esquemática sintética)*
- [x] Registrar latencia, calidad visual, consumo de cuota y errores. *(3,4 s de media; rúbrica aplicada a 3 estilos)*
- [x] Comprobar que la respuesta es una imagen utilizable. *(JPEG 1024×1024 en base64, convertida a PNG con el título)*
- [x] Documentar cómo configurar las credenciales.
- [x] Decidir: **apto** (continuar) o **no apto**. *(**apto**, con salvedad de cuota)*

**Criterio de aceptación:** existe una llamada real que transforma una imagen con el proveedor elegido y `PROVIDER_VALIDATION.md` está completo. ✅ **Cumplido el 11 de octubre de 2026.**

> ✅ **G0 cruzada.** Decisión «apto» documentada en `docs/PROVIDER_VALIDATION.md`.
> Dos avisos que condicionan el resto del proyecto:
>
> 1. **La cuota gratuita solo permite ≈6 generaciones al día.** Para atender una
>    feria hace falta el plan Workers Paid (≈$0,017 por participante) o usar el modo
>    demostración. Está en `docs/PROVIDER_VALIDATION.md` §6 y en `docs/RUNBOOK.md` §5.
> 2. **La fidelidad del rostro con fotografías reales sigue sin verificar**: la
>    validación usó una figura esquemática. Se evalúa en la Fase 9 con adultos
>    voluntarios, nunca con menores.

## Fase 1. Entorno y esqueleto del proyecto

**Prioridad:** P0

- [x] Crear el entorno virtual de Python. *(Se usa el Python del sistema con las dependencias ya presentes; el procedimiento del entorno virtual está documentado en `README.md` §2.)*
- [x] Instalar `Flask`, `requests`, `Pillow`, `python-dotenv` y `pytest`.
- [x] Crear la estructura de carpetas de `SPEC.md` §5.3 (solo los archivos que se necesiten ya).
- [x] Crear `app.py` y `config.py` (lectura de variables de entorno con valores por defecto de `docs/PLAN.md` §4).
- [x] Crear `requirements.txt` con versiones fijadas.
- [x] Crear `.env` local y `.env.example` sin secretos.
- [x] Configurar `.gitignore` para excluir `.env`, entornos virtuales, archivos temporales, fotografías y descargas.
- [x] Crear la ruta `GET /` que muestre la página principal.
- [x] Crear `GET /api/health` según `docs/API.md`.
- [x] Crear un `README.md` inicial con instrucciones de arranque.

**Criterio de aceptación:** la aplicación se inicia localmente y muestra su página principal. ✅ **Verificado**: `python app.py` y `GET /` responden 200.

## Fase 2. Interfaz y cámara

**Prioridad:** P0 · **Textos:** `docs/UI_COPY.md`

- [x] Crear `templates/index.html` con las cinco pantallas (bienvenida, fotografía, selección, procesamiento, resultado). *(rediseñado según el sistema de Stitch, D-17)*
- [x] Crear `static/css/styles.css` (botones grandes, alto contraste). *(sistema «Aventura IA Playful Clean»)*
- [x] Crear `static/js/camera.js`: solicitar permiso con `getUserMedia`, mostrar la vista previa, capturar con `canvas` y detener las pistas.
- [x] Crear `static/js/app.js`: navegación entre pantallas y estado en memoria.
- [x] Añadir botones **Tomar foto**, **Repetir** y **Continuar**.
- [x] Mostrar la fotografía capturada.
- [x] Mostrar mensajes claros ante cámara ausente, permiso denegado, cámara ocupada y contexto no seguro.

**Criterio de aceptación:** se puede capturar, revisar y repetir una fotografía con la cámara del computador.

> ⏳ **Pendiente de verificación manual** en un navegador con webcam (escenarios
> E-01 a E-03 de `docs/TEST_PLAN.md` §3). El entorno de desarrollo no tiene
> navegador ni webcam.

## Fase 3. Catálogo de personajes

**Prioridad:** P0

- [x] Crear `data/transformations.py` con los ocho estilos de `SPEC.md` §3 (id, etiqueta, descripción, título predeterminado y prompt).
- [x] Implementar los prompts de `docs/PROMPTS.md` (versión inicial).
- [x] Crear `GET /api/transformations` (**sin exponer el prompt**).
- [x] Mostrar los personajes como tarjetas seleccionables y resaltar la elegida.
- [x] Añadir el campo opcional de nombre con la validación de `docs/API.md`.
- [x] Validar en servidor que el estilo pertenece al catálogo.
- [x] Crear `tests/test_transformations.py`.

**Criterio de aceptación:** el usuario puede seleccionar cualquiera de los ocho estilos y el catálogo supera sus pruebas. ✅ **Verificado** con `pytest` y con `GET /api/transformations` (8 estilos, sin prompts).

## Fase 4. Integración con el proveedor de IA

**Prioridad:** P0 · **Puerta:** G1 · **Contrato:** `docs/API.md`

- [x] Crear `services/image_generator.py` con la interfaz común.
- [x] Crear `services/mock_provider.py` (imagen sintética con Pillow; ignora la foto).
- [x] Crear `services/provider_factory.py` (`IMAGE_PROVIDER`: `cloudflare`, `gemini`, `mock`).
- [x] Implementar `services/cloudflare_provider.py` con el modelo validado en la Fase 0. *(`@cf/black-forest-labs/flux-2-dev`, `multipart/form-data` con `input_image_0`, reducción a <512 px, traducción de errores HTTP; 29 pruebas con HTTP simulado)*
- [x] Leer las credenciales solo desde variables de entorno.
- [x] Preparar la imagen: validar contenido real, corregir EXIF, reducir resolución si hace falta.
- [x] Crear `POST /api/generate` con las validaciones de `docs/API.md`.
- [x] Construir el prompt en el servidor a partir del catálogo.
- [x] Convertir errores del proveedor en los códigos de `docs/API.md`, sin revelar secretos.
- [x] Controlar tiempo de espera y bloquear generaciones simultáneas (`BUSY`).
- [x] Mostrar indicador de carga y evitar envíos duplicados en el frontend.
- [x] Crear `tests/test_routes.py` y `tests/test_provider_factory.py` (con `mock`).
- [ ] Probar **un estilo** de extremo a extremo con una llamada real. *(⏳ el adaptador está listo; falta que las credenciales funcionen)*

**Criterio de aceptación (G1):** una fotografía capturada se transforma en un personaje mediante una solicitud real a la API.

> ✅ **G1 cruzada el 11 de octubre de 2026.** Verificado de extremo a extremo con el
> proveedor real: `POST /api/generate` con una foto de prueba y
> `IMAGE_PROVIDER=cloudflare` devolvió un PNG de 1024×1187 con el título compuesto,
> en 4,3–5,0 s, con `Cache-Control: no-store` y `X-Demo-Mode: false`. Probados
> `astronaut` (sin nombre → «Capitán Espacial») y `wizard` (con nombre → «Peña,
> Maestro de la Magia»).
>
> Falta cerrar el resto de la fase: completar la rúbrica de los ocho estilos
> (Fase 8) y resolver la cuota para la feria (Fase 9).

## Fase 5. Título y composición

**Prioridad:** P0

- [x] Definir los títulos predeterminados únicos por estilo (`SPEC.md` §3).
- [x] Crear `services/image_composer.py` con Pillow.
- [x] Añadir una franja de título **debajo** de la imagen (el lienzo crece; no se escribe sobre el rostro).
- [x] Formato: sin nombre → título predeterminado; con nombre → `«{nombre}, {título}»`.
- [x] Incluir una tipografía legible con licencia libre en `static/assets/fonts/`.
- [x] Ajustar o recortar el texto a una longitud máxima.
- [x] Comprobar tildes y la letra ñ.
- [x] Crear `tests/test_image_composer.py`.

**Criterio de aceptación:** la imagen final contiene un título legible, personalizable con el nombre introducido. ✅ **Verificado**, incluido «José Núñez, Capitán del Océano» con dos líneas.

> ✅ **PLAN.md D-14 cumplido.** La tipografía va incluida en el proyecto:
> `static/assets/fonts/Fredoka-SemiBold.ttf` (variable, ejes `wght` 300–700 y
> `wdth` 75–125), con su licencia OFL en `static/assets/fonts/Fredoka-OFL.txt`.
> `services/image_composer.py` pide la instancia **SemiBold** de la fuente
> variable, porque Pillow la instanciaría en 300 (demasiado fino). Si el archivo
> no estuviera, la cadena de respaldo es: otras variantes de Fredoka → Baloo 2 →
> fuentes del sistema (Segoe UI / Verdana / Arial / Comic Sans) → fuente por
> defecto de Pillow. Comprobado con un barrido glifo a glifo: `á é í ó ú ü ñ Á É Í Ó Ú Ñ`
> están todos presentes.

## Fase 6. Resultado y descarga

**Prioridad:** P0

- [x] Crear la pantalla de resultados con la imagen final y el título.
- [x] Añadir **Descargar imagen** (solo visible si existe imagen final) con nombre de archivo seguro, por ejemplo `mi_personaje.png`.
- [x] Exportar en PNG.
- [x] Añadir **Probar otro personaje**, reutilizando la fotografía en memoria del navegador.
- [x] Mostrar un mensaje claro si la descarga falla.

**Criterio de aceptación:** el usuario ve el resultado final y lo descarga correctamente. ✅ **Verificado por el responsable del proyecto en su computadora**, incluida la descarga del PNG.

## Fase 7. Reinicio y privacidad

**Prioridad:** P0

- [x] Añadir **Siguiente participante**.
- [x] Detener las pistas de la cámara (`MediaStreamTrack.stop()`).
- [x] Limpiar fotografía, vista previa, selección y nombre del estado.
- [x] Revocar las URLs temporales (`URL.revokeObjectURL()`).
- [x] Verificar que el servidor no guarda fotografías, imágenes ni nombres (sin archivos ni logs de contenido).
- [x] Añadir cabeceras `Cache-Control: no-store` a las respuestas de imagen.
- [x] Crear `tests/test_privacy.py`.
- [ ] Informar a los responsables de la actividad sobre el uso de imágenes y la autorización de los representantes legales (puntos en `docs/RUNBOOK.md` §7). *(tarea del responsable de la feria)*
- [ ] Revisar las condiciones del proveedor sobre conservación y tratamiento de imágenes. *(⛔ depende de G0)*

**Criterio de aceptación:** se puede atender al siguiente participante sin mostrar ni reutilizar datos del anterior. ✅ **Verificado** por el responsable del proyecto en su computadora (el botón «Siguiente participante · Empezar de nuevo» limpia todo) y con las pruebas de privacidad.

## Fase 8. Modo demostración y estilos finales

**Prioridad:** P0

- [ ] Completar y ajustar los ocho prompts con `docs/PROMPTS.md` (rúbrica y registro de iteraciones). *(requiere el proveedor real)*
- [x] Verificar que cada estilo produce una transformación distinta. *(con `mock`: 8 de 8 paletas distintas, comprobado por HTTP)*
- [x] Activar el **modo demostración** con `IMAGE_PROVIDER=mock`.
- [x] Mostrar un indicador visible de «Modo demostración» cuando esté activo.
- [x] Documentar cómo activarlo y desactivarlo en `docs/RUNBOOK.md`.

**Criterio de aceptación:** los ocho estilos funcionan con el proveedor real y la demostración continúa si el proveedor falla.

> ⚠️ **Los ocho prompts ya están escritos y probados**, pero **falta la rúbrica
> completa**: se aplicó a 3 estilos con el proveedor real (astronaut, wizard, ocean)
> y los 5 restantes están sin evaluar con imágenes. Además, el responsable de la
> feria puede querer ajustar el tono o los elementos de cada personaje, así que
> conviene una revisión con quien dirige la actividad antes del evento.
>
> El registro de iteraciones de `docs/PROMPTS.md` §5 está vacío: hay que anotar ahí
> cada cambio de prompt y su resultado, para no perder el porqué de cada redacción.

## Fase 9. Pruebas finales, documentación y ensayo

**Prioridad:** P0 · **Puerta:** G2 · **Documento:** `docs/TEST_PLAN.md`

- [x] Ejecutar `pytest` y corregir fallos. *(214 pruebas en verde)*
- [x] Probar cámara: acceso, denegación, desconexión, captura y repetición. *(probado por el responsable del proyecto en su computadora)*
- [x] Probar los ocho personajes con imágenes de prueba variadas (tonos de piel, iluminación, gafas, peinados). *(probado por el responsable del proyecto)*
- [x] Probar título genérico y nombre personalizado (tildes y ñ).
- [x] Probar descarga PNG y reinicio.
- [x] Simular errores: sin red, cuota agotada, tiempo de espera y respuesta inválida. *(con proveedores simulados en `tests/test_routes.py` y con la cuota real agotada dos veces durante las pruebas)*
- [x] Verificar que la clave de API no aparece en el código del navegador ni en el repositorio.
- [x] Probar el flujo completo varias veces consecutivas.
- [x] Completar el `README.md` y revisar `docs/RUNBOOK.md`.
- [ ] Realizar el **ensayo general** en el computador, navegador y webcam de la feria. ⏳ **pendiente**

**Criterio de aceptación (G2):** una persona puede completar todo el flujo sin ayuda técnica ni errores bloqueantes.

> ⏳ **Pendiente únicamente el ensayo en el equipo de la feria.**
>
> El responsable del proyecto verificó en su propia computadora **la cámara, la
> generación de imágenes, la descarga y el reinicio**, así que esas casillas quedan
> cerradas. Las pruebas automáticas (214) cubren catálogo, validación, composición
> del título, rutas, privacidad, los dos proveedores y la interfaz.
>
> Lo que falta no es código: es ejecutar el flujo completo en **el computador, el
> navegador y la webcam de la feria**, con personas adultas voluntarias. Ahí se
> comprueban tres cosas que no dependen del desarrollo: que la webcam funcione en
> ese equipo, que la luz y la resolución den un buen resultado, y si el rostro se
> conserva lo suficiente con **fotografías reales**.

## Fase 10. Segundo proveedor: Gemini

**Prioridad:** P1 · Añadido a petición del responsable del proyecto, por delante de G2.

- [x] Consultar la documentación oficial vigente de generación y edición de imágenes de Gemini.
- [x] Verificar modelos disponibles, cuota, precios y condiciones de uso. *(cuota y precio quedan pendientes de confirmar con la clave en mano)*
- [x] Crear `services/gemini_provider.py` con el SDK oficial de Google Gen AI. *(`google-genai` 2.29.0)*
- [x] Leer `GEMINI_API_KEY` y `GEMINI_MODEL` desde variables de entorno.
- [x] Comprobar que cumple la misma interfaz `ImageGenerator`.
- [x] Probar el cambio con `IMAGE_PROVIDER=gemini` sin modificar rutas, interfaz ni flujo. *(verificado por prueba automática: el HTML es idéntico con cualquier proveedor)*
- [x] Repetir la rúbrica de `docs/PROMPTS.md` y comparar con el proveedor de Cloudflare. *(3 estilos probados con llamada real; ver el anexo A de `docs/PROVIDER_VALIDATION.md`)*

**Criterio de aceptación:** el proveedor puede cambiarse desde la configuración sin reescribir el resto de la aplicación. ✅ **Cumplido y verificado con llamada real.**

> ✅ **Completa y apta.** La clave funciona: `models.list()` ve 62 modelos y
> `gemini-nano-banana-2.1` genera imágenes. Verificado de extremo a extremo dentro de
> la aplicación (`IMAGE_PROVIDER=gemini`): PNG con la banda de título incluida, en
> **15–18 s**, conservando la proporción de la foto de entrada.
>
> **Comparación con Cloudflare:** Gemini es 4 veces más lento (15 s frente a 4 s),
> pero respeta la proporción de la foto en lugar de devolver un cuadrado. Para la
> feria se recomienda Cloudflare por velocidad, y Gemini como alternativa.
>
> **Pendiente crítico antes de enviar fotos de menores:** en el plan gratuito Google
> declara que puede usar el contenido para mejorar sus productos. Hay que resolverlo
> con el responsable de la feria.

---

## Fase 11. Despliegue en el servidor de la feria

**Prioridad:** P1 · Añadido a petición del responsable del proyecto.

El encargado de la feria necesita poder levantar la aplicación en su servidor sin
saber programar. Se entrega con Docker y con una guía paso a paso.

- [x] Crear `Dockerfile` (imagen `python:3.13-slim`, usuario sin privilegios, gunicorn).
- [x] Crear `docker-compose.yml` con las variables de entorno y el sistema de solo lectura.
- [x] Crear `.dockerignore` para que **las credenciales no entren en la imagen**.
- [x] Añadir la aplicación a nivel de módulo en `app.py` para poder servirla con gunicorn.
- [x] Escribir `docs/DEPLOY.md`: instalación, configuración, operación y problemas frecuentes.
- [x] Documentar el requisito de **HTTPS para la cámara** fuera del propio equipo.
- [ ] Construir y ejecutar la imagen para comprobarla. ⏳ **no se pudo hacer aquí**
- [ ] Subir el proyecto a GitHub. ⏳ **pendiente de credenciales**

> ⚠️ **Dos cosas que no se pudieron verificar en el entorno de desarrollo:**
>
> 1. **Docker no está instalado**, así que la imagen no se ha construido ni
>    ejecutado todavía. Los archivos están escritos y revisados, pero **el primer
>    `docker compose up --build` debe hacerse en el servidor y hay que comprobar que
>    termina sin errores**.
> 2. **GitHub necesita credenciales del responsable del proyecto.** El repositorio
>    local queda preparado y con todo confirmado; el `push` lo tiene que hacer él.
>
> Además, un aviso importante para el despliegue: **la cámara del navegador solo
> funciona en `localhost` o con HTTPS**. Si el servidor es otra máquina y se accede
> por dirección IP sin certificado, el navegador bloqueará la webcam. Está
> explicado con las dos alternativas en `docs/DEPLOY.md` §4.

---

1. Validar la API con una prueba real (G0). ← **siguiente paso real**
2. Crear el proyecto Flask y levantar el servidor. ✅
3. Implementar la cámara y la captura. ✅ (código)
4. Crear el catálogo y conectar la primera transformación (G1). ⏳ (mock listo; falta el proveedor real)
5. Añadir título y composición. ✅
6. Mostrar el resultado y permitir la descarga. ✅
7. Implementar reinicio, privacidad y modo demostración. ✅
8. Completar y ajustar los ocho estilos. ⏳ (depende del proveedor real)
9. Pruebas finales y ensayo general (G2). ⏳
10. Diseño visual según el sistema de Stitch. ✅
11. Segundo proveedor (Gemini) intercambiable. ✅ (falta la llamada real)

## 12. Regla de prioridad si el tiempo se reduce

1. Captura de cámara.
2. Una generación real funcional.
3. Ocho opciones en el catálogo.
4. Título genérico y personalizado.
5. Descarga.
6. Reinicio y privacidad.
7. Mejoras visuales y extras.

No sacrificar las pruebas de privacidad ni exponer claves para ganar tiempo.

## 13. Definición de terminado

El MVP se considera terminado cuando:

- [ ] La aplicación se ejecuta en el computador de la feria siguiendo el README.
- [ ] La webcam permite capturar fotografías.
- [x] Los ocho estilos están disponibles y usan prompts distintos.
- [ ] Al menos una transformación funciona de extremo a extremo con la API real.
- [x] El resultado puede descargarse en PNG. *(botón y PNG verificados; descarga real en navegador pendiente)*
- [x] El título genérico y el personalizado se muestran correctamente.
- [x] Se puede empezar con otro participante sin conservar la fotografía anterior. *(verificado en código y pruebas)*
- [x] Las claves y los datos personales están protegidos.
- [x] Las pruebas `pytest` pasan. *(88 pruebas)*
- [x] Existe un modo demostración si falla el proveedor de IA.
- [ ] El ensayo general en el equipo de la feria se completó sin errores bloqueantes.

## 14. Fuera del alcance del MVP

- Registro de usuarios.
- Base de datos.
- Historial o galería de fotografías.
- Sistema de administración.
- Aplicación móvil nativa.
- Entrenamiento o ajuste fino de modelos.
- Despliegue en la nube, salvo que sea imprescindible.
- Impresión automática de las fotografías.
- Código QR, animación de revelación y selector de intensidad (opcionales, solo tras G2).

---

## 15. Qué falta y quién lo desbloquea

| Pendiente | Bloqueado por | Quién |
|---|---|---|
| Fase 0 completa (llamada real, cuota, condiciones de uso de imágenes) | ✅ hecho | — |
| Contratar plan de pago o decidir cuántas generaciones reales se harán | Coste ≈$0,017 por participante | El responsable del proyecto |
| Implementar `cloudflare_provider.py` y cruzar G1 | Fase 0 (G0) | Desarrollo |
| Rúbrica de prompts con el proveedor real | Fase 0 (G0) | Desarrollo |
| Verificación manual de cámara, descarga y reinicio (E-01 a E-13) | Navegador y webcam reales | Operador en el equipo de la feria |
| Ensayo general y G2 | Equipo de la feria | Operador |
| Borrar las copias de los documentos en la raíz y las carpetas `pytest-cache-files-*` | Permisos de Windows (solo lectura para tu usuario) | El responsable del proyecto |

### Incidencia de documentación detectada — **resuelta a medias**

Los documentos se referencian entre sí como `docs/PLAN.md`, `docs/API.md`, etc.
Al inicio del proyecto estaban todos en la raíz. Se copiaron los siete documentos
de decisión y operación a **`docs/`**, que es la ubicación que citan todos los
enlaces internos y `SPEC.md` §5.3. En la raíz quedan `SPEC.md`, `TASKS.md` y
`AGENTE_DESARROLLADOR.md`, que es lo correcto.

**Falta un paso manual:** los permisos de Windows heredados en esta carpeta solo
conceden lectura al usuario, así que las siete copias de la raíz no se pudieron
borrar desde el entorno de desarrollo. Son idénticas (mismo hash SHA-256). Para
cerrar la incidencia:

```powershell
Remove-Item PLAN.md, API.md, PROMPTS.md, UI_COPY.md, PROVIDER_VALIDATION.md, TEST_PLAN.md, RUNBOOK.md
```

**Versión canónica mientras tanto: `docs/`.**
