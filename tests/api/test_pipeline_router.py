import pytest
from unittest.mock import AsyncMock
from sdk.verdant.models import WrapResult, AuditPayload, PipelineStageOutputs, IntentStageOutput, BaselineStageOutput, BiasStageOutput, ExplainStageOutput, TrustStageOutput, ContextType, RiskLevel, BiasSeverity

def test_pipeline_run_success(client, mock_pipeline, mock_db):
    # Setup mock pipeline result
    audit = AuditPayload(
        context_type=ContextType.hiring,
        input_text="Test Input",
        output_text="Test Output",
        stages=PipelineStageOutputs(
            intent=IntentStageOutput(detected_intent="test", context_type=ContextType.hiring, user_intent_summary="test", confidence=1.0),
            baseline=BaselineStageOutput(context_type=ContextType.hiring, baseline_name="test", baseline_version="1", baseline_summary="test", confidence=1.0),
            bias=BiasStageOutput(summary="test", confidence=1.0, bias_score=0),
            explanation=ExplainStageOutput(plain_language_explanation="test", confidence=1.0),
            trust=TrustStageOutput(trust_score=85, risk_level=RiskLevel.low, confidence=1.0)
        ),
        trust_score=85,
        explanation="test"
    )
    result = WrapResult(
        output="Test Output",
        audit=audit,
        trust_score=85,
        explanation="test"
    )
    mock_pipeline.run.return_value = result
    mock_db.insert_audit_log.return_value = {"id": "vd_123"}
    
    response = client.post("/pipeline/run", json={
        "input_text": "Test Input",
        "context_type": "hiring"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["audit_id"] == "vd_123"
    assert data["meta"]["trust_score"] == 85
    
    # DB insert should have been called
    mock_db.insert_audit_log.assert_called_once()


def _make_result(trust=70):
    audit = AuditPayload(
        context_type=ContextType.hiring,
        input_text="Test Input",
        output_text="precomputed text",
        stages=PipelineStageOutputs(
            intent=IntentStageOutput(detected_intent="test", context_type=ContextType.hiring, user_intent_summary="test", confidence=1.0),
            baseline=BaselineStageOutput(context_type=ContextType.hiring, baseline_name="test", baseline_version="1", baseline_summary="test", confidence=1.0),
            bias=BiasStageOutput(summary="test", confidence=1.0, bias_score=0),
            explanation=ExplainStageOutput(plain_language_explanation="test", confidence=1.0),
            trust=TrustStageOutput(trust_score=trust, risk_level=RiskLevel.low, confidence=1.0),
        ),
        trust_score=trust,
        explanation="test",
    )
    return WrapResult(output="precomputed text", audit=audit, trust_score=trust, explanation="test")


def test_pipeline_analyze_success(client, mock_pipeline, mock_db):
    mock_pipeline.run.return_value = _make_result()
    mock_db.insert_audit_log.return_value = {"id": "vd_analyze1"}

    response = client.post("/pipeline/analyze", json={
        "input_text": "Test Input",
        "output_text": "precomputed text",
        "context_type": "hiring",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["audit_id"] == "vd_analyze1"

    # The router must forward the caller's output as precomputed_output.
    _, kwargs = mock_pipeline.run.call_args
    assert kwargs.get("precomputed_output") == "precomputed text"
    mock_db.insert_audit_log.assert_called_once()
