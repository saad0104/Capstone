import React from "react";

const PROVIDERS = [
  { value: "", label: "Default (server-configured)", verified: true },
  { value: "gemini", label: "Gemini", verified: true },
  { value: "grok", label: "Grok", verified: false },
  { value: "ollama", label: "Ollama (local)", verified: false },
  { value: "openrouter", label: "OpenRouter", verified: true },
  { value: "claude", label: "Claude", verified: false },
];

export default function ProviderSelector({ value, onChange, disabled }) {
  return (
    <fieldset className="space-y-2" disabled={disabled}>
      <legend className="text-sm font-medium text-slate-300">LLM provider</legend>
      {PROVIDERS.map((p) => (
        <label key={p.value} className="flex items-center gap-2 text-sm text-slate-200">
          <input
            type="radio"
            name="provider"
            value={p.value}
            checked={value === p.value}
            onChange={() => onChange(p.value)}
            className="accent-severity-medium"
          />
          {p.label}
          {!p.verified && (
            <span
              title="This provider is implemented but has not been live-verified end-to-end."
              className="rounded border border-amber-500/50 bg-amber-500/10 px-1.5 py-0.5 text-xs text-amber-300"
            >
              unverified
            </span>
          )}
        </label>
      ))}
    </fieldset>
  );
}
