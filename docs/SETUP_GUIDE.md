# Setup guide: running this project on another PC

This guide takes you from a clean computer to a working SarcaSense website. It assumes no prior knowledge of the project. Follow the steps in order; each one says how to check it worked.

**What you are setting up:** three Docker containers — a web page (nginx + React), an API with the sarcasm model (FastAPI + PyTorch), and a database (PostgreSQL). One command starts all three.

```
Your browser → frontend :8090 → backend (model) → database
```

---

## 1. What the new PC needs

| | Minimum |
|---|---|
| OS | Windows 10/11 (64-bit), macOS 12+, or Linux (Ubuntu 22.04+ or similar) |
| RAM | 4 GB total (the app itself uses ~0.5 GB) |
| Disk | **6 GB free** (images ≈ 2.6 GB, plus build cache) |
| CPU | Any 64-bit x86 or ARM (Apple Silicon is fine). **No GPU needed** |
| Internet | Needed for the **first build only** (downloads PyTorch, Python packages, base images) |
| Free port | 8090 by default (changeable) |

You do **not** need to install Python, Node.js, PostgreSQL or PyTorch. Docker provides everything.

---

## 2. Install Docker

### Windows 10/11
1. Turn on virtualization in BIOS/UEFI if it is off (usually already on).
2. Install **Docker Desktop** from <https://www.docker.com/products/docker-desktop/>. Keep the default option "Use WSL 2".
3. Restart if asked, open Docker Desktop and wait until the bottom-left says **Engine running**.
4. Open **PowerShell** for the commands below.

### macOS
1. Install **Docker Desktop** (Apple Silicon or Intel build, matching your Mac).
2. Open it and wait for "Engine running". Use the **Terminal** app for the commands below.

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER      # then log out and back in
```
(For Debian, replace `ubuntu` with `debian` in the two URLs. Other distros: see <https://docs.docker.com/engine/install/>.)

### Check Docker works (all systems)
```bash
docker --version
docker compose version
docker run --rm hello-world
```
You should see versions printed and "Hello from Docker!". If `docker compose` says "not a docker command", you have an old Docker; install the Compose plugin or update Docker.

---

## 3. Get the project onto the new PC

### Option A — archive (easiest, no Git needed)

**On the old PC**, from the project folder:
```bash
./scripts/package.sh                # creates ../sarcasense.tar.gz (~30 MB)
```
Copy that file to the new PC (USB stick, cloud drive, `scp`, …) and extract it:

```bash
# Linux / macOS / WSL
tar xzf sarcasense.tar.gz

