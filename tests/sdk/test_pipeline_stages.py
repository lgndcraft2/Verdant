import pytest
from sdk.verdant.stages.bias import match_bias_patterns
from sdk.verdant.stages.trust import synthesize_trust_score
from sdk.verdant.stages.intent import _heuristic_intent, _detect_context
from sdk.verdant.models import ContextType, BiasSeverity, IntentStageOutput, BaselineStageOutput, BiasStageOutput, ExplainStageOutput, RiskLevel

@pytest.mark.asyncio
async def test_bias_patterns():
    intent = IntentStageOutput(
        detected_intent="test",
        context_type=ContextType.hiring,
        user_intent_summary="test",
        confidence=0.9
    )
    baseline = BaselineStageOutput(
        context_type=ContextType.hiring,
        baseline_name="test",
        baseline_version="1",
        baseline_summary="test",
        confidence=0.9
    )

    # Test gender exclusion
    bias1 = await match_bias_patterns("Input", "This job is for male only candidates.", intent=intent, baseline=baseline)
    assert "gender_exclusion" in bias1.matched_patterns
    assert bias1.severity in (BiasSeverity.high, BiasSeverity.critical)

    # Test ethnic stereotype
    bias2 = await match_bias_patterns("Input", "He is yoruba so he is very smart", intent=intent, baseline=baseline)
    assert "ethnic_stereotype" in bias2.matched_patterns
    assert bias2.severity in (BiasSeverity.high, BiasSeverity.critical)

    # Test no bias
    bias3 = await match_bias_patterns("Input", "The candidate has 5 years of experience.", intent=intent, baseline=baseline)
    assert len(bias3.flags) == 0
    assert bias3.severity == BiasSeverity.low

def test_heuristic_intent():
    # Lending detection
    result = _heuristic_intent("Can I get a loan?", None)
    assert result.context_type == ContextType.lending
    assert result.detected_intent == "assess_credit_risk"
    
    # Hiring detection
    result2 = _heuristic_intent("Review this resume for the software engineer job", None)
    assert result2.context_type == ContextType.hiring
    assert result2.detected_intent == "screen_candidates"
    assert "review_request" in result2.signals

@pytest.mark.asyncio
async def test_trust_synthesis(mocker):
    # Mock DBService
    mock_db = mocker.AsyncMock()
    mock_db.fetch_recent_audits.return_value = []

    intent = IntentStageOutput(
        detected_intent="test",
        context_type=ContextType.hiring,
        user_intent_summary="test",
        confidence=1.0,
        needs_review=False
    )
    baseline = BaselineStageOutput(
        context_type=ContextType.hiring,
        baseline_name="test",
        baseline_version="1",
        baseline_summary="test",
        confidence=1.0
    )
    bias = BiasStageOutput(
        summary="Test",
        confidence=1.0,
        bias_score=0, # 100% bias signal strength
        severity=BiasSeverity.low
    )
    explanation = ExplainStageOutput(
        plain_language_explanation="Test",
        confidence=1.0
    )

    trust = await synthesize_trust_score(
        intent=intent,
        baseline=baseline,
        bias=bias,
        explanation=explanation,
        db_service=mock_db
    )

    # With perfect scores:
    # bias signal strength = 100 -> 40
    # exp conf = 100 -> 30
    # intent alignment = 100 -> 20
    # historical consistency (default no audits = 75) -> 7.5
    # Total = 97.5 (rounds to 98)
    assert trust.trust_score == 98
    assert trust.risk_level == RiskLevel.low
