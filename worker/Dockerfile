# Plain-English description: Dockerfile for containerizing the Celery background worker.

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend models and worker task code
COPY backend/ /app/backend/
COPY worker/ /app/worker/

# Ensure local video storage directory exists
RUN mkdir -p /app/backend/storage

CMD ["celery", "-A", "worker.celery_app.celery_app", "worker", "--loglevel=info"]

