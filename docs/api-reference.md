# API Reference

Base URL: `https://verdant-be.onrender.com`

All responses use a consistent envelope:

```json
{
  "data": { ... },
  "meta": { ... },
  "error": null
}
```

On error, `data` is `null` and `error` contains `{ "message": "...", "type": "..." }`.

---

## Pipeline

### `POST /pipeline/run`

Execute the full 5-stage reasoning pipeline on an input text.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `input_text` | `string` | ✅ | The text to analyze |
| `context_type` | `string` | ✅ | One of: `hiring`, `lending`, `content`, `healthcare` |
| `metadata` | `object` | ❌ | Arbitrary metadata to attach to the audit |

**Example:**

```bash
curl -X POST https://verdant-be.onrender.com/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "Reject this candidate — she is pregnant.",
    "context_type": "hiring"
  }'
```

**Response `meta`:**

| Field | Type | Description |
|---|---|---|
| `audit_id` | `string` | UUID of the stored audit log |
| `trust_score` | `integer` | 0–100 composite trust score |
| `webhook_dispatched` | `boolean` | Whether a low-trust webhook was sent |

**Response `data`:**

Full `WrapResult` object containing:
- `output` — the AI-generated output
- `audit` — full `AuditPayload` with all 5 stage results
- `trust_score` — 0–100
- `flags` — list of matched bias pattern names
- `explanation` — plain-language explanation string

---

## Audits

### `GET /audits`

List audit logs with optional filtering.

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | `integer` | `50` | Max records to return |
| `offset` | `integer` | `0` | Pagination offset |
| `context_type` | `string` | `null` | Filter by context type |

**Example:**

```bash
curl "https://verdant-be.onrender.com/audits?context_type=hiring&limit=10"
```

**Response `data`:**

```json
{
  "items": [ ... ],
  "total": 42
}
```

---

### `GET /audits/{audit_id}`

Fetch a single audit by ID.

**Path Parameters:**

| Param | Type | Description |
|---|---|---|
| `audit_id` | `string` | UUID of the audit |

**Example:**

```bash
curl "https://verdant-be.onrender.com/audits/550e8400-e29b-41d4-a716-446655440000"
```

**Errors:**

| Status | Detail |
|---|---|
| `404` | Audit not found |

---

## Webhooks

### `POST /webhooks/dispatch`

Manually trigger webhook dispatch for an audit.

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `audit_id` | `string` | `null` | UUID of the audit to dispatch |
| `force` | `boolean` | `false` | Bypass trust score threshold check |

**Example:**

```bash
curl -X POST "https://verdant-be.onrender.com/webhooks/dispatch?audit_id=550e8400-...&force=true"
```

**Response `data`:**

```json
{
  "sent": 1,
  "failed": 0,
  "skipped": 0
}
```

**Webhook Payload Format:**

When dispatched, each configured webhook endpoint receives:

```json
{
  "event": "verdant.audit.low_trust",
  "timestamp": "2026-07-07T12:00:00Z",
  "audit": { ... }
}
```

Headers include:
- `X-Verdant-Event` — event type
- `X-Verdant-Timestamp` — ISO timestamp
- `X-Verdant-Audit-Id` — audit UUID
- `X-Verdant-Signature` — HMAC-SHA256 signature (if webhook secret is configured)

---

## Reports

### `GET /reports/ndpr`

Generate an NDPR compliance report.

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `days` | `integer` | `30` | Rolling window in days |

**Example:**

```bash
curl "https://verdant-be.onrender.com/reports/ndpr?days=90"
```

**Response `data`:**

```json
{
  "generated_at": "2026-07-07T12:00:00Z",
  "window_days": 90,
  "total_audits": 150,
  "available_audits": 200,
  "low_trust_decisions": 12,
  "average_trust_score": 74.5,
  "by_context_type": { "hiring": 80, "lending": 70 },
  "flag_counts": { "gender_exclusion": 5, "ethnic_stereotype": 3 },
  "compliance_notes": [
    "Audits are stored with full stage breakdowns for traceability.",
    "Low-trust outputs trigger webhook dispatch according to configured thresholds.",
    "Baselines are versioned and can be updated independently of the SDK."
  ]
}
```

---

## Data Models

### Trust Score Breakdown

The trust score (0–100) is a weighted composite:

| Component | Weight | Description |
|---|---|---|
| Bias signal strength | 40% | `100 - bias_score` |
| Explanation confidence | 30% | AI explanation confidence × 100 |
| Intent alignment | 20% | Average of intent and baseline confidence × 100 |
| Historical consistency | 10% | Consistency with recent audit patterns |

### Bias Severity Levels

| Level | Description |
|---|---|
| `low` | No concerning patterns detected |
| `medium` | Proxy signals or mild pattern matches |
| `high` | Direct bias pattern match (e.g., gender exclusion, ethnic stereotype) |
| `critical` | Accumulated penalty score ≥ 70 |

### Context Types

| Value | Description |
|---|---|
| `hiring` | Candidate screening, recruitment, job decisions |
| `lending` | Credit, loans, financial eligibility |
| `content` | Content moderation, classification |
| `healthcare` | Clinical decisions, triage, medical support |
