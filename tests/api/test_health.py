def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["checks"]["cache"] == "ok"
    assert body["checks"]["db"] == "ok"


def test_health_needs_no_auth(client):
    # No Authorization header — the health check must still return 200.
    resp = client.get("/health", headers={})
    assert resp.status_code == 200


def test_health_reports_dep_error(client):
    # A failing dependency is reported, but the check itself still returns 200.
    async def boom():
        raise RuntimeError("db down")

    client.app.state.db.ping.side_effect = boom
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["checks"]["db"] == "error"
