# Cloud Run — Mortalidad Colombia 2019 (Dash)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt pyarrow

COPY . .

# Preprocesa Excel -> Parquet dentro de la imagen (arranque más rápido)
RUN python scripts/prepare_cache.py

EXPOSE 8080

# Cloud Run inyecta $PORT
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 120 app:server
