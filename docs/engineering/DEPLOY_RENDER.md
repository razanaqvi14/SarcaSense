# Deploying SarcaSense publicly (Render + Neon)

This guide takes the project from your computer to a public `https://…onrender.com` address anyone can open. It uses:

| Piece | Service | Cost |
|---|---|---|
| Website + API + model (one container) | [Render](https://render.com) web service, from `render.yaml` | free plan available (sleeps when idle) |
| Database | [Neon](https://neon.com) Postgres | free plan available |
| Code hosting | GitHub (your `razanaqvi14` repository) | free |

```
visitor ──HTTPS──▶ Render ──▶ one container: nginx ─┬─ static React app
                                                     └─ /api/* ─▶ FastAPI + PyTorch model ──▶ Neon Postgres
```

**What "tested" means in this guide.** The container image, its memory use, its client-IP handling, and a full browser sign-up/analyze/delete flow were tested locally under Render-like limits (512 MB RAM, `PORT=10000`, real Postgres). **The Render and Neon dashboards themselves were not available to me**, so the dashboard steps follow their documentation; if a screen has moved, follow the intent. Things to confirm on first deploy are marked **[verify]**.

---

## 0. Know the limits of the free plan before you start

| Fact | Source / status |
|---|---|
| Free Render web services **spin down after 15 minutes without traffic** and take about a minute to wake | [Render FAQ](https://render.com/docs/faq) |
| Free plan = **0.1 CPU, 512 MB RAM**. If you omit `plan`, Render uses `0.5c-512mb` (paid) | [Blueprint reference](https://render.com/docs/blueprint-spec) |
| Free **Render Postgres expires after 30 days** (14-day grace before deletion) — that is why this guide uses Neon | [Render docs](https://render.com/docs/your-first-deploy), [free-tier article](https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026) |
| Neon free: roughly 1 GB storage (some pages say 0.5 GB), compute scales to zero after 5 min idle, monthly compute-hour allowance | [Neon plans](https://neon.com/docs/introduction/plans) — check the pricing page for today's numbers |

**What that means for SarcaSense (measured locally with the same CPU/RAM caps):**

- The app fits in 512 MB: **360 MiB at start-up, 367 MiB after a heavy burst** (peak 414 MiB including file cache), no out-of-memory kills.
- **Cold start on 0.1 CPU ≈ 53 s** (loading the model), versus 7.7 s at 0.5 CPU. After that, sign-up/login ≈ 0.3 s and a prediction takes a few milliseconds.
- So on the free plan, **the first visitor after 15 idle minutes waits roughly 1–2 minutes**. Everyone after that is fast. If you demo it live, open the site yourself 5 minutes beforehand. A paid always-on plan avoids this.

---

## 1. Prerequisites

- The code pushed to GitHub (section 2).
- A free **Neon** account and a free **Render** account. Create the Render account with **"Sign in with GitHub"** while your browser is logged into `razanaqvi14`, so Render can see that repository. (This only affects the browser; your local git identity is unchanged.)

## 2. Push the code to GitHub

Follow the push instructions for the `razanaqvi14` account, then confirm on github.com that these exist at the repository root: `render.yaml`, `deploy/Dockerfile`, `backend/`, `frontend/`, and `backend/artifacts/best_model.pt` (≈ 29 MB). Do **not** commit `.env`.

Optional but recommended: test the exact production image on your machine first.

```bash
docker build -f deploy/Dockerfile -t sarcasense-allinone .
```

```bash
docker run --rm -p 8095:10000 -e PORT=10000 -e DATABASE_URL=sqlite:// -e COOKIE_SECURE=false -e SECRET_KEY=$(openssl rand -hex 32) sarcasense-allinone
```

Open <http://localhost:8095>. (SQLite in memory is for this smoke test only — data disappears when you stop it.)

## 3. Create the database (Neon)

1. Sign in at neon.com → **Create project**. Pick the region closest to where you will put Render (Render defaults to Oregon, US West — choose a nearby Neon region such as AWS US West/East).
2. On the project dashboard open **Connect** and copy the **direct (non-pooled)** connection string. It looks like:
   `postgresql://USER:PASSWORD@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`
3. Keep it secret — it is a password. You will paste it into Render once.

You do not need to create tables: the app creates them on first start. The app accepts `postgresql://` and `postgres://` URLs and adds the driver itself (covered by tests).

## 4. Create the service on Render

1. Render dashboard → **New → Blueprint**.
2. Connect GitHub and select your repository (grant Render access to it if asked — for a private repo you must choose it explicitly).
3. Render reads `render.yaml` and shows one web service, `sarcasense`. When it asks for **DATABASE_URL**, paste the Neon string from step 3.
4. Click **Apply**. Render builds the image from `deploy/Dockerfile` and starts it.

**What the Blueprint sets for you:**

| Variable | Value | Why |
|---|---|---|
| `DATABASE_URL` | *you paste it* | Neon connection |
| `SECRET_KEY` | generated by Render (random 256-bit) | signs login cookies |
| `COOKIE_SECURE` | `true` | the site is HTTPS |
| `CLIENT_IP_HEADER` | `cf-connecting-ip` | lets the rate limiter see each visitor's real IP **[verify]** |
| `ARGON2_MEMORY_KIB` / `ARGON2_TIME_COST` / `ARGON2_PARALLELISM` | `19456` / `2` / `1` | lighter password hashing so 512 MB is enough (OWASP's minimum profile) |
| `PORT` | provided by Render | the container listens on it |

The first build downloads PyTorch and builds the frontend: expect **several minutes (plausibly 10–15)**. Watch **Logs**; success looks like `Model loaded and warmed up` followed by the service turning **Live**.

**Prefer clicking through manually?** New → **Web Service** → connect the repo → Language/Runtime **Docker** → Dockerfile path `./deploy/Dockerfile` → add the variables above. Same result.

## 5. Check that it works

Your address is shown at the top of the service page (`https://sarcasense-xxxx.onrender.com`).

1. Open `/api/live` → `{"status":"ok"}`; open `/api/health` → `{"status":"ok","model_loaded":true}` (this one also checks the database).
2. Open the site, analyze the Monday sentence → **Sarcastic ≈ 94 %**.
3. Create an account, analyze something, open **History**, then **Account → delete account** to leave the database clean.
4. **[verify] Real visitor IPs.** In **Logs** find a line like `INFO: 203.0.113.7:0 - "POST /api/predict HTTP/1.0" 200`. The address should be *yours* and should differ between devices. If every line shows the same internal address (10.x / 172.x), Render is not providing the header: **delete the `CLIENT_IP_HEADER` variable**. The site then still works, but the per-IP limits (10 logins/min, 30 analyses/min) become shared by all visitors.

## 6. Updating the live site

Your computer and the live website are **two separate things**. Rebuilding containers on your PC never changes the live site, and pushing to GitHub never changes your local containers. **The live site is updated only by pushing to GitHub**: Render watches your branch (`autoDeployTrigger: commit` in `render.yaml`) and deploys by itself.

### When exactly to do what

| You changed… | Local containers (optional, to test) | Live website |
|---|---|---|
| Backend code `backend/app/**` | `docker compose up -d --build --wait backend` | `git push` → deploys automatically |
| Model files `backend/artifacts/**` | same | `git push` |
| Python packages `backend/requirements.txt` | same (slower: reinstalls) | `git push` (slower) |
| Frontend `frontend/src/**`, `frontend/index.html`, `frontend/package*.json` | `docker compose up -d --build frontend` | `git push` |
| Hosting files `deploy/**`, `.dockerignore` | nothing (local compose doesn't use them) | `git push` |
| Settings in `.env` (local only) | `docker compose up -d` | — (live settings are in Render → **Environment**) |
| Docs `docs/**`, notebook/training `ml/**`, `scripts/**`, `README.md` | nothing | **No deploy.** These are not part of the image, so the build filter skips them |
| `render.yaml` | — | always processed (service settings sync) |

**The routine, in order**

1. Make and save your change.
2. *(Optional, recommended)* Test it locally with the command from the table and open <http://localhost:8090>. For backend changes also run the tests:
   ```bash
   docker build --target test -t sarcasense-backend-test backend && docker run --rm sarcasense-backend-test
   ```
3. Commit and push. The repository's local git identity is already `razanaqvi14` and the remote is already set:
   ```bash
   git add -A
   git commit -m "Describe what you changed"
   git -c credential.helper= push
   ```
   Username `razanaqvi14`, password = a **new** GitHub personal access token (or set up the SSH key alias so no token is needed).
4. **Watch the deploy:** Render dashboard → your service → **Logs**. It starts within seconds of the push. Wait for **Live**.
5. **Check the live site:** open `/api/health`, then try your change. If you still see the old page, hard-refresh (Ctrl+Shift+R).

### Only the changed part is rebuilt

Docker builds the image in cached layers, and the Dockerfiles are ordered so the slow, stable steps come first (PyTorch, packages, NLTK data, `npm ci`, the model file) and the code you edit most comes last. Render keeps these layers between builds ([Render docs: image caching](https://render.com/docs/docker)). Measured on this project (local machine, legacy Docker builder):

| Change | Rebuild time | What actually re-ran |
|---|---|---|
| nothing changed | ~1 s | nothing |
| one backend file | ~11 s | only the final `COPY backend/app` |
| one frontend file | ~4 s | only the frontend build (and its copy, if the output differs) |
| `requirements.txt` | minutes | package install and everything after it |
| first build ever / cache cleared | ~2+ min locally (longer on Render's free CPU) | everything |

Be clear about what this does and does not mean on Render: your site is **one container**, so every deploy replaces the whole container (nginx + API + model together), even for a one-line frontend change. What is incremental is the **build**, not the restart. The restart then includes loading the model (about 53 s on the free plan's 0.1 CPU, 8 s at 0.5 CPU; measured locally). Replacing only the frontend or only the backend independently would need them to be two separate Render services, which costs more and breaks the same-address design (see section 11). The build filter's job is the other half: it stops commits that cannot change the site (docs, notebooks, scripts) from deploying at all.

### Controlling deploys

| Want to… | Do this |
|---|---|
| Push without deploying | put `[skip render]` (or `[render skip]`) in the commit message ([Render docs](https://render.com/docs/deploys)) |
| Deploy even though nothing in the filtered paths changed | Render dashboard → **Manual Deploy → Deploy latest commit** (manual deploys ignore build filters) |
| Rebuild from scratch (stuck or odd build) | Manual Deploy → **Clear build cache & deploy** |
| Know whether a push was skipped | service → **Events** shows skipped deploys |

The `buildFilter` in `render.yaml` uses Render's documented `paths` key. Render's docs do not say outright that build filters apply to Docker services — **[verify]** on your first docs-only push: nothing new should appear under **Events**/**Deploys**. If a deploy starts anyway, the filter is not applied to Docker services and docs commits will simply deploy too (harmless; add `[skip render]` to avoid it).

### Changes that need extra care

| Change | What to do |
|---|---|
| **Database schema** (changing an existing table) | The app only creates *missing* tables at start-up, it never alters existing ones, so such a change **breaks the live site**. Add a migration tool (Alembic) before the first schema change |
| **Environment variables / secrets** | Not in Git. Edit in Render → service → **Environment**; saving redeploys. `render.yaml` changes sync on push, but `sync: false` values (like `DATABASE_URL`) are not asked for again |
| **New model** | Retrain, run `python ml/export_for_serving.py`, commit `backend/artifacts/`, push. Each new 29 MB model stays in Git history forever, so do this deliberately |
| **Free plan** | The service sleeps after 15 idle minutes, so the first visit after a deploy or a quiet period takes ~1–2 minutes |

### If a deploy breaks the site

- A *failed build* normally leaves the previous version running. Read **Logs**, fix the problem, push again.
- To return to a known-good version use the **Rollback** option on an earlier deploy in the service's **Events/Deploys** list **[verify]**, or undo in Git and push:
  ```bash
  git revert HEAD
  git -c credential.helper= push
  ```

## 7. Everyday operations

| Task | How |
|---|---|
| Release an update | `git push` — see section 6 |
| Roll back | Service → **Events/Deploys** → pick an earlier deploy → **Rollback** **[verify]** |
| Change a setting | Service → **Environment** → edit → Render redeploys |
| Read logs | Service → **Logs** |
| Custom domain | Service → **Settings → Custom Domains**, then add the DNS record Render shows; HTTPS certificates are issued automatically **[verify]** |
| Keep it awake | Use a paid always-on plan, or (free) an uptime monitor that requests `/api/live` every ~10 minutes. Check Render's current free-tier hour limits before relying on that |
| Back up the data | `docker run --rm postgres:16-alpine pg_dump "YOUR_NEON_URL" \| gzip > backup-$(date +%F).sql.gz` — run it now and then; also check Neon's own restore options |
| Reset everything | delete the Render service; in Neon delete the project (this destroys user data) |

## 8. Security checklist for a public site

- `SECRET_KEY` and `DATABASE_URL` live only in Render's Environment settings. Never in Git. If either leaks: rotate it (changing `SECRET_KEY` signs everyone out).
- `COOKIE_SECURE=true`, API docs off (`ENABLE_DOCS` unset), HTTPS enforced by Render, HSTS sent by the app when the edge reports HTTPS.
- Open registration has **no email verification or CAPTCHA**; abuse is limited only by rate limits. For a public launch consider adding one.
- Rate-limit counters are in memory: they reset whenever the service restarts or wakes from sleep, and there must stay **one instance**.
- Signed-in users' submitted text is stored. Tell visitors (a short privacy note) — they can delete entries, their history, or the whole account in the app.
- More detail: [SECURITY.md](SECURITY.md).

## 9. Troubleshooting

| Symptom | Likely cause → fix |
|---|---|
| Build fails or runs out of memory/time | Retry; check the build log. The image is large (≈ 2 GB, PyTorch). Free-plan build limits apply — see your Render plan |
| Service restarts with "out of memory" / exit 137 | Memory exceeded 512 MB. Change `plan` to `1c-2g` (more RAM) in `render.yaml` and push |
| `could not connect to server` / SSL errors | Wrong `DATABASE_URL`. Use Neon's **direct** string with `?sslmode=require`; no spaces or quotes |
| `/api/health` fails but `/api/live` works | The database is unreachable or asleep. Retry after a few seconds; check Neon is not paused for exceeding its free allowance |
| Everyone gets "Too many requests" | Real-IP header not working (section 5, step 4) — remove `CLIENT_IP_HEADER` or fix it |
| Signing in does not stick | `COOKIE_SECURE=true` requires HTTPS. Use the `https://` address, not `http://` |
| "Missing CSRF header" | Stale cached page after an update. Hard-refresh (Ctrl+Shift+R) |
| Site very slow the first time | Free plan waking from sleep (≈ 1–2 min). Normal |

## 10. Other hosts (Railway, Fly.io, …)

`deploy/Dockerfile` is host-neutral: one container, listens on `$PORT`, health endpoints `/api/live` and `/api/health`. On another host set the same environment variables (at least `DATABASE_URL`, `SECRET_KEY`, `COOKIE_SECURE=true`). **Leave `CLIENT_IP_HEADER` unset** unless you know your host's edge sets a client-IP header that visitors cannot forge (for example, Fly.io documents a `Fly-Client-IP` header — **[verify]**); otherwise visitors could dodge the rate limiter by inventing addresses. `render.yaml` is Render-specific; Fly needs its own `fly.toml`.

## 11. Why the project is one repository with one container for hosting

Local development uses three containers (`docker-compose.yml`). Hosting platforms bill and route per service, and the login cookie, CSRF header and security policy assume the page and the API share one web address. Serving both from one container behind one address keeps that design intact, needs no CORS or cross-site cookies, and gives a single service to deploy. The code is identical in both modes; only `deploy/` differs.
