from __future__ import annotations

import re
from typing import Iterable

from ..models import BaselineStageOutput, BiasSeverity, BiasStageOutput, ContextType, IntentStageOutput


# Geographic tokens used for regional/state proxy detection in the Nigerian
# context: the 36 states + FCT, the six geopolitical zones, and common
# region/origin descriptors. State-of-origin is a recognised proxy for ethnicity
# and religion in Nigerian hiring/lending, so decisions keyed on it are a bias risk.
_NIGERIAN_REGIONS = (
    r"abia|adamawa|akwa ibom|anambra|bauchi|bayelsa|benue|borno|cross river|delta|"
    r"ebonyi|edo|ekiti|enugu|gombe|imo|jigawa|kaduna|kano|katsina|kebbi|kogi|kwara|"
    r"lagos|nasarawa|niger|ogun|ondo|osun|oyo|plateau|rivers|sokoto|taraba|yobe|zamfara|"
    r"fct|abuja|"
    r"north[\s-]?(?:west|east|central)|south[\s-]?(?:west|east|south)|"
    r"northern|southern|northerner|southerner|northerners|southerners|north|south|"
    r"middle belt|core north|rural|village|state of origin|indigene|indigenes|settler"
)

# Decision/assessment verbs that turn a geographic mention into a discriminatory signal.
_ADVERSE_DECISION = (
    r"reject\w*|denied|deny|declin\w+|disqualif\w+|exclud\w+|avoid|blacklist\w*|"
    r"not (?:hire|shortlist|approv\w+|eligible|suitable|for)|"
    r"high[\s-]?risk|higher risk|risk\w*|lower(?: the)? (?:score|priority|rating)|"
    r"downgrad\w+|unfit|unsuitable|untrustworth\w+|less (?:capable|qualified|reliable)"
)

# An adverse decision within ~50 chars of a region token, in either order.
_REGIONAL_EXCLUSION = re.compile(
    rf"\b(?:{_ADVERSE_DECISION})\b.{{0,50}}\b(?:{_NIGERIAN_REGIONS})\b"
    rf"|\b(?:{_NIGERIAN_REGIONS})\b.{{0,50}}\b(?:{_ADVERSE_DECISION})\b",
    re.I,
)

# Using origin itself as a factor — flagged even without an explicit adverse verb.
_ORIGIN_PROXY = re.compile(
    r"\b(?:state of origin|indigene\w*|indigeneity|hometown|home town|place of birth|"
    r"where (?:are|were) (?:you|they) from|originally from|ancestral|village of origin)\b",
    re.I,
)


_PATTERNS: list[tuple[str, re.Pattern[str], BiasSeverity, int]] = [
    ("regional_exclusion", _REGIONAL_EXCLUSION, BiasSeverity.high, 35),
    ("origin_proxy", _ORIGIN_PROXY, BiasSeverity.medium, 15),
    ("gender_exclusion", re.compile(r"\b(male only|female only|not for women|not for men)\b", re.I), BiasSeverity.high, 35),
    ("ethnic_stereotype", re.compile(r"\b(tribe|ethnic|yoruba|igbo|hausa).{0,40}\b(lazy|unreliable|uneducated|smart|better)\b", re.I), BiasSeverity.high, 35),
    ("accent_bias", re.compile(r"\b(accent|speaks? pidgin|english fluency).{0,40}\b(unfit|unprofessional|less capable)\b", re.I), BiasSeverity.medium, 25),
    ("school_prestige_proxy", re.compile(r"\b(ivy|elite school|top school|prestigious school|oxford|cambridge)\b", re.I), BiasSeverity.medium, 20),
    ("pregnancy_bias", re.compile(r"\b(pregnant|pregnancy|motherhood).{0,40}\b(unfit|risk|disqualify)\b", re.I), BiasSeverity.high, 35),
    ("credit_exclusion", re.compile(r"\b(no credit history|thin file|informal income|cash worker).{0,40}\b(deny|reject|decline)\b", re.I), BiasSeverity.medium, 25),
    ("religious_bias", re.compile(r"\b(christian|muslim|islam|church|mosque).{0,40}\b(unfit|untrustworthy|risk)\b", re.I), BiasSeverity.high, 35),
    ("content_context_collapse", re.compile(r"\b(slang|code-switch|pidgin|dialect).{0,40}\b(remove|ban|unsafe)\b", re.I), BiasSeverity.medium, 20),
    ("protected_attribute_proxy", re.compile(r"\b(age|gender|tribe|religion|marital status|disability)\b", re.I), BiasSeverity.medium, 15),
]


def _highest_severity(current: BiasSeverity, candidate: BiasSeverity) -> BiasSeverity:
    order = {
        BiasSeverity.low: 0,
        BiasSeverity.medium: 1,
        BiasSeverity.high: 2,
        BiasSeverity.critical: 3,
    }
    return candidate if order[candidate] > order[current] else current


async def match_bias_patterns(
    input_text: str,
    output_text: str,
    *,
    intent: IntentStageOutput,
    baseline: BaselineStageOutput,
) -> BiasStageOutput:
    combined_text = f"{input_text}\n{output_text}"
    flags: list[str] = []
    matched_patterns: list[str] = []
    severity = BiasSeverity.low
    penalty = 0

    for name, pattern, level, base_penalty in _PATTERNS:
        if pattern.search(combined_text):
            matched_patterns.append(name)
            severity = _highest_severity(severity, level)
            penalty += base_penalty
            if name == "protected_attribute_proxy" and intent.context_type != baseline.context_type:
                penalty += 10
            flags.append(name.replace("_", " "))

    if intent.needs_review:
        penalty += 10
    if baseline.confidence < 0.75:
        penalty += 5

    if penalty >= 70:
        severity = BiasSeverity.critical
    elif penalty >= 45:
        severity = _highest_severity(severity, BiasSeverity.high)
    elif penalty >= 20:
        severity = _highest_severity(severity, BiasSeverity.medium)

    bias_score = min(100, penalty)
    confidence = min(1.0, 0.55 + (0.1 * len(matched_patterns)))

    summary = (
        "No clear bias pattern matched the output."
        if not flags
        else f"Matched {len(flags)} bias signal(s): {', '.join(flags)}."
    )

    return BiasStageOutput(
        flags=flags,
        matched_patterns=matched_patterns,
        severity=severity,
        bias_score=bias_score,
        summary=summary,
        confidence=confidence,
    )
