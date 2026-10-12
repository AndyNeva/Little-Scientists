# UI_COPY.md — Textos de la interfaz

Idioma: español, tratamiento de **tú**. Público: niños y niñas de escuela. El operador también lee estos textos.

**Tono:** alegre, corto y claro. Una idea por mensaje.
**Evitar:** tecnicismos («API», «servidor», «cuota»), lenguaje marcado por género al dirigirse al participante («listo/lista»), culpar al niño o niña, y prometer tiempos.

---

## 1. Pantallas

### Pantalla 1 · Bienvenida

| Elemento | Texto |
|---|---|
| Título | `¡Conviértete en un personaje de aventura!` |
| Subtítulo | `Te sacamos una foto y la inteligencia artificial te transforma.` |
| Botón principal | `Empezar aventura` |
| Indicador (solo con `demo_mode`) | `Modo demostración` |

### Pantalla 2 · Fotografía

| Elemento | Texto |
|---|---|
| Instrucción | `Mira a la cámara y deja tu cara despejada.` |
| Botón de captura | `Tomar foto` |
| Tras la captura | Botones `Repetir` y `Continuar` |
| Mientras se activa la cámara | `Activando la cámara…` |

### Pantalla 3 · Selección

| Elemento | Texto |
|---|---|
| Título | `¿Quién quieres ser?` |
| Campo de nombre (etiqueta) | `Tu nombre (opcional)` |
| Campo de nombre (ayuda) | `Si lo escribes, saldrá en tu imagen.` |
| Botón principal | `Transformarme` |
| Nombre inválido | `Usa solo letras, espacios y guiones (hasta 20 caracteres).` |

Tarjetas (etiqueta y descripción corta; el título predeterminado sale en la imagen):

| ID | Etiqueta | Descripción |
|---|---|---|
| `superhero` | Superhéroe | `Vuela con tu capa y salva el día.` |
| `royalty` | Princesa o príncipe | `Un reino de fantasía te espera.` |
| `astronaut` | Astronauta | `Explora el espacio con tu traje espacial.` |
| `explorer` | Explorador de aventuras | `Descubre selvas y tesoros escondidos.` |
| `wizard` | Mago o maga | `Haz magia con tu varita brillante.` |
| `inventor` | Inventor futurista | `Crea robots e inventos del futuro.` |
| `knight` | Caballero o guardiana | `Protege un castillo de cuento.` |
| `ocean` | Explorador submarino | `Sumérgete entre peces y corales.` |

### Pantalla 4 · Procesamiento

| Elemento | Texto |
|---|---|
| Mensaje principal | `Estamos preparando tu aventura…` |
| Mensaje si tarda más de 15 s | `Ya casi… la magia necesita un poquito más.` |
| Botón (si se implementa cancelar) | `Volver` |

### Pantalla 5 · Resultado

| Elemento | Texto |
|---|---|
| Encabezado | `¡Tu personaje está aquí!` |
| Botón de descarga | `Descargar imagen` |
| Botón secundario | `Probar otro personaje` |
| Botón de cierre | `Siguiente participante · Empezar de nuevo` |
| Ayuda del botón de cierre | `Borra la foto y la elección de este niño o niña y vuelve al inicio, listo para el siguiente de la fila.` |
| Si la descarga falla | `No pudimos descargar la imagen. Inténtalo otra vez.` |

> El botón de cierre se amplió el 11 de octubre de 2026. Antes decía solo
> «Siguiente participante» y se mostraba como botón fantasma (discreto): el
> operador podía quedarse buscando cómo volver al inicio para el siguiente niño.
> Ahora es un botón destacado y el texto dice explícitamente que reinicia el flujo.
> El reinicio borra la foto, la elección, el nombre y la barra de progreso, apaga
> la cámara y libera las URLs temporales (`SPEC.md` §10).

---

## 2. Errores de cámara

Detectar por el nombre del error de `getUserMedia`:

| Situación | Texto | Acción para el operador |
|---|---|---|
| `NotAllowedError` (permiso denegado) | `Necesitamos permiso para usar la cámara. Pídele ayuda a la persona encargada.` | Permitir la cámara en el navegador y recargar. |
| `NotFoundError` (no hay cámara) | `No encontramos una cámara conectada.` | Revisar la conexión de la webcam. |
| `NotReadableError` (cámara en uso) | `La cámara está ocupada por otra aplicación.` | Cerrar la otra aplicación. |
| Contexto no seguro (sin HTTPS ni `localhost`) | `Abre la aplicación desde localhost para usar la cámara.` | Usar `http://localhost:5000`. |
| Cualquier otro error | `No pudimos activar la cámara. Pídele ayuda a la persona encargada.` | Revisar la consola y el navegador. |

Botón en todos los casos: `Intentar de nuevo`.

---

## 3. Errores de generación

Se muestran según el campo `error.code` de `docs/API.md`. Siempre con botón `Intentar de nuevo` y, cuando aplique, `Elegir otro personaje`.

| Código | Texto para el participante | Nota para el operador |
|---|---|---|
| `MISSING_PHOTO` / `INVALID_IMAGE` | `Esa foto no se pudo usar. Vamos a tomar otra.` | Volver a la captura. |
| `INVALID_STYLE` | `Elige uno de los personajes para continuar.` | |
| `INVALID_NAME` | `Usa solo letras, espacios y guiones (hasta 20 caracteres).` | |
| `IMAGE_TOO_LARGE` | `La foto es demasiado grande. Vamos a tomar otra.` | |
| `BUSY` | `Estamos terminando otra aventura. Espera un momento.` | |
| `PROVIDER_RATE_LIMIT` | `Hay muchas aventuras en preparación. Espera un momento y vuelve a intentarlo.` | Si persiste, activar el modo demostración (`RUNBOOK.md` §5). |
| `PROVIDER_TIMEOUT` | `Esto está tardando más de lo normal. Inténtalo otra vez.` | |
| `PROVIDER_BAD_RESPONSE` / `PROVIDER_ERROR` | `No pudimos crear tu personaje esta vez. Inténtalo otra vez.` | Revisar la conexión; si persiste, modo demostración. |
| `PROVIDER_NOT_CONFIGURED` | `Algo no está listo todavía. Pídele ayuda a la persona encargada.` | Revisar `.env` y `IMAGE_PROVIDER`. |
| `INTERNAL_ERROR` | `Algo salió mal. Inténtalo otra vez.` | |
| Sin conexión del navegador con el servidor | `No hay conexión. Pídele ayuda a la persona encargada.` | Verificar que el servidor esté corriendo. |

---

## 4. Mensaje de privacidad (pantalla de bienvenida, texto pequeño)

`Tu foto se usa solo para crear tu personaje y no se guarda.`

> Verificar que esta frase sea cierta para el proveedor activo antes del evento. Al usar una API remota, la fotografía se envía al proveedor para procesarse; el texto final debe acordarse con el responsable de la feria (`PLAN.md` Q-08).

---

## 5. Accesibilidad básica

- Botones grandes y de alto contraste.
- Todo botón con texto visible, no solo icono.
- Mensajes de error visibles junto a la acción que falló.
- Foco visible al navegar con teclado.
- Fuente legible y tamaño mínimo 18 px en textos principales.
