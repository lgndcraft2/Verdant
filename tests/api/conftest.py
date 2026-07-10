import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from api.auth import verify_api_key
from api.main import app
from sdk.verdant.config import Settings

@pytest.fixture
def mock_settings():
    return Settings(
        verdant_api_key="test_api_key",
        environment="test",
        trust_score_alert_threshold=40,
    )

@pytest.fixture
def mock_db(mocker):
    db = mocker.AsyncMock()
    # Setup default return values
    db.list_audits.return_value = ([], 0)
    db.get_audit.return_value = None
    db.insert_audit_log.return_value = {"id": "vd_test123"}
    db.fetch_webhook_configs.return_value = []
    db.fetch_recent_audits.return_value = []
    return db

@pytest.fixture
def mock_cache(mocker):
    cache = mocker.AsyncMock()
    return cache

@pytest.fixture
def mock_pipeline(mocker):
    pipeline = mocker.AsyncMock()
    # We will let individual tests configure pipeline.run.return_value
    return pipeline

@pytest.fixture
def client(mock_settings, mock_db, mock_cache, mock_pipeline):
    # Bypass VERDANT API-key auth so these tests can exercise handler logic.
    # Only affects the TestClient; production auth is unchanged.
    app.dependency_overrides[verify_api_key] = lambda: {"active": True, "key_prefix": "vd_test"}
    with TestClient(app) as test_client:
        # Override dependencies in app.state AFTER lifespan runs
        app.state.settings = mock_settings
        app.state.db = mock_db
        app.state.cache = mock_cache
        app.state.pipeline = mock_pipeline
        yield test_client
    app.dependency_overrides.clear()
