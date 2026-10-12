# PROMPTS.md — Prompts de transformación y evaluación

Fuente de redacción de los prompts. La implementación vive en `data/transformations.py`; si este documento y el código difieren, se corrige el código.

**Idioma:** inglés (suelen dar mejores resultados con los modelos de imagen). Las etiquetas visibles para el usuario siguen en español.

**Estado:** versión inicial. Se ajusta con pruebas reales en la Fase 8 y se registra en §5.

---

## 1. Reglas de redacción

1. Pedir un resultado **amable, alegre y apropiado para todos los públicos**: sin elementos aterradores, sin violencia y sin armas.
2. Pedir conservar **rasgos faciales reconocibles, edad aparente, tono de piel, cabello y expresión**, sin prometer que el modelo lo logre.
3. Mantener **rostro visible y despejado**: sin máscaras, viseras cerradas ni sombreros que lo tapen.
4. **No pedir texto, letras, logotipos ni marcas de agua**: el título lo añade Pillow.
5. El estilo no depende del género del participante: usar ropa y accesorios neutros.
6. El prompt final = **bloque común** + **bloque del estilo**. El cliente solo envía `style_id`.

---

## 2. Bloque común

```text
Transform the person in this photo into the character described below.
Keep the person's recognizable facial features, apparent age, skin tone, hair
and expression. The person must still look like the same child, not an adult.
Show head and upper body, facing the camera, with the face fully visible and
unobstructed. Friendly, cheerful, colorful storybook illustration style that is
safe and appropriate for all ages. No weapons, no scary or violent elements.
Do not add any text, letters, numbers, logos or watermarks.
```

---

## 3. Bloques por estilo

| ID | Bloque de estilo |
|---|---|
| `superhero` | `Character: a friendly superhero in a bright, colorful costume with a flowing cape and a star emblem on the chest. No mask covering the face. Background: a sunny city skyline at sunrise.` |
| `royalty` | `Character: fantasy royalty wearing rich, colorful royal clothes and a small golden crown or circlet. Background: a magical castle garden with soft sparkles. The outfit suits any child.` |
| `astronaut` | `Character: a young astronaut in a white and blue space suit, with the helmet held under the arm or the visor fully open so the face is clearly visible. Background: stars and a colorful planet.` |
| `explorer` | `Character: an adventure explorer with a safari hat, a backpack and binoculars around the neck. Background: a lush, friendly jungle with an old treasure map.` |
| `wizard` | `Character: a wizard in a starry robe and a pointed hat, holding a glowing magic wand with soft sparkles. Background: a cozy magical library with floating books.` |
| `inventor` | `Character: a futuristic inventor with goggles resting on the forehead and a tool belt. Background: a bright workshop with small friendly robots and glowing blueprints.` |
| `knight` | `Character: a storybook knight in shiny friendly armor, with the helmet held under the arm so the face is visible, and a decorative shield. No weapons. Background: a fairytale castle on a green hill.` |
| `ocean` | `Character: an underwater explorer in a retro-futuristic diving suit, with the helmet visor transparent or open. Background: a colorful coral reef with friendly fish and soft rays of light.` |

### Estructura sugerida en código

```python
COMMON_PROMPT = """..."""  # bloque común de §2

TRANSFORMATIONS = [
    {
        "id": "astronaut",
        "label": "Astronauta",
        "description": "Explora el espacio con tu traje espacial.",
        "default_title": "Capitán Espacial",
        "style_prompt": "Character: ...",
    },
    # ... resto de estilos
]

def build_prompt(style_id: str) -> str:
    style = get_style(style_id)  # lanza error si no existe
    return f"{COMMON_PROMPT}\n{style['style_prompt']}"
```

---

## 4. Rúbrica de evaluación

Evaluar cada estilo con imágenes de prueba **no personales** (ilustraciones con licencia o adultos que dieron su consentimiento; nunca menores). Incluir variedad: tonos de piel, iluminación, gafas, peinados.

| Criterio | Escala | Mínimo aceptable |
|---|---|---|
| Fidelidad del rostro (rasgos, tono de piel, edad aparente) | 1–5 | 3 |
| Estilo reconocible (se entiende el personaje) | 1–5 | 4 |
| Rostro visible y despejado | Sí / No | Sí |
| Apropiado para niños (sin elementos aterradores ni armas) | Sí / No | Sí |
| Sin texto, letras ni marcas en la imagen | Sí / No | Sí |
| Anatomía y artefactos (manos, ojos, deformaciones) | 1–5 | 3 |

Un estilo con un «No» en cualquier criterio de tipo Sí/No **no se da por aprobado**: se ajusta el prompt y se repite.

---

## 5. Registro de iteraciones

| Fecha | Estilo | Cambio en el prompt | Resultado | Decisión |
|---|---|---|---|---|
| | | | | |

---

## 6. Notas

- Si el rostro cambia demasiado, probar: reforzar la frase de identidad, simplificar el fondo, reducir el número de elementos del estilo.
- Si el modelo escribe texto en la imagen, reforzar la última línea del bloque común.
- Los prompts no deben contener nombres de personas, marcas ni personajes con derechos de autor.
