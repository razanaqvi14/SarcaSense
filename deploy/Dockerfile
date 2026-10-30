# syntax=docker/dockerfile:1
# Single-container build of the whole site (nginx + API) for hosts such as Render, Railway or Fly.io.
# Build context = repository root:   docker build -f deploy/Dockerfile .

FROM node:22-alpine AS web
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/index.html frontend/vite.config.js ./
COPY frontend/src ./src
RUN npm run build


FROM python:3.12.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NLTK_DATA=/opt/nltk_data \
    MALLOC_ARENA_MAX=1 \
    MALLOC_TRIM_THRESHOLD_=131072 \
    OMP_NUM_THREADS=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx-light gettext-base \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
RUN python -m nltk.downloader -d "$NLTK_DATA" punkt punkt_tab wordnet omw-1.4

RUN useradd --system --uid 10001 --no-create-home app
COPY backend/app ./app
COPY backend/artifacts ./artifacts
COPY --from=web /app/dist /srv/www
COPY deploy/nginx.conf.template /etc/nginx/nginx.conf.template
COPY deploy/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY deploy/start.sh /srv/start.sh
RUN chmod 755 /srv/start.sh

USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD python -c "import os,sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:%s/api/health' % os.environ.get('PORT','8080'), timeout=4).status==200 else 1)"

CMD ["/srv/start.sh"]
