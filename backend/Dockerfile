# syntax=docker/dockerfile:1
FROM python:3.12.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NLTK_DATA=/opt/nltk_data \
    MALLOC_ARENA_MAX=1 \
    MALLOC_TRIM_THRESHOLD_=131072 \
    OMP_NUM_THREADS=1

WORKDIR /srv

# CPU-only torch keeps the image ~1 GB smaller than the default CUDA wheel.
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch

COPY requirements.txt .
RUN pip install -r requirements.txt

# Corpora the cleaning pipeline needs (tokenizer + lemmatizer).
RUN python -m nltk.downloader -d "$NLTK_DATA" punkt punkt_tab wordnet omw-1.4

RUN useradd --system --uid 10001 --no-create-home app
COPY app ./app
COPY artifacts ./artifacts
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status==200 else 1)"

# Single worker: rate-limit counters are in-process (see docs/ARCHITECTURE.md).
# nginx is the only client and overwrites X-Forwarded-For, so trusting it is safe.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips=*"]


FROM runtime AS test
USER root
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY tests ./tests
USER app
ENV SECRET_KEY=test-secret-key-test-secret-key-0000 \
    DATABASE_URL=sqlite:// \
    COOKIE_SECURE=false \
    RATE_LIMIT_ENABLED=false
CMD ["pytest", "-q", "-p", "no:cacheprovider"]
