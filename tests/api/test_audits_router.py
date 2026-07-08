def test_list_audits_success(client, mock_db):
    mock_db.list_audits.return_value = (
        [{"id": "vd_1", "context_type": "hiring"}, {"id": "vd_2", "context_type": "hiring"}],
        2
    )
    
    response = client.get("/audits?context_type=hiring&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["context_type"] == "hiring"
    assert data["data"]["total"] == 2
    assert len(data["data"]["items"]) == 2

def test_list_audits_invalid_context(client):
    response = client.get("/audits?context_type=invalid")
    assert response.status_code == 400
    assert "Unsupported context type" in response.json()["error"]["message"]

def test_get_audit_success(client, mock_db):
    mock_db.get_audit.return_value = {"id": "vd_123", "trust_score": 85}
    
    response = client.get("/audits/vd_123")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == "vd_123"

def test_get_audit_not_found(client, mock_db):
    mock_db.get_audit.return_value = None
    
    response = client.get("/audits/vd_404")
    assert response.status_code == 404
