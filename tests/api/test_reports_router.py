from datetime import datetime, timezone

def test_ndpr_report(client, mock_db):
    now = datetime.now(timezone.utc).isoformat()
    mock_db.list_audits.return_value = (
        [
            {"id": "1", "context_type": "hiring", "trust_score": 85, "flags": [], "created_at": now},
            {"id": "2", "context_type": "lending", "trust_score": 35, "flags": ["geographic_bias"], "created_at": now},
            {"id": "3", "context_type": "hiring", "trust_score": 90, "flags": [], "created_at": now},
        ],
        3
    )
    
    response = client.get("/reports/ndpr?days=30")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    report = data["data"]
    
    assert report["total_audits"] == 3
    assert report["low_trust_decisions"] == 1
    assert report["average_trust_score"] == 70.0
    
    assert report["by_context_type"]["hiring"] == 2
    assert report["by_context_type"]["lending"] == 1
    
    assert report["flag_counts"]["geographic_bias"] == 1
