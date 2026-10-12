# ============================================================================
# Aventura IA — imagen de la aplicación
#
# Solo ejecuta el servidor. La cámara vive en el navegador del operador, así que
# el contenedor no necesita acceso a ningún dispositivo ni privilegios extra.
#
# Las credenciales NO van dentro de la imagen: se pasan en tiempo de ejecución
# (ver docker-compose.yml), de modo que la imagen se puede compartir sin filtrar
# ninguna clave.
#
# Guía para quien administra el servidor: docs/DEPLOY.md
# ============================================================================

FROM python:3.13-slim

# Salida sin búfer para que los registros aparezcan en `docker logs` al instante,
# y sin archivos .pyc: el contenedor se ejecuta con el sistema de solo lectura.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Las dependencias primero: mientras no cambien, Docker reutiliza esta capa.
# Pillow y las demás se instalan desde ruedas precompiladas, así que no hacen
# falta compiladores ni paquetes de desarrollo.
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

# Código y recursos, solo lo necesario para ejecutar.
COPY app.py config.py preflight_cloudflare.py preflight_gemini.py ./
COPY api/ ./api/
COPY data/ ./data/
COPY services/ ./services/
COPY templates/ ./templates/
COPY static/ ./static/

# Valores por defecto del contenedor. Se pueden sobrescribir desde docker-compose
# o con `docker run -e`. El proveedor por defecto es la demostración: no gasta
# cuota ni envía fotografías a internet si nadie configura credenciales.
ENV HOST=0.0.0.0 \
    PORT=5000 \
    IMAGE_PROVIDER=mock \
    LOG_LEVEL=INFO

# Usuario sin privilegios: si algo saliera mal, no es root.
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Comprobación de salud contra el propio endpoint de la aplicación.
# Dentro del contenedor, 127.0.0.1 funciona aunque el servidor escuche en 0.0.0.0.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, sys, urllib.request; \
url = 'http://127.0.0.1:' + os.environ.get('PORT', '5000') + '/api/health'; \
sys.exit(0 if urllib.request.urlopen(url, timeout=4).status == 200 else 1)"

# ---------------------------------------------------------------------------
# Un solo worker A PROPÓSITO.
#
# La aplicación limita a UNA generación simultánea con un bloqueo en memoria
# (PLAN.md D-11, error BUSY). Con varios workers cada proceso tendría su propio
# bloqueo, el límite no se respetaría y se gastaría cuota de más.
#
# El tiempo de espera es amplio porque el proveedor puede tardar 15-18 s; la
# propia ruta ya controla su tiempo de espera con REQUEST_TIMEOUT_SECONDS.
# ---------------------------------------------------------------------------
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "1", \
     "--threads", "4", \
     "--timeout", "180", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
