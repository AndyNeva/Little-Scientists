# API.md — Contrato HTTP

Servidor Flask local y sin estado: no guarda sesión, ni fotografías, ni resultados. Todas las rutas devuelven JSON salvo `POST /api/generate` en caso de éxito, que devuelve un PNG.

---

## 1. Convenciones

- **Errores:** siempre con este formato y el código HTTP indicado en §5.

```json
{ "error": { "code": "INVALID_IMAGE", "message": "Texto breve y sin datos sensibles." } }
```

- `message` es informativo para depurar; el texto que ve el participante viene de `docs/UI_COPY.md`, según `code`.
- Ninguna respuesta incluye claves, rutas internas, trazas ni cuerpos del proveedor.
- Las respuestas con imagen llevan `Cache-Control: no-store`.
- Los logs registran solo ruta, estilo, código y duración.

---

## 2. `GET /api/health`

Comprueba que el servidor funciona e informa del proveedor activo.

**200**
```json
{ "status": "ok", "provider": "mock", "demo_mode": true }
```

- `provider`: `cloudflare`, `gemini` o `mock`.
- `demo_mode`: `true` si `provider` es `mock`. La interfaz usa este campo para mostrar «Modo demostración».
- No revela credenciales ni estado de la cuota.

---

## 3. `GET /api/transformations`

Devuelve el catálogo. **No expone el prompt.**

**200**
```json
{
  "transformations": [
    {
      "id": "astronaut",
      "label": "Astronauta",
      "description": "Explora el espacio con tu traje espacial.",
      "default_title": "Capitán Espacial"
    }
  ]
}
```

- Siempre contiene al menos ocho elementos.
- `id` es único y es el único identificador que acepta `/api/generate`.

---

## 4. `POST /api/generate`

Recibe la fotografía, el estilo y un nombre opcional. Valida, genera con el proveedor activo, añade el título y devuelve el PNG.

**Solicitud:** `multipart/form-data`

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `photo` | archivo | Sí | JPEG, PNG o WebP; máximo `MAX_UPLOAD_MB` (8 MB por defecto); debe decodificarse como imagen real (no se confía en la extensión ni en el MIME). |
| `style_id` | texto | Sí | Debe existir en el catálogo. |
| `name` | texto | No | Tras recortar espacios: 1 a `MAX_NAME_LENGTH` (20) caracteres; solo letras Unicode, espacios, guion y apóstrofo. Vacío = sin nombre. |

No se aceptan campos de prompt ni de proveedor enviados por el cliente.

**Procesamiento en servidor**
1. Validar campos y tamaño.
2. Verificar que `photo` es una imagen real; corregir orientación EXIF; reducir resolución si hace falta.
3. Construir el prompt desde el catálogo.
4. Adquirir el bloqueo de generación; si está ocupado, responder `BUSY`.
5. Llamar a `ImageGenerator.generate(image_bytes, prompt)` con tiempo de espera.
6. Componer la franja de título con Pillow (título predeterminado o `«{nombre}, {título}»`).
7. Responder y liberar todo (sin escribir en disco).

**200** — cuerpo binario

| Cabecera | Valor |
|---|---|
| `Content-Type` | `image/png` |
| `Cache-Control` | `no-store` |
| `X-Demo-Mode` | `true` solo si el proveedor es `mock` |

---

## 5. Códigos de error

| Código | HTTP | Cuándo |
|---|---|---|
| `MISSING_PHOTO` | 400 | No se envió `photo`. |
| `INVALID_IMAGE` | 400 | El archivo no es una imagen decodificable o su formato no está permitido. |
| `INVALID_STYLE` | 400 | `style_id` ausente o fuera del catálogo. |
| `INVALID_NAME` | 400 | `name` incumple las reglas. |
| `IMAGE_TOO_LARGE` | 413 | La solicitud supera `MAX_UPLOAD_MB`. |
| `BUSY` | 409 | Ya hay una generación en curso. |
| `PROVIDER_NOT_CONFIGURED` | 500 | Falta una credencial o el valor de `IMAGE_PROVIDER` no es válido. |
| `PROVIDER_RATE_LIMIT` | 429 | El proveedor indica límite de uso o cuota agotada. |
| `PROVIDER_TIMEOUT` | 504 | Se superó `REQUEST_TIMEOUT_SECONDS`. |
| `PROVIDER_BAD_RESPONSE` | 502 | La respuesta no contiene una imagen utilizable. |
| `PROVIDER_ERROR` | 502 | Error de red o HTTP del proveedor no cubierto arriba. |
| `INTERNAL_ERROR` | 500 | Cualquier otro fallo inesperado. |

Reglas:
- Los errores de proveedor se traducen a estos códigos dentro del adaptador; el resto de la aplicación nunca ve la estructura del proveedor.
- El mensaje de error nunca contiene credenciales ni datos de la solicitud.

---

## 6. Rutas que no existen

- `POST /api/reset`: no hay estado de servidor que limpiar. Debe responder 404.
- Cualquier ruta para listar, guardar o recuperar fotografías.

---

## 7. Interfaz del proveedor (referencia interna)

```python
class ImageGenerator:
    def generate(self, image_bytes: bytes, prompt: str) -> bytes:
        """Devuelve los bytes de una imagen generada.

        Debe lanzar excepciones propias que la capa de rutas traduzca a los
        códigos PROVIDER_* de este documento.
        """
        raise NotImplementedError
```

Si ambos proveedores lo permiten, el contrato puede ampliarse con tamaño o relación de aspecto, sin romper las rutas.
