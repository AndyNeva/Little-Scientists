# DEPLOY.md — Poner la aplicación en un servidor

Para quien administra el servidor donde se usará la aplicación en la feria. No
hace falta saber programar: son copiar, pegar y cambiar un `.env`.

---

## 1. Qué necesita el servidor

| Requisito | Detalle |
|---|---|
| Docker | Engine 20.10 o superior, con el plugin `docker compose` (v2). |
| Sistema | Cualquier Linux (probado con la imagen `python:3.13-slim`). |
| Salida a internet | **Solo si se usa un proveedor de IA real.** Con `mock` no hace falta. |
| Navegador con webcam | En el equipo donde se atenderá a los participantes (ver §4). |
| Puerto libre | 5000 por defecto, configurable. |

**La aplicación no guarda nada.** No escribe fotografías en disco, no usa base de
datos y no necesita volumen de datos. Todas las imágenes viven en la memoria del
navegador. Por eso el contenedor se ejecuta con el sistema de archivos de solo
lectura.

---

## 2. Instalación en cuatro pasos

```bash
# 1. Traer el código
git clone <URL-del-repositorio> aventura-ia
cd aventura-ia

# 2. Crear el archivo de configuración
cp .env.example .env
nano .env          # ver §3

# 3. Construir y arrancar
docker compose up -d --build

# 4. Comprobar que responde
curl http://127.0.0.1:5000/api/health
```

Debe devolver algo como:

```json
{"status": "ok", "provider": "cloudflare", "demo_mode": false}
```

Si `status` es `"error"`, el mensaje dice **qué variable falta** (nunca su valor).
Para comprobar las credenciales de verdad, con una llamada real:

```bash
docker compose exec aventura-ia python preflight_cloudflare.py
docker compose exec aventura-ia python preflight_gemini.py
```

---

## 3. Configurar el proveedor de IA

Todo se decide en `.env`. **La persona que usa la aplicación nunca ve este cambio.**

```dotenv
# Modo demostración: no envía fotos a internet y no gasta cuota.
IMAGE_PROVIDER=mock

# Cloudflare Workers AI (el más rápido: 3-5 s por imagen)
IMAGE_PROVIDER=cloudflare
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_MODEL=@cf/black-forest-labs/flux-2-klein-9b

# Gemini (15-18 s por imagen, pero funciona sin plan de pago)
IMAGE_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-nano-banana-2.1
```

> ⚠️ **Cuota.** Antes del evento hay que confirmar cuántas imágenes se podrán
> generar: el plan gratuito de Cloudflare da para unas **6 al día**. La aplicación
> avisa en la terminal cuando se agota la cuota y dice qué alternativas hay
> configuradas.

Después de cambiar `.env`:

```bash
docker compose up -d --force-recreate
```

**Nunca subas el `.env` al repositorio.** Ya está en `.gitignore`.

---

## 4. ⚠️ La cámara y el HTTPS: leer antes de decidir cómo se accede

Esta es la parte que más problemas da, y no depende de Docker.

El navegador **solo permite usar la cámara** (`getUserMedia`) en lo que llama
«contexto seguro». Se cumple en estos dos casos:

| Cómo se abre la aplicación | ¿Funciona la cámara? |
|---|---|
| `http://localhost:5000` **en el mismo equipo** que tiene la webcam | ✅ Sí |
| `https://…` con certificado válido, desde cualquier equipo | ✅ Sí |
| `http://192.168.1.50:5000` (por IP, sin HTTPS) | ❌ **No.** El navegador la bloquea |
| `http://nombre-del-servidor:5000` sin HTTPS | ❌ **No** |

**La aplicación lo detecta** y muestra «Abre la aplicación desde localhost para usar
la cámara» en lugar de fallar en silencio.

### Recomendación

**Opción A (la más simple, y la que menos puede fallar):** ejecutar la aplicación en
**el mismo computador** que tiene la webcam, y abrirla en
`http://localhost:5000`. No hace falta HTTPS ni certificados.

```bash
# En ese computador
docker compose up -d --build
# Y en su navegador: http://localhost:5000
```