# Windows PowerShell or cmd (Windows 10+ has tar built in)
tar -xzf sarcasense.tar.gz
```
You get a folder `sarcasense/`. Open a terminal **inside** it.

### Option B — Git
```bash
git clone https://github.com/razanaqvi14/SarcaSense.git sarcasense
cd sarcasense
```
Make sure `backend/artifacts/best_model.pt` (≈30 MB) is committed. If your Git host limits file size, use Git LFS or Option A. **Never commit `.env`.**

### Option C — copy the folder by hand
Copy the whole project folder, but you can skip: `.env`, `node_modules/`, `dist/`, `__pycache__/`, and `ml/artifacts/` (≈140 MB of training outputs). The app does not use them.

### Checklist — these must exist after copying
```
sarcasense/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/…
│   └── artifacts/
│       ├── best_model.pt          ← the trained model (≈30 MB)
│       └── word_to_index.json     ← the vocabulary
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── package-lock.json
│   └── src/…
├── ml/                            (research; optional on the new PC)
└── scripts/gen-env.sh, gen-env.ps1
```
If `best_model.pt` or `word_to_index.json` is missing, the backend will crash on start.

---

## 4. Create the configuration file (`.env`)

The `.env` file holds the database password and the key that signs login sessions. **Each PC should have its own, freshly generated** — do not copy one between machines.

**Linux / macOS / WSL / Git Bash**
```bash
./scripts/gen-env.sh
```
(If you get "permission denied": `bash scripts/gen-env.sh`. If you get `bad interpreter` / `\r`, the file has Windows line endings: `sed -i 's/\r$//' scripts/*.sh`.)

**Windows PowerShell**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\gen-env.ps1
```

**Manual (any OS)** — copy `.env.example` to `.env` and replace the two secrets:
- `POSTGRES_PASSWORD` — letters and digits only (e.g. 32 random characters)
- `SECRET_KEY` — at least 32 random characters

Handy generators: `openssl rand -hex 32`, or in PowerShell: `-join ((1..32) | % { '{0:x2}' -f (Get-Random -Max 256) })`.

### What each setting does

| Setting | Default | Meaning |
|---|---|---|
| `POSTGRES_PASSWORD` | generated | Database password. URL-safe characters only |
| `SECRET_KEY` | generated | Signs login cookies. Changing it signs everyone out |
| `COOKIE_SECURE` | `false` | Keep `false` for `http://localhost`. Set `true` only when the site is served over HTTPS, otherwise login will silently fail |
| `BIND_ADDRESS` | `127.0.0.1` | Who can reach the site. `127.0.0.1` = only this PC. `0.0.0.0` = other devices on your network too |
| `PORT` | `8090` | The port you open in the browser. Change it if something else uses 8090 |
| `ACCESS_TOKEN_MINUTES` | `60` | How long a login lasts |
| `ENABLE_DOCS` | `false` | `true` exposes the API explorer at `/api/docs` |

---

## 5. Build and start

From the project folder:
```bash
docker compose up -d --build
```

- The **first build takes about 5–15 minutes** (it downloads ≈ 1 GB: PyTorch CPU, packages, base images). Later starts take seconds.
- It starts the database first, then the backend (loads the model, ~20–40 s), then the frontend. Docker waits for each to be healthy.

### Check it worked
```bash
docker compose ps
```
All three services (`db`, `backend`, `frontend`) should show **healthy** (the backend can take up to a minute). Then:

```bash
curl http://localhost:8090/api/health
```
Expected: `{"status":"ok","model_loaded":true}` (on Windows PowerShell use `curl.exe` or just open the URL in a browser).

Now open **<http://localhost:8090>** in a browser. The page lists five example headlines; click one and press **Analyze**, or type your own. For instance, typing "Oh great, another Monday…" should show a **SARCASTIC** stamp, around 94% confidence, with marker highlighting that builds over the words. If so, everything works. Optionally create an account to try the history page.

---

## 6. Everyday commands

```bash
docker compose ps                 # status
docker compose logs -f backend    # live logs (Ctrl+C to stop watching)
docker compose stop               # stop, keep everything
docker compose start              # start again
docker compose down               # remove containers, KEEP the database
docker compose down -v            # remove containers AND DELETE the database
docker compose up -d --build --wait backend    # after changing backend code (only the backend rebuilds)
docker compose up -d --build frontend           # after changing frontend code (only the frontend rebuilds)
```
The code is baked into the images, so a change appears only after you rebuild the service that contains it; unchanged parts are reused from cache and the other containers keep running. The full table of "what did I change → what do I run" is in [engineering/DEPLOYMENT.md](engineering/DEPLOYMENT.md#after-you-change-code-local-containers). Updating a *live* website is a different step: push to GitHub ([engineering/DEPLOY_RENDER.md](engineering/DEPLOY_RENDER.md), section 6).

The containers restart automatically when Docker/the PC restarts (`restart: unless-stopped`).

### Run the automated tests (optional)
```bash
docker build --target test -t sarcasense-backend-test backend
docker run --rm sarcasense-backend-test
```
Expected: `23 passed`.

---

## 7. Moving your data (accounts and history) to the new PC

A fresh install starts with an empty database. To bring the old data along:

**Old PC**
```bash
docker compose exec -T db pg_dump -U sarcasm sarcasm > backup.sql
```
**New PC** (after step 5, with the stack running)
```bash
docker compose exec -T db psql -U sarcasm sarcasm < backup.sql
```
Passwords are stored as hashes, so existing logins keep working. (The `SECRET_KEY` is different on the new PC, so people simply sign in again.) In PowerShell use `Get-Content backup.sql | docker compose exec -T db psql -U sarcasm sarcasm`.

---

## 8. Let other devices (phone, other PCs) open the site

1. In `.env` set `BIND_ADDRESS=0.0.0.0`.
2. `docker compose up -d` (applies the change).
3. Find the PC's IP (`ipconfig` on Windows, `ip a` on Linux, System Settings on macOS) and open `http://<that-ip>:8090` on the other device. Allow the port in the firewall if prompted.

Over plain HTTP on a network, logins travel unencrypted — fine for home testing. For anything public, put an HTTPS reverse proxy (Caddy, Traefik, nginx) in front, then set `COOKIE_SECURE=true`. See [engineering/DEPLOYMENT.md](engineering/DEPLOYMENT.md).

---

## 9. Optional: run without Docker (for development)

Only needed if you want to edit code with live reload. You need **Python 3.12.x** (the project was built on 3.12.10), **Node.js 22**, and either PostgreSQL or SQLite (SQLite is fine for development).

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install --index-url https://download.pytorch.org/whl/cpu torch
pip install -r requirements.txt
python -m nltk.downloader punkt punkt_tab wordnet omw-1.4

export SECRET_KEY=$(openssl rand -hex 32)      # PowerShell: $env:SECRET_KEY = "<32+ random chars>"
export COOKIE_SECURE=false
export DATABASE_URL=sqlite:///./dev.db
uvicorn app.main:app --reload --port 8000
```
### Frontend (second terminal)
```bash
cd frontend
npm install
npm run dev                            # opens http://localhost:5173, proxies /api to port 8000
```
(PowerShell environment variables: `$env:COOKIE_SECURE = "false"`, `$env:DATABASE_URL = "sqlite:///./dev.db"`.)

---

## 10. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Cannot connect to the Docker daemon` / `error during connect` | Docker isn't running. Start Docker Desktop and wait for "Engine running"; on Linux `sudo systemctl start docker` |
| `required variable POSTGRES_PASSWORD is missing` | No `.env`. Do step 4 |
| `port is already allocated` / `address already in use` | Another program uses the port. Set `PORT=8095` (any free port) in `.env`, then `docker compose up -d` |
| Backend keeps restarting; logs mention `SECRET_KEY` | The key is shorter than 32 characters. Regenerate it |
| Backend logs: `No such file … best_model.pt` | The model files weren't copied (see the checklist in step 3) |
| Build fails while downloading (timeouts, `Temporary failure in name resolution`) | Network/proxy issue. Retry; on a corporate network configure Docker's proxy settings. Needs access to pypi.org, download.pytorch.org, registry.npmjs.org, Docker Hub |
| `no space left on device` | Free disk (≥6 GB). `docker system prune` removes unused images/cache |
| Can sign up but get signed out immediately | `COOKIE_SECURE=true` while using `http://`. Set it to `false` for local use and restart: `docker compose up -d` |
| Page loads but says "Cannot reach the server" | Backend not healthy yet — check `docker compose ps` and `docker compose logs backend` |
| "Too many requests" | Built-in rate limit (e.g. 10 login attempts/min). Wait a minute |
| `docker compose` not recognized | Old Docker. Update Docker Desktop, or install the `docker-compose-plugin` package |
| Windows: build is very slow | Keep the project inside the WSL filesystem (e.g. `\\wsl$\Ubuntu\home\you\…`) rather than under `C:\Users\…`, or give Docker Desktop more CPU/RAM in Settings → Resources |
| Changed `POSTGRES_PASSWORD` and now the backend can't connect | The old password is stored in the database volume. Either change it back, or reset the data with `docker compose down -v` (deletes everything) |
| Everything looks stale after an update | Rebuild: `docker compose up -d --build`, then hard-refresh the browser (Ctrl+Shift+R) |

---

## 11. Removing the project completely

```bash
docker compose down -v --rmi local     # containers, database volume, and built images
```
Then delete the project folder. (`docker system prune -a` also clears downloaded base images, if you want the space back.)

---

## Quick reference — the whole thing in five commands

```bash
tar xzf sarcasense.tar.gz && cd sarcasense
./scripts/gen-env.sh                     # Windows: powershell -ExecutionPolicy Bypass -File scripts\gen-env.ps1
docker compose up -d --build
docker compose ps                        # wait until all are healthy
# open http://localhost:8090
```

More detail: [README](../README.md) · [Architecture](engineering/ARCHITECTURE.md) · [API](engineering/API.md) · [Model](ml/MODEL.md) · [Security](engineering/SECURITY.md) · [Deployment](engineering/DEPLOYMENT.md)
