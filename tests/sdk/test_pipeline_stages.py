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
async def test_regional_bias_detection():
    intent = _intent()
    baseline = _baseline()

    # Explicit state-based exclusion
    b1 = await match_bias_patterns(
        "Loan decision", "Reject all applicants from Kano for this facility.",
        intent=intent, baseline=baseline,
    )
    assert "regional_exclusion" in b1.matched_patterns
    assert b1.severity in (BiasSeverity.high, BiasSeverity.critical)

    # Region-as-risk, reversed word order
    b2 = await match_bias_patterns(
        "q", "Applicants from the Northern states should be treated as high risk.",
        intent=intent, baseline=baseline,
    )
    assert "regional_exclusion" in b2.matched_patterns

    # Using origin itself as a factor -> medium proxy flag
    b3 = await match_bias_patterns(
        "q", "Score candidates partly on their state of origin.",
        intent=intent, baseline=baseline,
    )
    assert "origin_proxy" in b3.matched_patterns

    # Benign geographic mention -> must NOT flag (no adverse decision nearby)
    b4 = await match_bias_patterns(
        "q", "The candidate from Lagos has five years of relevant experience.",
        intent=intent, baseline=baseline,
    )
    assert "regional_exclusion" not in b4.matched_patterns
    assert "origin_proxy" not in b4.matched_patterns


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
    gemini.model_name = "gemini-2.5-flash"

    pipe = VerdantPipeline(claude_service=claude, gemini_service=gemini)
    # #3: generation reports which model actually produced the output.
    out, model = await pipe._generate_default_output("hello", _intent(), _baseline(), {})
    assert out == "gemini answer"
    assert model == "gemini-2.5-flash"
    gemini.generate_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_generation_reports_claude_model(mocker):
    claude = mocker.AsyncMock()
    claude.generate_text.return_value = "claude answer"
    claude.model_name = "claude-sonnet-4-6"
    gemini = mocker.AsyncMock()

    pipe = VerdantPipeline(claude_service=claude, gemini_service=gemini)
    out, model = await pipe._generate_default_output("hello", _intent(), _baseline(), {})
    assert out == "claude answer"
    assert model == "claude-sonnet-4-6"
    gemini.generate_text.assert_not_awaited()


class _FakeLLM:
    """Minimal stand-in for Claude/Gemini services for full-pipeline tests."""

    def __init__(self, *, model_name: str, text: str | None = None, text_raises: bool = False):
        self.model_name = model_name
        self._text = text
        self._text_raises = text_raises

    async def generate_json(self, prompt_name, user_prompt, response_model, *, temperature=0.0):
        if response_model is IntentStageOutput:
            return _intent()
        if response_model is ExplainStageOutput:
            return ExplainStageOutput(plain_language_explanation="e", confidence=0.8)
        raise AssertionError(f"unexpected response_model {response_model!r}")

    async def generate_text(self, prompt_name, user_prompt, *, temperature=0.0):
        if self._text_raises:
            raise RuntimeError("generation unavailable")
        return self._text


def _pipeline_with(mocker, claude, gemini):
    db = mocker.AsyncMock()
    db.fetch_baseline.return_value = None          # -> fallback baseline
    db.fetch_recent_audits.return_value = []       # -> default historical score
    cache = mocker.AsyncMock()
    cache.get_baseline.return_value = None          # -> skip cache
    return VerdantPipeline(claude_service=claude, gemini_service=gemini, db_service=db, cache_service=cache)


@pytest.mark.asyncio
async def test_run_audit_records_actual_generation_model(mocker):
    # Claude analyses the stages but can't generate; Gemini generates the output.
    claude = _FakeLLM(model_name="claude-sonnet-4-6", text_raises=True)
    gemini = _FakeLLM(model_name="gemini-2.5-flash", text="the generated answer")
    pipe = _pipeline_with(mocker, claude, gemini)

    result = await pipe.run(context_type="hiring", input_text="Evaluate this candidate.")

    assert result.output == "the generated answer"
    assert result.audit.model_name == "gemini-2.5-flash"  # not the old hardcoded default


@pytest.mark.asyncio
async def test_run_audit_marks_client_supplied_output(mocker):
    claude = _FakeLLM(model_name="claude-sonnet-4-6")
    gemini = _FakeLLM(model_name="gemini-2.5-flash")
    pipe = _pipeline_with(mocker, claude, gemini)

    result = await pipe.run(
        context_type="hiring",
        input_text="Evaluate this candidate.",
        precomputed_output="a client-produced answer",
    )

    assert result.output == "a client-produced answer"
    assert result.audit.model_name == "client-supplied"


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
