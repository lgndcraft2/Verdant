"use client";

import { FormEvent, useState } from "react";
import { ArrowIcon, CheckIcon } from "./icons";

const useCases = [
  "Hiring",
  "Lending",
  "Content moderation",
  "Healthcare",
] as const;

type FormState = {
  name: string;
  email: string;
  useCase: (typeof useCases)[number];
  company: string;
};

const initialState: FormState = {
  name: "",
  email: "",
  useCase: "Hiring",
  company: "",
};

export function LeadCaptureForm() {
  const [form, setForm] = useState<FormState>(initialState);
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitted(true);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-white/10 bg-white/5 p-5 backdrop-blur-sm"
    >
      <div className="flex items-start gap-3 rounded-lg border border-white/10 bg-white/5 p-4">
        <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-400/20 text-emerald-300">
          <CheckIcon className="h-4 w-4" aria-hidden="true" />
        </span>
        <div>
          <p className="text-sm font-semibold text-white">
            Request a VERDANT demo
          </p>
          <p className="mt-1 text-sm leading-6 text-slate-300">
            Tell us what you are shipping and we will follow up with the right walkthrough.
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4">
        <label className="grid gap-2">
          <span className="text-sm font-medium text-white">Name</span>
          <input
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            required
            autoComplete="name"
            className="min-h-11 rounded-lg border border-white/10 bg-slate-950/40 px-4 py-3 text-sm text-white outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30"
            placeholder="Adaeze Okafor"
          />
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-medium text-white">Work email</span>
          <input
            type="email"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            required
            autoComplete="email"
            className="min-h-11 rounded-lg border border-white/10 bg-slate-950/40 px-4 py-3 text-sm text-white outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30"
            placeholder="you@company.com"
          />
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-medium text-white">Use case</span>
          <select
            value={form.useCase}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                useCase: event.target.value as FormState["useCase"],
              }))
            }
            className="min-h-11 rounded-lg border border-white/10 bg-slate-950/40 px-4 py-3 text-sm text-white outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30"
          >
            {useCases.map((useCase) => (
              <option key={useCase} value={useCase}>
                {useCase}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-medium text-white">Company</span>
          <input
            value={form.company}
            onChange={(event) => setForm((current) => ({ ...current, company: event.target.value }))}
            autoComplete="organization"
            className="min-h-11 rounded-lg border border-white/10 bg-slate-950/40 px-4 py-3 text-sm text-white outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30"
            placeholder="Verdant Labs"
          />
        </label>
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <button
          type="submit"
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-white px-5 py-3 text-sm font-semibold text-slate-950 transition-transform duration-300 hover:-translate-y-0.5"
        >
          Send request
          <ArrowIcon className="h-4 w-4" aria-hidden="true" />
        </button>
        <p className="text-sm leading-6 text-slate-300">
          No spam. We use your details to coordinate a demo and follow-up.
        </p>
      </div>

      {submitted ? (
        <div
          role="status"
          aria-live="polite"
          className="mt-5 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200"
        >
          Thanks. We have your request for {form.useCase.toLowerCase()}.
        </div>
      ) : null}
    </form>
  );
}
