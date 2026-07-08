import pytest
from pydantic import ValidationError

from sdk.verdant.models import ContextType, BiasStageOutput, TrustStageOutput, BiasSeverity, RiskLevel

def test_context_type_normalize():
    # Enums return themselves
    assert ContextType.normalize(ContextType.hiring) == ContextType.hiring
    
    # None defaults to content
    assert ContextType.normalize(None) == ContextType.content
    
    # Valid strings
    assert ContextType.normalize("hiring") == ContextType.hiring
    assert ContextType.normalize("LENDING") == ContextType.lending
    assert ContextType.normalize("  HealthCare  ") == ContextType.healthcare
    
    # Aliases
    assert ContextType.normalize("content_moderation") == ContextType.content
    assert ContextType.normalize("moderation") == ContextType.content
    
    # Invalid
    with pytest.raises(ValueError, match="Unsupported context type"):
        ContextType.normalize("invalid_context")

def test_bias_score_clamping():
    # Clamps to 0-100
    bias = BiasStageOutput(
        summary="Test",
        confidence=0.5,
        bias_score=150
    )
    assert bias.bias_score == 100

    bias2 = BiasStageOutput(
        summary="Test",
        confidence=0.5,
        bias_score=-10
    )
    assert bias2.bias_score == 0
    
    bias3 = BiasStageOutput(
        summary="Test",
        confidence=0.5,
        bias_score=45
    )
    assert bias3.bias_score == 45

def test_trust_score_clamping():
    trust = TrustStageOutput(
        risk_level=RiskLevel.low,
        confidence=0.9,
        trust_score=105
    )
    assert trust.trust_score == 100

    trust2 = TrustStageOutput(
        risk_level=RiskLevel.low,
        confidence=0.9,
        trust_score=-5
    )
    assert trust2.trust_score == 0

def test_confidence_validation():
    # Confidence must be between 0.0 and 1.0
    with pytest.raises(ValidationError):
        BiasStageOutput(summary="Test", confidence=1.5, bias_score=50)

    with pytest.raises(ValidationError):
        BiasStageOutput(summary="Test", confidence=-0.1, bias_score=50)
