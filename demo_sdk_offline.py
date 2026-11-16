"""Deterministic SDK wrap demo. Run: python demo_sdk_offline.py

Uses VerdantClient.wrap, its HTTP request/response path, and the real five-stage
pipeline. Intent and explanation model responses are fixed stubs; no hosted API,
Neon, or provider credentials are used.
"""

import asyncio
import httpx
from fastapi import FastAPI, Request
import verdant.client as client_module

from verdant import VerdantClient
from verdant.config import Settings
from verdant.models import ContextType, ExplainStageOutput, IntentStageOutput
from verdant.pipeline import VerdantPipeline


class DemoProvider:
    model_name = "demo-stub"

    async def generate_json(self, prompt_name, user_prompt, response_model):
        if response_model is IntentStageOutput:
            return IntentStageOutput(
                detected_intent="assess candidate suitability",
                context_type=ContextType.hiring,
                user_intent_summary="Review a hiring decision",
                confidence=0.95,
            )
        if response_model is ExplainStageOutput:
            biased = "gender_exclusion" in user_prompt
            return ExplainStageOutput(
                plain_language_explanation=(
                    "The decision excludes candidates by gender, which is unrelated "
                    "to role fit and requires human review."
                    if biased else
                    "The decision cites relevant experience and references; no "
                    "demographic exclusion was detected."
                ),
                confidence=0.9,
            )
        raise AssertionError(f"Unexpected model: {response_model}")


class DemoDatabase:
    async def fetch_baseline(self, context_type):
        return None

    async def fetch_recent_audits(self, *args, **kwargs):
        return []


class DemoCache:
    async def get_baseline(self, context_type):
        return None

    async def set_baseline(self, *args, **kwargs):
        pass


def hiring_model(*, decision):
    return decision


async def main():
    provider = DemoProvider()
    pipeline = VerdantPipeline(
        Settings(),
        claude_service=provider,
        gemini_service=provider,
        db_service=DemoDatabase(),
        cache_service=DemoCache(),
    )
    app = FastAPI()

    @app.post("/pipeline/analyze")
    async def analyze(request: Request):
        assert request.headers["authorization"] == "Bearer vd_live_offline_demo"
        payload = await request.json()
        result = await pipeline.run(
            context_type=payload.get("context_type"),
            input_text=payload["input_text"],
            precomputed_output=payload["output_text"],
            metadata=payload["metadata"],
        )
        return {"data": result.model_dump(mode="json"), "meta": {}, "error": None}

    real_async_client = httpx.AsyncClient

    def demo_http_client(*args, **kwargs):
        return real_async_client(*args, transport=httpx.ASGITransport(app=app), **kwargs)

    client_module.httpx.AsyncClient = demo_http_client
    client = VerdantClient(api_key="vd_live_offline_demo", base_url="http://offline.verdant.test")
    scenarios = (
        ("Biased decision", "This analyst role is for male only candidates."),
        ("Evidence-based decision", "The candidate has five years of relevant experience and strong references."),
    )
    try:
        for label, decision in scenarios:
            result = await client.wrap(
                hiring_model,
                context_type="hiring",
                input_text="Should we shortlist this candidate for the analyst role?",
                decision=decision,
            )
            print(f"\n{label}: {result.output}")
            print(f"Trust: {result.trust_score}/100")
            print(f"Flags: {result.flags}")
            print(f"Bias patterns: {result.audit.stages.bias.matched_patterns}")
            print(f"Baseline: {result.audit.stages.baseline.baseline_name}")
            print(f"Explanation: {result.explanation}")
            assert result.output == decision
            assert result.audit.stages.intent.context_type == ContextType.hiring
            assert 0 <= result.trust_score <= 100
    finally:
        client_module.httpx.AsyncClient = real_async_client
    print("\nSDK wrap and all five stages passed.")


if __name__ == "__main__":
    asyncio.run(main())
