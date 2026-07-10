import pytest
from fastapi.testclient import TestClient

from api.auth import verify_supabase_jwt
from api.main import app
from sdk.verdant.config import Settings
from sdk.verdant.services.db_service import DBService

FAKE_USER = {"user_id": "user-123", "email": "tester@example.com"}


@pytest.fixture
def db():
    # Settings() with no supabase config -> DBService uses its in-memory store.
    return DBService(Settings())


@pytest.fixture
def client(db):
    app.dependency_overrides[verify_supabase_jwt] = lambda: FAKE_USER
    with TestClient(app) as test_client:
        # Override app.state AFTER lifespan runs (which builds its own services).
        app.state.db = db
        app.state.settings = Settings(environment="test", trust_score_alert_threshold=40)
        yield test_client
    app.dependency_overrides.clear()


def _create_key(client) -> str:
    response = client.post("/keys", json={})
    assert response.status_code == 200
    raw = response.json()["data"]["raw_key"]
    assert raw.startswith("vd_live_")
    return raw


def test_create_returns_raw_once(client):
    response = client.post("/keys", json={"label": "CI key"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["raw_key"].startswith("vd_live_")
    assert data["key_prefix"] == data["raw_key"][:12]
    assert data["label"] == "CI key"


def test_list_never_exposes_secret(client):
    _create_key(client)
    response = client.get("/keys")
    assert response.status_code == 200
    keys = response.json()["data"]
    assert len(keys) == 1
    assert "hashed_key" not in keys[0]
    assert "raw_key" not in keys[0]
    assert keys[0]["key_prefix"].startswith("vd_live_")


def test_issued_key_authenticates_api(client):
    raw = _create_key(client)
    # A valid key passes the verify_api_key gate on a protected route.
    ok = client.get("/audits", headers={"Authorization": f"Bearer {raw}"})
    assert ok.status_code == 200
    # A bogus key is rejected.
    bad = client.get("/audits", headers={"Authorization": "Bearer vd_live_deadbeef"})
    assert bad.status_code == 401


def test_regenerate_revokes_old_key(client):
    old = _create_key(client)
    regen = client.post("/keys/regenerate", json={})
    assert regen.status_code == 200
    new = regen.json()["data"]["raw_key"]
    assert new != old

    # Old key is now deactivated (403), new key works (200).
    old_resp = client.get("/audits", headers={"Authorization": f"Bearer {old}"})
    assert old_resp.status_code == 403
    new_resp = client.get("/audits", headers={"Authorization": f"Bearer {new}"})
    assert new_resp.status_code == 200

    # Only the new key remains active.
    active = client.get("/keys").json()["data"]
    assert len(active) == 1
    assert active[0]["key_prefix"] == new[:12]


def test_keys_require_session():
    # No dependency override here -> the endpoint must reject an anonymous caller.
    with TestClient(app) as anon:
        response = anon.get("/keys")
    assert response.status_code == 401
