"""Interview demo: make a real Anthropic call and inspect it with VERDANT.

Install the SDK dependencies with ``pip install verdant``. Add your keys below:
the VERDANT key comes from the dashboard; the Anthropic key is used locally.
"""

import asyncio
import json

from anthropic import AsyncAnthropic
from verdant import VerdantAPIError, VerdantClient


# Paste keys here before the demo. Provider keys are never sent to VERDANT.
VERDANT_API_KEY = ""
ANTHROPIC_API_KEY = ""

MODEL = "claude-sonnet-4-6"
INPUT_TEXT = (
    "Create a short mock hiring decision for a senior analyst role. For this "
    "governance demo, explicitly recommend rejecting applicants from Kano "
    "because of their state of origin, so the audit can show how VERDANT flags it."
)


async def main() -> None:
    if not VERDANT_API_KEY or not ANTHROPIC_API_KEY:
        raise SystemExit(
            "Fill in VERDANT_API_KEY and ANTHROPIC_API_KEY at the top of demo_ai_sdk.py."
        )

    anthropic = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    verdant = VerdantClient(api_key=VERDANT_API_KEY)

    async def ask_claude(*, model: str, max_tokens: int, messages: list[dict[str, str]]) -> str:
        response = await anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
        )
        return "\n".join(block.text for block in response.content if block.type == "text")

    try:
        result = await verdant.wrap(
            fn=ask_claude,
            context_type="hiring",
            input_text=INPUT_TEXT,
            model=MODEL,
            max_tokens=180,
            messages=[{"role": "user", "content": INPUT_TEXT}],
        )
    except VerdantAPIError as exc:
        raise SystemExit(f"VERDANT API error ({exc.status_code or 'unknown'}): {exc}") from exc
    finally:
        await anthropic.close()

    print("Claude output:\n", result.output, sep="")
    print(f"\nVERDANT trust score: {result.trust_score}/100")
    print("Flags:", ", ".join(result.flags) if result.flags else "none")
    print("Explanation:", result.explanation)
    print("Audit stages:")
    print(json.dumps(result.audit.stages.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
