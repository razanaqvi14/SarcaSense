import pytest
from fastapi.testclient import TestClient

from app.main import app

CSRF = {"X-Requested-With": "sarcasense"}
PASSWORD = "correct-horse-battery"


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url="http://testserver") as c:
        yield c


def _register(client, email):
    return client.post(
        "/api/auth/register", json={"email": email, "password": PASSWORD}, headers=CSRF
    )


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "model_loaded": True}


def test_liveness_needs_no_database(client):
    r = client.get("/api/live")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_predict_anonymous_not_saved(client):
    r = client.post(
        "/api/predict",
        json={"text": "Oh great, another Monday. Just what I needed."},
        headers=CSRF,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["label"] in {"Sarcastic", "Not Sarcastic"}
    assert 0 <= body["probability"] <= 1
    assert body["id"] is None
    assert body["tokens"] and max(t["attention"] for t in body["tokens"]) == 1.0


def test_predict_long_text_does_not_crash(client):
    text = " ".join(["senator"] * 60)
    r = client.post("/api/predict", json={"text": text}, headers=CSRF)
    assert r.status_code == 200
    assert len(r.json()["tokens"]) == 20
    assert any("first 20" in w for w in r.json()["warnings"])


def test_predict_unanalysable_text(client):
    r = client.post("/api/predict", json={"text": "😊✨"}, headers=CSRF)
    assert r.status_code == 422


def test_predict_validation(client):
    assert client.post("/api/predict", json={"text": "   "}, headers=CSRF).status_code == 422
    assert client.post("/api/predict", json={"text": "a" * 501}, headers=CSRF).status_code == 422


def test_csrf_header_required(client):
    r = client.post("/api/predict", json={"text": "hello there world"})
    assert r.status_code == 403


def test_auth_and_history_flow(client):
    assert _register(client, "Alice@Example.com").status_code == 201
    assert _register(client, "alice@example.com").status_code == 409  # case-insensitive
    assert client.get("/api/auth/me").json()["email"] == "alice@example.com"

    session_cookie = client.cookies.get("access_token")
    assert session_cookie

    r = client.post(
        "/api/predict", json={"text": "area man thrilled to attend meeting"}, headers=CSRF
    )
    pred_id = r.json()["id"]
    assert pred_id is not None

    h = client.get("/api/history").json()
    assert h["total"] == 1 and h["items"][0]["id"] == pred_id
    assert client.get("/api/history/stats").json()["total"] == 1

    # Another user cannot see or delete it.
    client.cookies.clear()
    assert client.get("/api/history").status_code == 401
    _register(client, "bob@example.com")
    assert client.get("/api/history").json()["total"] == 0
    assert client.delete(f"/api/history/{pred_id}", headers=CSRF).status_code == 404

    # Owner can delete.
    client.cookies.clear()
    client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": PASSWORD}, headers=CSRF
    )
    assert client.delete(f"/api/history/{pred_id}", headers=CSRF).status_code == 204
    assert client.get("/api/history").json()["total"] == 0


def test_login_failures_are_generic(client):
    client.cookies.clear()
    bad_pw = client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": "nope-nope-nope"}, headers=CSRF
    )
    no_user = client.post(
        "/api/auth/login", json={"email": "ghost@example.com", "password": "nope-nope-nope"}, headers=CSRF
    )
    assert bad_pw.status_code == no_user.status_code == 401
    assert bad_pw.json() == no_user.json()


def test_weak_password_rejected(client):
    r = client.post(
        "/api/auth/register", json={"email": "c@example.com", "password": "short"}, headers=CSRF
    )
    assert r.status_code == 422


def test_tampered_token_rejected(client):
    client.cookies.clear()
    client.cookies.set("access_token", "not.a.jwt", path="/api")
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.clear()


def test_delete_account(client):
    _register(client, "dave@example.com")
    r = client.post("/api/auth/delete-account", json={"password": "wrong-wrong-wrong"}, headers=CSRF)
    assert r.status_code == 401
    r = client.post("/api/auth/delete-account", json={"password": PASSWORD}, headers=CSRF)
    assert r.status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_matches_notebook_example_output(client):
    r = client.post(
        "/api/predict",
        json={
            "text": "Oh great, another Monday. Just what I needed to recharge from the "
            "exhausting weekend of doing absolutely nothing."
        },
        headers=CSRF,
    )
    body = r.json()
    assert body["label"] == "Sarcastic"
    assert body["important_words"] == ["exhausting", "weekend", "of", "doing", "absolutely"]
