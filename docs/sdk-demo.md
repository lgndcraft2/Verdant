# SDK demo run sheet

From the repository root:

```powershell
python demo_sdk_offline.py
```

Expected result: the gender-exclusive hiring decision is flagged and scores
39/100; the evidence-based decision has no flags and scores 88/100.
The script asserts that `VerdantClient.wrap()` preserves the caller's output,
sends the analysis request, parses the response, and returns all five stage
outputs. It takes a few seconds and needs no network or API key.

Say explicitly that the intent and explanation model responses are deterministic
stubs. Bias matching, baseline selection, trust synthesis, the SDK wrapper, and
the HTTP request/response path are real application code. The in-process API
does not persist an audit to Neon.

For a live hosted demo, deploy the migrated backend with `DATABASE_URL` and
`JWT_SECRET`, register a dashboard account, promote the provider-key admin,
configure an Anthropic or Gemini key, and issue a VERDANT API key. Then run
`demo_verdant.py` with `VERDANT_KEY` set. Do not describe the live path as
ready until those steps and a successful `/pipeline/analyze` call are verified.
