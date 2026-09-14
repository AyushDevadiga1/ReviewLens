# Dockerfile — ReviewLens API service
# Targets Python 3.11-slim to keep image size down.
# The frontend runs as a separate service (Dockerfile.frontend).

FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies needed by psycopg2-binary and lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer-cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default command — override in docker-compose.yml if needed
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
