# Deployment & operations

> Hosting on Render (including how to update the live site after a change)? See [DEPLOY_RENDER.md](DEPLOY_RENDER.md). This page covers Docker Compose on your own machine or server.

## Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `POSTGRES_PASSWORD` | – (required) | DB password; URL-safe characters only |
| `SECRET_KEY` | – (required) | JWT signing key, ≥32 chars (`openssl rand -hex 32`) |
| `COOKIE_SECURE` | `true` in compose, `false` in generated `.env` | Set `true` whenever served over HTTPS |
| `BIND_ADDRESS` | `127.0.0.1` | Host interface for the published port |
| `PORT` | `8090` | Host port (container is always 8080) |
| `ACCESS_TOKEN_MINUTES` | `60` | Session lifetime |
| `ENABLE_DOCS` | `false` | Serve OpenAPI docs at `/api/docs` |

Rate limits and the text-length cap live in `backend/app/config.py` (env vars `RATE_LIMIT_LOGIN`, `RATE_LIMIT_REGISTER`, `RATE_LIMIT_PREDICT`, `MAX_TEXT_LENGTH` work too if you add them to the compose `environment`).

## Running

```bash
./scripts/gen-env.sh
docker compose up -d --build
docker compose ps            # all three should become healthy
```

### After you change code (local containers)

The code is **baked into the images** (compose mounts only the database volume), so a change shows up only after you rebuild the service that contains it. Rebuilding one service leaves the others, and your database, untouched.

| You changed | Run from the project root | What happens |
|---|---|---|
| `backend/app/**`, `backend/artifacts/**` | `docker compose up -d --build --wait backend` | only the backend image's last layers rebuild; only the backend container restarts |
| `backend/requirements.txt` | same | packages reinstall (slow, minutes); only the backend restarts |
| `frontend/src/**`, `frontend/index.html`, `frontend/nginx.conf` | `docker compose up -d --build frontend` | only the frontend rebuilds and restarts |
| `frontend/package*.json` | same | `npm ci` re-runs, then as above |
| `.env` or `docker-compose.yml` | `docker compose up -d` | no rebuild; recreates only services whose settings changed |
| both backend and frontend | `docker compose up -d --build --wait` | each service rebuilds only its own changed layers |
| `docs/`, `ml/`, `scripts/`, `README.md`, `deploy/`, `render.yaml` | nothing | not part of the local images |

Notes:
- **Why only the changed part rebuilds:** the Dockerfiles put slow, stable steps (PyTorch, packages, NLTK data, `npm ci`, the model file) first and your code last, so Docker reuses everything above the first changed step. Measured: no change ≈ 1 s, one backend file ≈ 11 s, instead of minutes.
- **Use `--wait` for the backend.** After a restart the backend needs a few seconds to load the model; until then the site can answer `502`. `--wait` returns only once it is healthy.
- Your accounts and history survive rebuilds (they live in the `pgdata` volume). Only `docker compose down -v` deletes them.
- **If you clear Docker's cache** (`docker image prune`, `docker system prune`, deleting images), the next rebuild has to redo the slow steps (minutes), and services whose images were rebuilt are recreated, even ones you didn't edit. Nothing is lost; it is just slower once.
- Force a full rebuild only when something seems stale: `docker compose build --no-cache backend`.
- To update the **live website**, see [DEPLOY_RENDER.md](DEPLOY_RENDER.md) section 6: pushing to GitHub is what does that, not rebuilding local containers.

Update the model: see [../ml/MODEL.md](../ml/MODEL.md).

## Production checklist

1. Put a TLS-terminating reverse proxy (Caddy, Traefik, cloud load balancer) in front of the `frontend` container and proxy to it.
2. Set `COOKIE_SECURE=true`; `BIND_ADDRESS=127.0.0.1` if the proxy runs on the same host (leave `0.0.0.0` only if a firewall protects the port).
3. Add `Strict-Transport-Security: max-age=31536000; includeSubDomains` at the proxy.
4. Make sure the proxy **sets** (not appends) `X-Forwarded-For`, or the per-IP rate limit sees the proxy for every user. If it sits in front of this nginx, change nginx's `proxy_set_header X-Forwarded-For $remote_addr` to use the real-IP module (`set_real_ip_from <proxy>; real_ip_header X-Forwarded-For;`).
5. Back up the database (below) and test a restore.
6. Keep `ENABLE_DOCS=false`.

## Backup & restore

```bash
docker compose exec -T db pg_dump -U sarcasm sarcasm | gzip > backup-$(date +%F).sql.gz
gunzip -c backup-2026-01-01.sql.gz | docker compose exec -T db psql -U sarcasm sarcasm
```

Data lives in the `pgdata` volume; `docker compose down -v` deletes it.

## Operations

- Health: `GET /api/health`; Docker health checks gate startup order (db → backend → frontend).
- Logs: `docker compose logs -f backend` (access log + app errors; submitted text is not logged).
- Resource use: the backend uses roughly 400–600 MB RAM (PyTorch + model); limit is 1 GB.
- Scaling: stateless apart from rate-limit counters. To run several backend replicas, point slowapi at Redis (`Limiter(storage_uri="redis://…")`) and add a migration tool (Alembic) for schema changes.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `port is already allocated` | Another service uses the port; change `PORT` in `.env` |
| `variable is not set` on compose | `.env` missing — run `scripts/gen-env.sh` |
| Backend restart loop, `SECRET_KEY` validation error | Key shorter than 32 chars |
| Signed in but immediately signed out on http | `COOKIE_SECURE=true` over plain http — set `false` locally |
| Everyone shares one rate limit / `429` too soon | Proxy not forwarding client IP (checklist item 4) |
| DB auth failure after changing `POSTGRES_PASSWORD` | The password is baked into the existing volume; `ALTER USER` inside Postgres or recreate the volume (`down -v`, loses data) |
