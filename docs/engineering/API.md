# API reference

Base path `/api`. JSON in and out. Interactive OpenAPI docs are available at `/api/docs` only when `ENABLE_DOCS=true`.

**Requirements for every `POST`/`PUT`/`PATCH`/`DELETE`:** header `X-Requested-With: sarcasense` (else `403`) and `Content-Type: application/json`.

**Authentication:** a session cookie `access_token` (HttpOnly, set by register/login). Endpoints marked 🔒 return `401` without it.

Errors: `{"detail": "message"}`; validation errors use FastAPI's list form. `429` when rate-limited.

## Auth

| Method & path | Body | Success | Notes |
|---|---|---|---|
| `POST /auth/register` | `{email, password}` (password 10–128 chars) | `201` user, sets cookie | `409` if email exists. Limit 5/min/IP |
| `POST /auth/login` | `{email, password}` | `200` user, sets cookie | `401` generic message for any failure. Limit 10/min/IP |
| `POST /auth/logout` | – | `204` | Clears the cookie |
| `GET /auth/me` 🔒 | – | `200` user | `{id, email, created_at}` |
| `POST /auth/delete-account` 🔒 | `{password}` | `204` | Deletes user and all predictions |

## Prediction

### `POST /predict`
Optional auth. Limit 30/min/IP.

Request: `{"text": "…", "save": true}` — `text` 1–500 chars; `save` only matters when signed in.

Response `200`:
```json
{
  "id": 12,                       // null when not saved
  "label": "Sarcastic",
  "is_sarcastic": true,
  "probability": 0.938,           // P(sarcastic)
  "confidence": 0.938,            // P(predicted class)
  "cleaned_text": "oh great another monday …",
  "tokens": [{"word": "oh", "attention": 0.46}, …],   // first 20 cleaned words; top word = 1.0
  "important_words": ["exhausting", "weekend", …],    // attention ≥ 50% of the top word
  "warnings": []                  // e.g. very short text, truncated, mostly unknown words
}
```
`422` if validation fails or the text has no analysable words after cleaning (e.g. only emoji).

## History 🔒

| Method & path | Result |
|---|---|
| `GET /history?limit=20&offset=0` | `{items: […], total}` newest first; `limit` 1–100 |
| `GET /history/stats` | `{total, sarcastic, not_sarcastic}` |
| `DELETE /history/{id}` | `204`; `404` if it doesn't exist **or belongs to someone else** |
| `DELETE /history` | `204`; deletes all of the caller's entries |

## Meta

`GET /health` → `{"status":"ok","model_loaded":true}`; `500` if the database is unreachable. Used by the container health check.
