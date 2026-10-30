# Security

## Controls in place

| Area | Control |
|---|---|
| Passwords | Argon2id (argon2-cffi defaults), 10–128 chars; auto-rehash on login if parameters change |
| Sessions | JWT (HS256) with `exp`, `iat`, `jti`; `HttpOnly`, `SameSite=Strict`, `Secure` (when `COOKIE_SECURE=true`), path `/api`; 60-minute lifetime. Algorithm is pinned on verify; `exp`/`sub` required |
| Account enumeration | Login returns one generic error and verifies against a dummy hash for unknown emails (no timing difference) |
| CSRF | `SameSite=Strict` plus required `X-Requested-With` header on all state-changing requests (forces a CORS preflight, and no cross-origin access is allowed) |
| XSS | React escapes output; nginx CSP `default-src 'self'` blocks inline/third-party script; token never accessible to JS |
| Clickjacking / sniffing | `frame-ancestors 'none'`, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer` |
| Authorization | Every history query is scoped to the authenticated user; other users' ids return `404` |
| SQL injection | SQLAlchemy ORM with bound parameters only |
| Input limits | Text ≤ 500 chars, nginx body ≤ 16 KB, password ≤ 128 chars (bounds hashing cost), pagination `limit` ≤ 100 |
| Rate limiting | Per client IP: login 10/min, register 5/min, predict 30/min (configurable in `config.py`). nginx overwrites `X-Forwarded-For` so it can't be spoofed |
| Model loading | `torch.load(weights_only=True)`; vocabulary is JSON, not pickle |
| Secrets | In `.env` (git-ignored, mode 600 from `gen-env.sh`); compose refuses to start if they are missing; app refuses a `SECRET_KEY` under 32 chars |
| Containers | Non-root users, `read_only` root FS, `cap_drop: ALL`, `no-new-privileges`, memory/pid limits; DB on an internal-only network with no published port; API docs off by default |
| Privacy | The app never logs submitted text. Users can delete individual entries, all history, or their account (cascade delete) |

## Known limits / recommended follow-ups

- **No TLS in the stack.** Terminate HTTPS in front (see DEPLOYMENT.md), set `COOKIE_SECURE=true` and add HSTS there.
- **Logout is client-side.** Tokens are stateless, so a stolen token stays valid until expiry (≤60 min). Add a server-side revocation list or short-lived access + refresh tokens if that is unacceptable.
- **No email verification or password reset** (no mail service). Registration is open; anyone can create accounts, limited only by rate limiting.
- **No per-account lockout**, only per-IP throttling. Distributed guessing is mitigated by Argon2 cost and password length, not blocked.
- **Rate limits are in-memory** and reset on restart; they're per process (see ARCHITECTURE.md).
- **Registration reveals whether an email exists** (`409`). Acceptable for this app; avoid if email privacy matters.
- **Rotating `SECRET_KEY`** logs everyone out. Rotating `POSTGRES_PASSWORD` requires also changing it inside the existing database volume.
- Dependencies are version-ranged, not hash-locked. For production, pin and scan (`pip-audit`, `npm audit`, Trivy) in CI.
- Postgres data is not encrypted at rest; use an encrypted volume/disk if required.

## Reporting

Treat any vulnerability report as private; fix, rotate `SECRET_KEY` if sessions may be compromised, and redeploy.
