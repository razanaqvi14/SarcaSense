# SarcaSense

> An attention-based BiLSTM–BiGRU model that flags sarcastic news headlines — and shows which words drove the verdict.

**Live demo:** <https://sarcasense.onrender.com> (free hosting: after 15 idle minutes the first visit can take 1–2 minutes to wake up).  
**Source:** <https://github.com/razanaqvi14/SarcaSense>

A web app that tells you whether a news headline (or any short sentence) is sarcastic, and highlights the words the model paid most attention to. It productionises the model from `sarcasm-detection-using-attention-mechanism-87.ipynb`: a BiLSTM → BiGRU → attention classifier trained on the News Headlines Sarcasm dataset (~87% test accuracy).

| Layer     | Technology                                                       |
| --------- | ---------------------------------------------------------------- |
| Frontend  | React 18 + Vite, served by unprivileged nginx                    |
| Backend   | FastAPI (Python 3.12), PyTorch (CPU), NLTK                       |
| Database  | PostgreSQL 16                                                    |
| Auth      | Argon2id passwords, JWT in an `HttpOnly; SameSite=Strict` cookie |
| Packaging | Docker Compose (3 containers)                                    |

## Quick start

Requires Docker with the Compose plugin.

```bash
./scripts/gen-env.sh        # creates .env with random secrets
docker compose up -d --build
```

Open <http://localhost:8090>. First build downloads PyTorch (CPU) and takes a few minutes.

```bash
docker compose logs -f backend   # watch logs
docker compose down              # stop (data is kept)
docker compose down -v           # stop and DELETE the database
```

## Features

- Analyze text without an account; the verdict, confidence and per-word attention highlighting are shown.
- The home page lists five fixed example headlines (a mix of sarcastic and not sarcastic); click one to try it. They live in `frontend/src/samples.js`; edit that file to change them.
- Sign up to keep a history of analyses, view simple stats, delete entries, or delete your account and all its data.
- Input is cleaned with the exact pipeline used in training (see [docs/ml/MODEL.md](docs/ml/MODEL.md)).

## Project layout

```
ml/                   RESEARCH: notebook, training outputs, export script
  notebooks/          the training/evaluation notebook
  artifacts/          best_model.pt, word2vec.model, pickles (large, git-ignored)
  export_for_serving.py   promotes a trained model into backend/artifacts/
backend/              SERVICE: FastAPI app, tests, Dockerfile
  app/ml/             preprocessing, model definition, predictor (ported from the notebook)
  app/routers/        auth, predict, history endpoints
  artifacts/          best_model.pt + word_to_index.json (loaded at startup)
frontend/             React app, nginx.conf, Dockerfile
docs/                 documentation (index: docs/README.md)
  ml/                 MODEL card + VIVA_GUIDE (AI/ML questions and answers)
  engineering/        ARCHITECTURE, API, SECURITY, DEPLOYMENT
  SETUP_GUIDE.md      install on another PC
deploy/               single-container image + nginx config for hosting platforms (Render, Railway, Fly)
render.yaml           Render Blueprint (one-click service definition)
scripts/              gen-env.sh / gen-env.ps1 (create .env), package.sh (archive for another PC)
docker-compose.yml
```

The notebook and its training outputs live in `ml/` and are not used at runtime — the embedding weights are already inside `best_model.pt`. See [ml/README.md](ml/README.md).

## Changing code

| You changed | Local containers | Live website (if deployed) |
|---|---|---|
| `backend/` | `docker compose up -d --build --wait backend` | `git push` |
| `frontend/` | `docker compose up -d --build frontend` | `git push` |
| `docs/`, `ml/`, `scripts/`, `README.md` | nothing | `git push` (these files are not in the image, but any push redeploys; add `[skip render]` to the commit message to avoid that) |

Only the service you changed is rebuilt, and only its changed layers. Rebuilding local containers does not change the live site; pushing to GitHub does. Details: [local](docs/engineering/DEPLOYMENT.md#after-you-change-code-local-containers) and [live](docs/engineering/DEPLOY_RENDER.md).

## Tests

```bash
docker build --target test -t sarcasense-backend-test backend && docker run --rm sarcasense-backend-test
```

Runs 23 tests covering text cleaning, the prediction endpoint, auth, per-user data isolation, CSRF protection and validation.

## Local development (without Docker for the frontend)

```bash
docker compose up -d db backend      # backend is only on the internal network by default
cd frontend && npm install && npm run dev
```

The Vite dev server proxies `/api` to `localhost:8000`; to reach the backend from the host, temporarily add `ports: ["127.0.0.1:8000:8000"]` to the `backend` service (and set `COOKIE_SECURE=false`).

## Documentation

- **[Setup guide](docs/SETUP_GUIDE.md) — step-by-step install on another PC (Windows, macOS, Linux)**
- [Architecture](docs/engineering/ARCHITECTURE.md) — components, request flow, data model, design decisions
- [API reference](docs/engineering/API.md)
- [Model card](docs/ml/MODEL.md) — what was trained, how inference works, limitations
- [Security](docs/engineering/SECURITY.md) — controls in place and known limits
- **[Deploy publicly on Render + Neon](docs/engineering/DEPLOY_RENDER.md) — start-to-end guide, including how to push updates to the live site**
- [Deployment & operations](docs/engineering/DEPLOYMENT.md) — configuration, HTTPS, backups, scaling

## Limitations

The model was trained on ~28k headlines (The Onion vs. HuffPost). It reflects the style of that source: it is good at "Onion-style" headlines and noticeably weaker on casual conversational sarcasm, very short text, or out-of-vocabulary words. The UI warns in those cases. Do not use it for decisions that affect people.
