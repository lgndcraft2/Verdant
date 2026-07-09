"""
VERDANT SDK — Working Example
==============================

This script demonstrates how VERDANT wraps an AI call and returns
a structured reasoning chain with bias flags, trust score, and
a plain-language explanation.

No API keys required — the pipeline falls back to heuristic analysis
when Claude/Gemini are unavailable.

Usage:
    python examples/demo.py
"""

import asyncio
import sys
import os
import io

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure the project root and sdk are on the path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "sdk"))

from sdk.verdant.client import VerdantClient


# --- Simulated AI functions (stand-ins for real AI calls) ---

async def biased_hiring_ai(prompt: str) -> str:
    """Simulates an AI that produces a biased hiring recommendation."""
    return (
        "Based on the candidate's profile, I recommend rejection. "
        "The candidate speaks pidgin English which is unprofessional "
        "for a corporate role. Additionally, candidates from elite schools "
        "like Oxford tend to perform better in this position."
    )


async def fair_lending_ai(prompt: str) -> str:
    """Simulates an AI that produces a fair lending assessment."""
    return (
        "The applicant demonstrates consistent monthly cashflow of NGN 450,000 "
        "through verified mobile money transactions over 18 months. "
        "Repayment capacity is adequate for the requested NGN 2M loan. "
        "Recommend approval with standard terms."
    )


async def healthcare_triage_ai(prompt: str) -> str:
    """Simulates an AI providing a healthcare triage recommendation."""
    return (
        "The patient presents with persistent headache and fever for 3 days. "
        "Given the symptoms, malaria testing is recommended as first-line "
        "investigation. If negative, consider typhoid panel. "
        "Urgency: moderate — schedule within 24 hours."
    )


# --- Pretty printer ---

def print_result(label: str, result):
    """Print a VERDANT result in a readable format."""
    print(f"\n{'=' * 70}")
    print(f"  {label}")
    print(f"{'=' * 70}")
    print(f"\n  AI Output:\n    {result.output}\n")
    print(f"  Trust Score:  {result.trust_score}/100")
    print(f"  Flags:        {result.flags if result.flags else '(none)'}")
    print(f"  Explanation:  {result.explanation}")

    # Show stage breakdown
    audit = result.audit
    print(f"\n  --- Stage Breakdown ---")
    print(f"  Intent:     {audit.stages.intent.detected_intent} "
          f"(context: {audit.stages.intent.context_type.value}, "
          f"confidence: {audit.stages.intent.confidence:.2f})")
    print(f"  Baseline:   {audit.stages.baseline.baseline_name} "
          f"(v{audit.stages.baseline.baseline_version})")
    print(f"  Bias:       severity={audit.stages.bias.severity.value}, "
          f"score={audit.stages.bias.bias_score}, "
          f"patterns={audit.stages.bias.matched_patterns}")
    print(f"  Trust:      score={audit.stages.trust.trust_score}, "
          f"risk={audit.stages.trust.risk_level.value}")

    if audit.stages.trust.alerts:
        print(f"  Alerts:     {audit.stages.trust.alerts}")
    print()


# --- Main demo ---

async def main():
    client = VerdantClient()

    print("\n" + "=" * 70)
    print("  VERDANT SDK Demo — Inspectable AI Governance")
    print("  Every decision leaves a trace.")
    print("=" * 70)

    # -------------------------------------------------------
    # Example 1: Biased hiring output — should flag bias
    # -------------------------------------------------------
    result1 = await client.wrap(
        biased_hiring_ai,
        context_type="hiring",
        input_text="Evaluate this candidate for the senior analyst role.",
        prompt="Evaluate this candidate for the senior analyst role.",
    )
    print_result("Example 1: Biased Hiring Recommendation", result1)

    # -------------------------------------------------------
    # Example 2: Fair lending output — should pass cleanly
    # -------------------------------------------------------
    result2 = await client.wrap(
        fair_lending_ai,
        context_type="lending",
        input_text="Assess this loan application for NGN 2M.",
        prompt="Assess this loan application for NGN 2M.",
    )
    print_result("Example 2: Fair Lending Assessment", result2)

    # -------------------------------------------------------
    # Example 3: Healthcare triage — should pass cleanly
    # -------------------------------------------------------
    result3 = await client.wrap(
        healthcare_triage_ai,
        context_type="healthcare",
        input_text="Patient has had fever and headache for 3 days.",
        prompt="Patient has had fever and headache for 3 days.",
    )
    print_result("Example 3: Healthcare Triage", result3)

    # -------------------------------------------------------
    # Summary
    # -------------------------------------------------------
    print("=" * 70)
    print("  Summary")
    print("=" * 70)
    print(f"\n  {'Scenario':<45} {'Trust':>6}  {'Flags':>6}")
    print(f"  {'-' * 45} {'-' * 6}  {'-' * 6}")
    for label, r in [
        ("Biased hiring recommendation", result1),
        ("Fair lending assessment", result2),
        ("Healthcare triage", result3),
    ]:
        print(f"  {label:<45} {r.trust_score:>5}/100  {len(r.flags):>5}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
