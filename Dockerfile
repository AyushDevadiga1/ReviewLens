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

# HuggingFace hub's xet transfer backend hangs in this environment
# (both at build and at runtime) — force the classic HTTP path.
ENV HF_HUB_DISABLE_XET=1

# spacy syntax model — AspectExtractor.predict() needs it and its
# auto-downloader fails inside restricted networks, so bake it in (small).
RUN python -m spacy download en_core_web_sm

# The multilingual ABSA checkpoint (~810MB) is deliberately NOT baked here:
# its download goes through the xet path above and, when baked, is lost on
# every container recreate — each start re-downloaded 810MB before serving.
# Instead ./checkpoints is bind-mounted by docker-compose.yml: fetched once
# (PyABSA downloads it on first boot if the host dir is empty) and reused.

# The GPU/CPU-embedding backbone that a cold boot otherwise fetches
# (~1.1GB). Prefetched through transformers itself so the weights land
# in the HF hub cache (~/.cache/huggingface) — exactly where the runtime
# loader looks. (A raw curl to /app would be dead weight: no loader reads
# arbitrary paths.) With HF_HUB_DISABLE_XET=1 above this uses plain HTTP.
RUN python -c "
from transformers import AutoModel, AutoTokenizer
AutoTokenizer.from_pretrained('microsoft/mdeberta-v3-base')
AutoModel.from_pretrained('microsoft/mdeberta-v3-base')
print('backbone prefetched into hub cache', flush=True)
"

# Copy project source (.dockerignore keeps checkpoints/ and mlruns/ out)
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default command — override in docker-compose.yml if needed
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
