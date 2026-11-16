from api.auth import check_password, hash_password


def test_password_hash_checks_password():
    stored = hash_password("a sufficiently long password")
    assert "a sufficiently long password" not in stored
    assert check_password("a sufficiently long password", stored)
    assert not check_password("wrong password", stored)


def test_key_creation_requires_session(client):
    assert client.post("/keys", json={}).status_code == 401


def test_login_issues_custom_jwt(client, mock_db):
    mock_db.get_user_by_email.return_value = {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "tester@example.com",
        "full_name": "Tester",
        "role": "member",
        "password_hash": hash_password("a sufficiently long password"),
    }
    client.app.state.settings.jwt_secret = "test-secret-at-least-thirty-two-characters"
    response = client.post("/auth/login", json={
        "email": "tester@example.com", "password": "a sufficiently long password"
    })
    assert response.status_code == 200
    assert response.json()["data"]["access_token"]


def test_provider_keys_require_admin(client, mock_db):
    from api.auth import verify_session
    from api.main import app
    app.dependency_overrides[verify_session] = lambda: {
        "user_id": "00000000-0000-0000-0000-000000000001", "role": "member"
    }
    try:
        response = client.post("/providers/keys", json={"provider": "anthropic", "api_key": "test"})
        assert response.status_code == 403
        mock_db.set_provider_key.assert_not_called()
    finally:
        app.dependency_overrides.pop(verify_session, None)
