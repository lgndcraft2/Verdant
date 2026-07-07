"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ArrowIcon, CheckIcon, PulseIcon, ShieldIcon, TraceIcon } from "./icons";

type Segment = {
  id: string;
  label: string;
  trustScore: number;
  title: string;
  description: string;
  signals: string[];
  flag: string;
  action: string;
};

const segments: Segment[] = [
  {
    id: "hiring",
    label: "Hiring",
    trustScore: 84,
    title: "Filter out proxy bias before a shortlist ships.",
    description:
      "Spot job-posting drift, skill proxy language, and explanation gaps before a decision reaches recruiters or candidates.",
    signals: ["Proxy bias language", "Qualification drift", "Regional imbalance"],
    flag: "Needs human review",
    action: "Open audit trail",
  },
  {
    id: "lending",
    label: "Lending",
    trustScore: 79,
    title: "Catch approval patterns that quietly exclude whole groups.",
    description:
      "Compare the model output against Nigerian fairness baselines to surface class, geography, and access bias early.",
    signals: ["Geographic bias", "Income proxying", "Low explanation confidence"],
    flag: "Webhook alert armed",
    action: "Inspect bias flags",
  },
  {
    id: "content",
    label: "Content",
    trustScore: 91,
    title: "Keep moderation decisions explainable and consistent.",
    description:
      "Track why an item was flagged, what pattern matched, and whether the output overreached on tone or identity.",
    signals: ["Stereotype amplification", "Over-moderation risk", "Tone ambiguity"],
    flag: "Safe to publish",
    action: "Review rationale",
  },
  {
    id: "healthcare",
    label: "Healthcare",
    trustScore: 73,
    title: "Surface safety-critical uncertainty before it becomes advice.",
    description:
      "A low-confidence explanation matters more in healthcare than a polished answer. VERDANT makes that visible.",
    signals: ["Safety ambiguity", "Low confidence", "Escalation needed"],
    flag: "Escalate to expert",
    action: "See trace output",
  },
];

export function AudienceSwitcher() {
  const [activeId, setActiveId] = useState(segments[0].id);
  const active = useMemo(
    () => segments.find((segment) => segment.id === activeId) ?? segments[0],
    [activeId],
  );

  return (
    <section
      aria-label="VERDANT use-case preview"
      className="relative overflow-hidden rounded-lg border border-emerald-950/10 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-white/5 sm:p-6"
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-500/60 to-transparent" />
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700 dark:text-emerald-300">
            Live decision lens
          </p>
          <h2 className="mt-2 font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Switch the lens by use case.
          </h2>
        </div>
        <div className="hidden items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300 sm:flex">
          <CheckIcon className="h-4 w-4" />
          Structured JSON only
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {segments.map((segment) => {
          const selected = segment.id === activeId;

          return (
            <button
              key={segment.id}
              type="button"
              onClick={() => setActiveId(segment.id)}
              aria-pressed={selected}
              className={[
                "min-h-11 rounded-lg border px-4 py-2 text-sm font-semibold transition-all duration-300",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-900",
                selected
                  ? "border-emerald-700 bg-emerald-700 text-white shadow-sm"
                  : "border-emerald-950/10 bg-white text-slate-700 hover:border-emerald-500 hover:text-emerald-800 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:border-emerald-500 dark:hover:text-white",
              ].join(" ")}
            >
              {segment.label}
            </button>
          );
        })}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-lg border border-emerald-950/10 bg-slate-50 p-5 dark:border-white/10 dark:bg-white/5">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-11 w-11 items-center justify-center rounded-lg bg-emerald-700 text-white shadow-sm">
              <ShieldIcon className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-700 dark:text-emerald-300">
                {active.label} review
              </p>
              <h3 className="mt-1 font-display text-xl font-semibold tracking-tight text-slate-950 dark:text-white">
                {active.title}
              </h3>
            </div>
          </div>

          <p className="mt-4 max-w-prose text-sm leading-7 text-slate-600 dark:text-slate-300">
            {active.description}
          </p>

          <ul className="mt-5 space-y-3">
            {active.signals.map((signal) => (
              <li key={signal} className="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-200">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white text-emerald-700 shadow-sm ring-1 ring-emerald-950/10 dark:bg-white/5 dark:text-emerald-300 dark:ring-white/10">
                  <TraceIcon className="h-4 w-4" aria-hidden="true" />
                </span>
                {signal}
              </li>
            ))}
          </ul>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="#developers"
              className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-emerald-700 px-5 py-3 text-sm font-semibold text-white transition-transform duration-300 hover:-translate-y-0.5 hover:bg-emerald-800 dark:bg-emerald-500 dark:text-slate-950 dark:hover:bg-emerald-400"
            >
              {active.action}
              <ArrowIcon className="h-4 w-4" aria-hidden="true" />
            </Link>
            <Link
              href="#how-it-works"
              className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-emerald-950/10 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition-colors duration-300 hover:border-emerald-500 hover:text-emerald-800 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:border-emerald-500 dark:hover:text-white"
            >
              Read the audit
            </Link>
          </div>
        </div>

        <div className="flex flex-col gap-4 rounded-lg border border-emerald-950/10 bg-gradient-to-br from-emerald-800 to-rose-800 p-5 text-white shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/80">
                Trust score
              </p>
              <div className="mt-2 flex items-end gap-3">
                <span className="font-display text-5xl font-semibold leading-none">
                  {active.trustScore}
                </span>
                <span className="pb-1 text-sm font-medium text-white/80">/ 100</span>
              </div>
            </div>

            <div className="rounded-lg bg-white/10 px-4 py-3 backdrop-blur-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/80">
                Status
              </p>
              <p className="mt-1 text-sm font-semibold">{active.flag}</p>
            </div>
          </div>

          <div className="rounded-lg bg-white/10 p-4 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-sm font-semibold text-white/90">
              <PulseIcon className="h-4 w-4" aria-hidden="true" />
              Reasoning chain snapshot
            </div>
            <div className="mt-4 space-y-3">
              {[
                ["1", "Intent", "Detected the user goal and context type."],
                ["2", "Baseline", "Matched a Nigerian fairness baseline."],
                ["3", "Bias", "Checked for high-risk patterns and proxies."],
                ["4", "Explain", "Generated a plain-language rationale."],
                ["5", "Trust", "Synthesized score, risk, and alerts."],
              ].map(([step, label, detail]) => (
                <div key={label} className="flex items-start gap-3 rounded-lg bg-white/10 px-3 py-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-xs font-bold text-emerald-800">
                    {step}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-white">{label}</p>
                    <p className="text-sm text-white/75">{detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg bg-slate-950/20 p-4 backdrop-blur-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/70">
                Alert rule
              </p>
              <p className="mt-2 text-sm font-medium text-white">
                Scores below 40 trigger webhook alerts by default.
              </p>
            </div>
            <div className="rounded-lg bg-slate-950/20 p-4 backdrop-blur-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/70">
                Output
              </p>
              <p className="mt-2 text-sm font-medium text-white">
                Clean response for users, full audit payload for teams.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
