# VERDANT API image.
# Build context MUST be the repo root: the API imports the SDK by path
# (`from sdk.verdant...`), so both api/ and sdk/ have to be present.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Install dependencies first for better layer caching. requirements.txt pins
# `-e ./sdk`, so the SDK source must be present before pip runs.
COPY requirements.txt ./
COPY sdk/ ./sdk/
RUN pip install --upgrade pip && pip install -r requirements.txt

# App code
COPY api/ ./api/

# Repo root on the path so both `api` and `sdk` are importable.
ENV PYTHONPATH=/app

EXPOSE 8000

# Honour the platform-provided $PORT (Render/Railway/Fly set this); default 8000.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
