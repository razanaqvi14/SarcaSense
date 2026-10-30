# Architecture

```
Browser ──HTTP──▶ frontend (nginx :8080) ──/api/*──▶ backend (uvicorn :8000) ──▶ db (postgres :5432)
                    │ static React build              │ FastAPI + PyTorch model
                    └ only published port             └ model loaded once at startup
```

Networks: `edge` (frontend ↔ backend) and `data` (backend ↔ db, `internal: true` — no outside access). Only nginx publishes a port, bound to `127.0.0.1` by default. Postgres and the API are unreachable from the host.

## Components

**Frontend** (`frontend/`). Single-page React app. Routes: `/` analyze, `/login`, `/register`, `/history`, `/account` (last two require sign-in). All calls go through `src/api.js`, which sends the CSRF header and same-origin cookies. nginx serves the static build, proxies `/api/`, and sets security headers (CSP etc.).

**Backend** (`backend/app/`).

| Module | Role |
|---|---|
| `main.py` | App factory, lifespan (create tables, load model), CSRF + header middleware, `/api/health` |
| `config.py` | Settings from environment variables (`SECRET_KEY` required, ≥32 chars) |
| `security.py` | Argon2id hashing, JWT create/verify |
| `deps.py` | `get_optional_user` / `get_current_user` from the cookie |
| `ratelimit.py` | slowapi limiter keyed by client IP |
| `routers/auth.py` | register, login, logout, me, delete-account |
| `routers/predict.py` | `POST /api/predict` |
| `routers/history.py` | list, stats, delete one/all |
| `ml/preprocess.py` | text cleaning ported from the notebook |
| `ml/model.py` | network definition |
| `ml/predictor.py` | loads artifacts, runs inference, derives important words |

**Database.** Tables are created at startup with `Base.metadata.create_all`.

```
users(id PK, email UNIQUE idx, password_hash, is_active, created_at)
predictions(id PK, user_id FK→users ON DELETE CASCADE idx, text, cleaned_text,
            is_sarcastic, probability, tokens JSON, important_words JSON, created_at idx)
```

## Prediction flow

1. Browser `POST /api/predict {text}` (header `X-Requested-With: sarcasense`).
2. nginx forwards, overwriting `X-Forwarded-For` with the real client address.
3. Rate limit check → CSRF header check → body validation (1–500 chars).
4. `clean_text` → first 20 tokens → vocabulary lookup (`<UNK>`=1) → left-pad with 0.
5. Model returns a logit and attention weights; `sigmoid(logit) > 0.5` ⇒ sarcastic.
6. Attention for real tokens is rescaled so the top word is 1.0; words ≥ 0.5 are "important".
7. If a user is signed in (and `save` is true) the result is stored; the response is returned.

## Hosting variant

On platform-as-a-service hosts the same code runs as one container (`deploy/Dockerfile`): nginx serves the React build and proxies `/api/` to uvicorn on localhost, listening on the platform's `$PORT`. Memory is kept small by warming the model at start-up and tuning the allocator (`MALLOC_ARENA_MAX=1`), and password hashing concurrency is capped (`ARGON2_MAX_CONCURRENT`, default 2). See [DEPLOY_RENDER.md](DEPLOY_RENDER.md).

## Design decisions

- **Ship only what inference needs.** `best_model.pt` already contains the frozen embedding matrix, so Word2Vec, gensim and the 55 MB `embedding_matrix.pkl` stay out of the image. The vocabulary was converted from pickle to JSON, so no pickle is loaded at runtime, and `torch.load(weights_only=True)` is used.
- **Model dimensions are read from the checkpoint** (vocab size, hidden size), so a retrained checkpoint drops in without code changes as long as the architecture is unchanged.
- **CPU-only PyTorch.** Inference on 20 tokens is milliseconds; the CPU wheel avoids ~2 GB of CUDA libraries.
- **Anonymous use allowed.** Analysis is the core feature; accounts only add history. Anonymous requests are never stored.
- **Cookie auth, same origin.** nginx serves UI and API from one origin, so no CORS is configured at all, and the JWT is never readable by JavaScript.
- **Single backend worker.** Rate-limit counters are in process memory. For multiple workers/replicas, give slowapi a Redis `storage_uri`.
- **No migrations tool yet.** `create_all` only creates missing tables; it will not alter existing ones. Introduce Alembic before the first schema change in production.
