# Plain-English description: Dockerfile for containerizing the FastAPI backend application.

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code and helper scripts
COPY backend/ /app/backend/
COPY scripts/ /app/scripts/

# Ensure local video storage directory exists
RUN mkdir -p /app/backend/storage

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

