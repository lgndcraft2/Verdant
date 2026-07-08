insert into public.fairness_baselines (
    context_type,
    baseline_name,
    baseline_version,
    demographic_focus,
    baseline_summary,
    policy_notes,
    baseline_data,
    source,
    confidence,
    active
)
values
(
    'hiring',
    'Nigerian Hiring Baseline',
    '2026.07.01',
    '["Yoruba", "Igbo", "Hausa", "minority ethnic groups", "urban-rural parity", "gender balance"]'::jsonb,
    'Use hiring signals that reflect role fit and verified capability, not tribe, accent, religion, or school prestige alone.',
    '["Avoid proxy discrimination through name, origin, or language register.", "Account for regional access to education and work experience.", "Flag overconfident ranking based on informal cues."]'::jsonb,
    '{
        "context": "hiring",
        "risk_focus": ["proxy discrimination", "accent bias", "gendered screening"],
        "recommended_review": ["qualification evidence", "role-specific experience", "local labor market context"]
    }'::jsonb,
    'seed',
    0.900,
    true
),
(
    'lending',
    'Nigerian Lending Baseline',
    '2026.07.01',
    '["financial inclusion", "informal income earners", "SMEs", "rural borrowers", "gender access"]'::jsonb,
    'Use repayment and affordability signals that recognize informal income, uneven banking access, and regional economic disparity.',
    '["Do not treat lack of formal credit history as proof of default risk.", "Prefer cashflow and transaction evidence where available.", "Flag decisions that ignore mobile-money and cooperative savings patterns."]'::jsonb,
    '{
        "context": "lending",
        "risk_focus": ["informal-income exclusion", "thin-file bias", "regional disparity"],
        "recommended_review": ["cashflow evidence", "repayment ability", "alternative credit indicators"]
    }'::jsonb,
    'seed',
    0.900,
    true
),
(
    'content',
    'Nigerian Content Moderation Baseline',
    '2026.07.01',
    '["multilingual code-switching", "political speech nuance", "religious sensitivity", "youth slang", "local dialects"]'::jsonb,
    'Distinguish harm from ordinary Nigerian multilingual expression, satire, and context-dependent references.',
    '["Avoid over-penalizing local slang or code-switching.", "Treat direct threats and hate speech as high risk.", "Consider whether a phrase is quoted, reclaimed, or targeted."]'::jsonb,
    '{
        "context": "content moderation",
        "risk_focus": ["language nuance", "context collapse", "political expression"],
        "recommended_review": ["speaker intent", "targeted harm", "cultural context"]
    }'::jsonb,
    'seed',
    0.850,
    true
),
(
    'healthcare',
    'Nigerian Healthcare Baseline',
    '2026.07.01',
    '["rural access", "maternal health", "language access", "cost sensitivity", "regional care gaps"]'::jsonb,
    'Use clinically relevant signals while accounting for access disparities, language barriers, and the risk of overconfident triage.',
    '["Do not substitute proxy social cues for clinical evidence.", "Surface uncertainty for human review when symptoms are ambiguous.", "Treat safety-critical decisions as high review priority."]'::jsonb,
    '{
        "context": "healthcare",
        "risk_focus": ["access disparity", "triage risk", "language barrier"],
        "recommended_review": ["clinical evidence", "urgency", "need for human escalation"]
    }'::jsonb,
    'seed',
    0.900,
    true
)
on conflict (context_type)
do update set
    baseline_name = excluded.baseline_name,
    baseline_version = excluded.baseline_version,
    demographic_focus = excluded.demographic_focus,
    baseline_summary = excluded.baseline_summary,
    policy_notes = excluded.policy_notes,
    baseline_data = excluded.baseline_data,
    source = excluded.source,
    confidence = excluded.confidence,
    active = excluded.active,
    updated_at = now();