**Opción B:** si el servidor está en otra máquina, hay que publicar la aplicación
con **HTTPS**. Con un proxy inverso que gestione el certificado:

```nginx
# /etc/nginx/sites-available/aventura
server {
    listen 443 ssl;
    server_name aventura.midominio.org;

    ssl_certificate     /etc/letsencrypt/live/aventura.midominio.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aventura.midominio.org/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_read_timeout 180s;   # el proveedor puede tardar 15-18 s
    }
}
```

Y en `docker-compose.yml`, mantén el puerto atado a `127.0.0.1` (como viene): el
proxy es quien atiende a la red. **No publiques el puerto a internet sin HTTPS.**

---

## 5. Operación del día

| Tarea | Comando |
|---|---|
| Arrancar | `docker compose up -d` |
| Ver la actividad | `docker compose logs -f` |
| Detener | `docker compose down` |
| Reiniciar tras cambiar `.env` | `docker compose up -d --force-recreate` |
| Estado de salud | `docker compose ps` |
| Cambiar de proveedor | editar `.env` y reiniciar |

El contenedor arranca solo tras un reinicio del servidor (`restart: unless-stopped`).

**Registro de actividad:** los registros de la aplicación registran solo ruta,
estilo, código de resultado y duración. **Nunca** fotografías, nombres, claves ni
cuerpos de solicitud. Aun así, revísalos antes de compartirlos.

---

## 6. Detalles técnicos de la imagen

- **Servidor:** `gunicorn` con **un solo worker** y 4 hilos. Es deliberado: la
  aplicación limita a una generación simultánea con un bloqueo en memoria, y con
  varios workers ese límite no se respetaría y se gastaría cuota de más.
- **Tiempo de espera:** 180 s en gunicorn. El proveedor puede tardar 15–18 s.
- **Usuario:** la aplicación corre como usuario sin privilegios (`appuser`), no root.
- **Sistema de archivos:** de solo lectura, con `/tmp` en memoria.
- **Sin estado:** se puede destruir y recrear el contenedor sin perder nada.
- **Solo HTTP dentro del contenedor:** el HTTPS se resuelve en el proxy (§4).

---

## 7. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| «Abre la aplicación desde localhost» | Se entró por IP o por nombre de red. Usar `http://localhost:5000` en el equipo de la webcam, o publicar con HTTPS (§4). |
| `{"status":"error", ...}` en `/api/health` | Falta una credencial. El mensaje dice cuál. Revisar `.env` y recrear el contenedor. |
| «Algo no está listo todavía» | `IMAGE_PROVIDER` o sus claves están mal en `.env`. |
| «Hay muchas aventuras en preparación» | Cuota agotada o límite de uso. Ver `docker compose logs -f`: la aplicación dice qué alternativas hay configuradas. |
| El puerto 5000 está ocupado | Cambiar la publicación en `docker-compose.yml`, o averiguar qué lo usa con `ss -ltnp \| grep 5000`. |
| Va lento (15–18 s por imagen) | Es el proveedor Gemini. Cloudflare tarda 3–5 s. |
| Tras cambiar `.env` no se aplica | `docker compose up -d --force-recreate` (no basta con `restart`). |

---

## 8. Antes de la feria: lista de comprobación

- [ ] `docker compose up -d --build` termina sin errores.
- [ ] `/api/health` devuelve `"status": "ok"` **con el proveedor elegido**.
- [ ] `preflight_*.py` del proveedor elegido dice «credenciales correctas».
- [ ] La cuota alcanza para las personas previstas (o hay plan de demostración).
- [ ] La cámara funciona **en el equipo y el navegador de la feria** (§4).
- [ ] Se probó el flujo completo de principio a fin con una persona adulta.
- [ ] Se comprobó la descarga del PNG y el botón «Siguiente participante».
- [ ] Los términos de uso de datos del proveedor están revisados y aceptados por el
      responsable (se envían fotografías de menores a un servicio externo).
- [ ] Está resuelta la autorización de los representantes legales y la información
      a las familias sobre el envío de la fotografía a un proveedor externo.
- [ ] Se hizo un ensayo general y se anotaron los tiempos.
