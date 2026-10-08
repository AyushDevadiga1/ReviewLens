# Dockerfile — ReviewLens API service
# Targets Python 3.11-slim to keep image size down.
# The frontend runs as a separate service (Dockerfile.frontend).

FROM python:3.11-slim

# Install system dependencies needed by psycopg2-binary and lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy and install Python dependencies first (layer-cached unless requirements.txt changes)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# PyABSA runtime assets (own layers — cached unless requirements change):
# 1. spacy syntax model — AspectExtractor.predict() needs it and its
#    auto-downloader fails inside restricted networks, so bake it in.
# 2. multilingual ABSA checkpoint (~500MB) — baking avoids a slow,
#    restart-loop-prone first-boot download; WORKDIR is /app so the
#    runtime finds checkpoints/ without re-downloading.
RUN python -m spacy download en_core_web_sm
RUN python -c "from pyabsa import AspectTermExtraction as ATEPC; ATEPC.AspectExtractor(checkpoint='multilingual', auto_device=False)"

# Copy project source (.dockerignore keeps checkpoints/ and mlruns/ out)
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default command — override in docker-compose.yml if needed
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
