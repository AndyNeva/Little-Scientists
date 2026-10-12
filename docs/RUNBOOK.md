# RUNBOOK.md — Guía del operador

Para quien atiende la actividad en la feria (profesor o estudiante). No requiere programar. Se completa y se revisa al final de la Fase 9.

**Contacto técnico:** ____ · **Responsable de la feria:** ____

---

## 1. Antes del evento

- [ ] Computador cargado y con la webcam conectada.
- [ ] Internet disponible (necesario para el proveedor real).
- [ ] Navegador y permiso de cámara ya probados.
- [ ] Archivo `.env` configurado en el computador (nunca se comparte ni se sube al repositorio).
- [ ] `IMAGE_PROVIDER` en el valor deseado (`cloudflare` o `mock`).
- [ ] Ensayo general hecho (`docs/TEST_PLAN.md` §5).
- [ ] Autorización de los representantes legales resuelta (§7).
- [ ] Carpeta de descargas del navegador identificada (§6).

---

## 2. Arrancar la aplicación

1. Abrir una terminal en la carpeta del proyecto.
2. Activar el entorno virtual (ver `README.md`).
3. Ejecutar: `python app.py`
4. Abrir en el navegador: `http://localhost:5000` (o el puerto configurado en `PORT`).
5. Comprobar `http://localhost:5000/api/health`: debe mostrar `"status": "ok"`.
6. Dejar la ventana de la terminal abierta durante todo el evento.

Si el puerto 5000 está ocupado, cambiar `PORT` en `.env` y volver a arrancar.

### ⚠️ Comprobar que solo hay UN servidor arrancado

En Windows, Werkzeug enlaza el puerto con `SO_REUSEADDR`, así que **dos servidores
pueden escuchar a la vez en el mismo puerto**. Si se arranca uno nuevo sin haber
cerrado el anterior, las peticiones se reparten entre los dos y aparecen
comportamientos imposibles: una pantalla con el diseño viejo, o un proveedor
distinto del que dice `.env`.

Antes de arrancar (o si algo «no cuadra»), comprobar:

```powershell
netstat -ano | Select-String ':5000.*LISTENING'
```

Debe aparecer **una sola línea**. Si hay varias, cerrar los sobrantes:

```powershell
Stop-Process -Id <PID> -Force     # uno por cada PID que aparezca
taskkill /PID <PID> /F            # si el anterior diera «Acceso denegado»
```

Y una señal igual de útil: si al recargar la página **no aparece ninguna línea
`GET /` en la terminal del servidor**, estás hablando con otro proceso.

### Cambiar de proveedor de IA

La aplicación puede generar las imágenes con dos servicios distintos. **Se cambia
una sola línea de `.env` y se reinicia; en la pantalla no se nota nada.**

1. Detener la aplicación (`Ctrl + C`).
2. En `.env`, cambiar `IMAGE_PROVIDER` a uno de estos valores:

   | Valor | Qué usa |
   |---|---|
   | `cloudflare` | Cloudflare Workers AI |
   | `gemini` | Gemini |
   | `mock` | Modo demostración (no envía fotos a internet) |

3. Arrancar de nuevo (§2).
4. **Antes de atender público**, comprobar las credenciales del proveedor elegido:

   ```powershell
   python preflight_cloudflare.py    # si se usa Cloudflare
   python preflight_gemini.py        # si se usa Gemini
   ```

   Debe terminar con «credenciales correctas». Si falla, dice qué revisar y **nunca
   muestra la clave**, así que su salida se puede compartir.

El proveedor activo se ve en la terminal al arrancar y en `GET /api/health`; **nunca
en la pantalla del participante**. La única señal visible es «Modo demostración»,
que aparece cuando `IMAGE_PROVIDER=mock`.

---

## 3. Atender a un participante

1. En la pantalla de bienvenida, pulsar **Empezar aventura**.
2. Si el navegador pide permiso de cámara, pulsar **Permitir**.
3. El niño o niña se coloca frente a la cámara, con el rostro despejado.
4. Pulsar **Tomar foto**. Si no sale bien, **Repetir**.
5. Pulsar **Continuar** y elegir un personaje.
6. Si quiere, escribir su nombre (opcional).
7. Pulsar **Transformarme** y esperar.
8. Mostrar el resultado. Para llevarlo: **Descargar imagen**. Para probar otro: **Probar otro personaje**.
9. Al terminar, pulsar **Siguiente participante**. Esto apaga la cámara y borra la foto de la pantalla.

**No pasar al siguiente niño sin pulsar «Siguiente participante».**

---

## 4. Si algo falla

| Síntoma | Qué hacer |
|---|---|
| La cámara no aparece | Revisar el cable. Permitir la cámara en el navegador (icono junto a la dirección) y recargar. Cerrar otras aplicaciones que usen la cámara. |
| «Abre la aplicación desde localhost» | Entrar por `http://localhost:5000`, no por otra dirección. |
| La página no carga | Revisar que la terminal siga ejecutando `python app.py`; si se cerró, arrancar de nuevo (§2). |
| Mensaje de «muchas aventuras en preparación» | Esperar un minuto y reintentar. Si se repite, pasar al modo demostración (§5). |
| Tarda demasiado o falla varias veces | Revisar internet. Si no se resuelve, modo demostración (§5). |
| Mensaje de «Algo no está listo todavía» | Revisar `.env` y `IMAGE_PROVIDER`; avisar al contacto técnico. |
| La descarga no funciona | Probar otro intento; revisar los permisos de descarga del navegador. |

---

## 5. Modo demostración

Se usa cuando el proveedor de IA falla o se agota la cuota. **No genera la imagen real del niño o niña:** muestra una imagen ilustrativa de ejemplo con el título. Hay que decirlo al participante con claridad.

