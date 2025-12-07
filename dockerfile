# syntax=docker/dockerfile:1.7

############################
# 1) Base & deps layer
############################
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Optional: improve pip reliability & install system deps you might need
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

# Where the app will live
WORKDIR /app

# (Optional) If you use torch/sentence-transformers on CPU:
#   This extra index serves CPU wheels quickly.
ARG PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"
ENV PIP_EXTRA_INDEX_URL=$PIP_EXTRA_INDEX_URL

############################
# 2) Requirements layer
############################
FROM base AS deps

# Copy only dependency files first for better caching
COPY requirements.txt /app/requirements.txt

# If you don't have requirements.txt, you can swap for pyproject.toml/poetry.lock here
RUN pip install --upgrade pip setuptools wheel \
 && pip install  -r /app/requirements.txt

############################
# 3) Runtime image
############################
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    WEB_CONCURRENCY=2 \
    GUNICORN_TIMEOUT=120

# Create non-root user
RUN useradd -m -u 10001 appuser

WORKDIR /app

# Copy installed packages from deps layer (faster, smaller)
COPY --from=deps /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy your code
COPY . /app

# Optional: if you have a prestart script (migrations, warmups)
# RUN chmod +x ./prestart.sh
# ENTRYPOINT ["./prestart.sh"]


# Drop privileges
USER appuser

# Expose the port (informational)
EXPOSE 8000

# Start Gunicorn with Uvicorn workers
# Replace "main:app" with your module:variable if different
CMD exec gunicorn "app.main:app" \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT} \
    --workers ${WEB_CONCURRENCY} \
    --timeout ${GUNICORN_TIMEOUT} \
