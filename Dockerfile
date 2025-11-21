FROM python:3.11-slim

# Environment optimizations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# expose port
EXPOSE 8000

# Production server command (dev uses runserver)
CMD ["gunicorn", "pkv_backend.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--worker-class", "gthread", \
     "--threads", "4"]
