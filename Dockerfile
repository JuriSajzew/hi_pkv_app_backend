FROM python:3.11-slim

# Python-Optimierungen für Docker
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off

WORKDIR /app

# Getrennte Schritte für besseres Layer-Caching
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y gcc && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY . .

# Statische Dateien getrennt sammeln
RUN python manage.py collectstatic --noinput

EXPOSE 8000

RUN pip install python-decouple


# Gunicorn mit optimierten Einstellungen
CMD ["gunicorn", "pkv_backend.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--workers", "2", \
     "--worker-class", "gthread", \
     "--threads", "4", \
     "--log-level", "debug"]