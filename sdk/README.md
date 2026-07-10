# VERDANT SDK

VERDANT is a lightweight SDK for making AI outputs inspectable. It wraps an AI call and returns the clean model output together with a structured audit payload, bias flags, a plain-language explanation, and a 0-100 trust score.

The SDK is built for Nigerian and African teams shipping AI into higher-stakes contexts such as hiring, lending, content moderation, and healthcare.

## Install

```bash
pip install verdant
```

## Usage

```python
from verdant import VerdantClient

client = VerdantClient(api_key="vd_live_...")

result = await client.wrap(
    fn=openai.chat.completions.create,
    model="gpt-4o",
    messages=[{"role": "user", "content": user_input}],
)

print(result.output)
print(result.trust_score)
print(result.flags)
print(result.explanation)
```

## Project

Source code, documentation, and issue tracking live at:

https://github.com/lgndcraft2/Verdant
