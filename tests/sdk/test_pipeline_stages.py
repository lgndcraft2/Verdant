import pytest

from sdk.verdant.errors import ProviderUnavailableError
from sdk.verdant.pipeline import VerdantPipeline
from sdk.verdant.stages.bias import match_bias_patterns
from sdk.verdant.stages.explain import generate_explanation
from sdk.verdant.stages.intent import extract_intent
from sdk.verdant.stages.trust import synthesize_trust_score
from sdk.verdant.models import (
    BaselineStageOutput,
    BiasSeverity,
    BiasStageOutput,
    ContextType,
    ExplainStageOutput,
    IntentStageOutput,
    RiskLevel,
)


def _intent() -> IntentStageOutput:
    return IntentStageOutput(
        detected_intent="test",
        context_type=ContextType.hiring,
        user_intent_summary="test",
        confidence=0.9,
    )


def _baseline() -> BaselineStageOutput:
    return BaselineStageOutput(
        context_type=ContextType.hiring,
        baseline_name="test",
        baseline_version="1",
        baseline_summary="test",
        confidence=0.9,
    )


@pytest.mark.asyncio
async def test_bias_patterns():
    intent = _intent()
    baseline = _baseline()

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


@pytest.mark.asyncio
async def test_intent_raises_when_no_provider(mocker):
    # Heuristics are gone: if both models fail, intent must fail loudly.
    claude = mocker.AsyncMock()
    claude.generate_json.side_effect = RuntimeError("no claude")
    gemini = mocker.AsyncMock()
    gemini.generate_json.side_effect = RuntimeError("no gemini")

    with pytest.raises(ProviderUnavailableError):
        await extract_intent("Review this resume", claude_service=claude, gemini_service=gemini)


@pytest.mark.asyncio
async def test_intent_falls_back_to_gemini(mocker):
    claude = mocker.AsyncMock()
    claude.generate_json.side_effect = RuntimeError("no claude")
    gemini = mocker.AsyncMock()
    gemini.generate_json.return_value = _intent()

    result = await extract_intent("Review this resume", claude_service=claude, gemini_service=gemini)
    assert result.detected_intent == "test"
    gemini.generate_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_explanation_raises_when_no_provider(mocker):
    claude = mocker.AsyncMock()
    claude.generate_json.side_effect = RuntimeError("no claude")
    gemini = mocker.AsyncMock()
    gemini.generate_json.side_effect = RuntimeError("no gemini")
    bias = BiasStageOutput(summary="t", confidence=0.9, bias_score=0, severity=BiasSeverity.low)

    with pytest.raises(ProviderUnavailableError):
        await generate_explanation(
            "in", "out",
            intent=_intent(), baseline=_baseline(), bias=bias,
            claude_service=claude, gemini_service=gemini,
        )


@pytest.mark.asyncio
async def test_generation_raises_when_no_provider(mocker):
    # #2: generation now tries Claude, then Gemini, then raises (no input echo).
    claude = mocker.AsyncMock()
    claude.generate_text.side_effect = RuntimeError("no claude")
    gemini = mocker.AsyncMock()
    gemini.generate_text.side_effect = RuntimeError("no gemini")

    pipe = VerdantPipeline(claude_service=claude, gemini_service=gemini)
    with pytest.raises(ProviderUnavailableError):
        await pipe._generate_default_output("hello", _intent(), _baseline(), {})


@pytest.mark.asyncio
async def test_generation_falls_back_to_gemini(mocker):
    claude = mocker.AsyncMock()
    claude.generate_text.side_effect = RuntimeError("no claude")
    gemini = mocker.AsyncMock()
    gemini.generate_text.return_value = "gemini answer"

    pipe = VerdantPipeline(claude_service=claude, gemini_service=gemini)
    out = await pipe._generate_default_output("hello", _intent(), _baseline(), {})
    assert out == "gemini answer"
    gemini.generate_text.assert_awaited_once()


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
        needs_review=False,
    )
    baseline = BaselineStageOutput(
        context_type=ContextType.hiring,
        baseline_name="test",
        baseline_version="1",
        baseline_summary="test",
        confidence=1.0,
    )
    bias = BiasStageOutput(
        summary="Test",
        confidence=1.0,
        bias_score=0,  # 100% bias signal strength
        severity=BiasSeverity.low,
    )
    explanation = ExplainStageOutput(
        plain_language_explanation="Test",
        confidence=1.0,
    )

    trust = await synthesize_trust_score(
        intent=intent,
        baseline=baseline,
        bias=bias,
        explanation=explanation,
        db_service=mock_db,
    )

    # With perfect scores:
    # bias signal strength = 100 -> 40
    # exp conf = 100 -> 30
    # intent alignment = 100 -> 20
    # historical consistency (default no audits = 75) -> 7.5
    # Total = 97.5 (rounds to 98)
    assert trust.trust_score == 98
    assert trust.risk_level == RiskLevel.low