**Activar**
1. Detener la aplicación en la terminal (`Ctrl + C`).
2. En `.env`, poner `IMAGE_PROVIDER=mock`.
3. Arrancar de nuevo (§2).
4. Verificar que aparece «Modo demostración» en la pantalla de bienvenida.

**Volver al proveedor real**
1. Detener la aplicación.
2. En `.env`, poner `IMAGE_PROVIDER=cloudflare` (o el proveedor vigente).
3. Arrancar de nuevo y completar una prueba antes de atender público.

### ⚠️ Cuota: leer antes del evento

Los proveedores reales se pagan por uso. **Hay que decidir de antemano cuántas
imágenes reales se van a hacer**, porque el plan gratuito no da para una feria.

| Proveedor | Plan gratuito | Coste por imagen | Velocidad medida |
|---|---|---|---|
| Cloudflare | 10.000 neuronas al día → **≈6 imágenes** | ≈$0,017 en plan de pago | **3–5 s** |
| Gemini | **Genera imágenes sin plan de pago** (límite por confirmar) | ⏳ por confirmar en el panel de Google | 15–18 s |

**Mensaje textual de Cloudflare al agotarse** (comprobado el 11/10/2026 a las 23:30 UTC):

```text
429  you have used up your daily free allocation of 10,000 neurons,
     please upgrade to Cloudflare's Workers Paid plan if you would like to continue usage.
```

No es un fallo de la aplicación: es la cuota de la cuenta. La aplicación lo traduce
al mensaje amable de `docs/UI_COPY.md` y sigue funcionando.

Cloudflare es cuatro veces más rápido, así que es la opción recomendada para la
feria — pero **con plan de pago**. Con el plan gratuito solo alcanza para unas 6
imágenes al día, así que en una demostración se agota en minutos (ya ocurrió dos
veces durante las pruebas). Gemini aguanta más, a cambio de 15 s por imagen.

Antes del evento, comprobar:

- [ ] ¿La cuenta del proveedor elegido tiene plan de pago o créditos suficientes?
- [ ] ¿Cuántas imágenes se prevén? (personas esperadas × intentos por persona)
- [ ] Si no hay plan de pago: decidir cuántas transformaciones reales se harán y
      pasar a modo demostración al agotarlas, **diciéndolo con claridad**.
- [ ] Repasar las condiciones de uso de datos del proveedor elegido, sobre todo si
      se van a enviar fotografías de menores (`PROVIDER_VALIDATION.md`).

Cuando se agota la cuota, la aplicación muestra «Hay muchas aventuras en
preparación. Espera un momento y vuelve a intentarlo» y sigue funcionando: no se
cae. Si el mensaje se repite, cambiar al otro proveedor o al modo demostración (§2).

**La terminal te dice qué hacer.** Al agotarse la cuota, el registro avisa de las
alternativas que ya tienes configuradas y, si el proveedor es Cloudflare, recuerda
que su cuota gratuita se reinicia a las **00:00 UTC**. Ejemplo real:

```text
WARNING fallo de proveedor category=generacion type=ProviderRateLimit
        detail=Cloudflare indica límite de uso o cuota agotada.
WARNING Cuota agotada con el proveedor «cloudflare». Alternativas ya configuradas:
        gemini, mock (modo demostración). Se cambia con IMAGE_PROVIDER en .env y reiniciando.
WARNING Nota: la cuota gratuita de Cloudflare son 10.000 neuronas al día
        (unas 6 imágenes) y se reinicia a las 00:00 UTC.
```

El consumo se consulta en el panel del proveedor: **Workers AI** en Cloudflare, y
el panel de **Google AI Studio** para Gemini.

---

## 6. Fin de la jornada

- [ ] Detener la aplicación (`Ctrl + C`).
- [ ] Borrar las imágenes descargadas de la carpeta de descargas del navegador, según lo acordado con el responsable de la feria.
- [ ] Vaciar la papelera si corresponde.
- [ ] Cerrar el navegador.
- [ ] Verificar que no quedan fotografías en la carpeta del proyecto.
- [ ] Guardar el `.env` en un lugar seguro o eliminarlo del equipo compartido.

**Plazo acordado para eliminar las descargas:** ____ *(lo decide el responsable de la feria)*

---

## 7. Privacidad y autorización

Los participantes son menores de edad. La aplicación no guarda fotografías, pero **la imagen se envía a un proveedor externo de IA** cuando se usa el modo real (no en modo demostración).

Antes de tomar fotografías reales, el responsable de la feria debe resolver y documentar:

- [ ] Autorización de los representantes legales para tomar y procesar la fotografía.
- [ ] Información clara a las familias de que la imagen se envía a un proveedor externo para procesarla.
- [ ] Qué hace el proveedor con las imágenes (conservación, uso para entrenamiento) según sus condiciones vigentes (`docs/PROVIDER_VALIDATION.md`).
- [ ] Quién conserva las imágenes descargadas, dónde y hasta cuándo.
- [ ] Qué pasa si una familia no autoriza (alternativa para ese niño o niña, por ejemplo, ver el modo demostración).

Si no hay autorización adecuada o no se puede verificar el tratamiento de datos, **usar el modo demostración o imágenes de prueba no personales**.

> El texto de autorización lo redacta o aprueba el responsable de la feria o la institución; este documento solo lista los puntos que debe cubrir.

---

## 8. Reglas para el operador

- No usar fotografías de los participantes para otro fin.
- No compartir, subir ni conservar las imágenes fuera de lo acordado.
- No compartir el archivo `.env` ni mostrar la terminal con claves en pantalla.
- Ante cualquier duda sobre privacidad, detener la actividad y consultar al responsable.
