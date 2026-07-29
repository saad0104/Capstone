import React, { useState } from "react";
import { Link } from "react-router-dom";
import { analyze } from "../api/client";
import { useAlerts } from "../context/AlertsContext";
import ProviderSelector from "../components/ProviderSelector";
import ErrorPanel from "../components/ErrorPanel";
import LoadingSpinner from "../components/LoadingSpinner";
import SeverityBadge from "../components/SeverityBadge";
import IocChipList from "../components/IocChipList";

export default function AnalyzePage() {
  const { dispatch } = useAlerts();
  const [text, setText] = useState("");
  const [provider, setProvider] = useState("");
  const [submitStatus, setSubmitStatus] = useState("idle"); // idle | submitting | success | error
  const [result, setResult] = useState(null);
  const [submitError, setSubmitError] = useState(null);

  const isBlank = text.trim() === "";

  async function handleSubmit(e) {
    e.preventDefault();
    if (isBlank || submitStatus === "submitting") return;

    setSubmitStatus("submitting");
    setSubmitError(null);
    try {
      const alert = await analyze({ text, provider });
      dispatch({ type: "ADD_ALERT", alert });
      setResult(alert);
      setSubmitStatus("success");
    } catch (err) {
      setSubmitError(err);
      setSubmitStatus("error");
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-xl font-semibold text-slate-100">Analyze a threat report</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={submitStatus === "submitting"}
          rows={8}
          placeholder="Paste raw threat report text here..."
          className="w-full rounded border border-surface-border bg-surface-raised p-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-slate-400 focus:outline-none"
        />

        <ProviderSelector value={provider} onChange={setProvider} disabled={submitStatus === "submitting"} />

        <button
          type="submit"
          disabled={isBlank || submitStatus === "submitting"}
          className="rounded bg-severity-medium/90 px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Analyze
        </button>

        {submitStatus === "submitting" && <LoadingSpinner label="Analyzing..." />}
      </form>

      {submitStatus === "error" && (
        <ErrorPanel error={submitError} providerHint={provider === "grok" || provider === "ollama"} />
      )}

      {submitStatus === "success" && result && (
        <div className="space-y-3 rounded border border-surface-border bg-surface-raised p-4">
          <div className="flex items-center justify-between">
            <SeverityBadge severity={result.severity} />
            <Link to={`/alerts/${result.id}`} className="text-sm text-slate-400 hover:text-slate-200">
              View in Alerts list &rarr;
            </Link>
          </div>
          <p className="font-mono text-xs uppercase tracking-wide text-slate-400">{result.threat_type}</p>
          <p className="text-sm text-slate-100">{result.summary}</p>
          <div>
            <p className="mb-1 text-xs text-slate-400">Indicators of compromise</p>
            <IocChipList iocs={result.ioc_list} />
          </div>
          <p className="text-sm text-slate-300">
            <span className="text-slate-400">Recommended action: </span>
            {result.recommended_action}
          </p>
          <p className="text-xs text-slate-500">
            Processed in {result.processing_ms}ms &middot;{" "}
            {result.created_at ? new Date(result.created_at).toLocaleString() : ""}
          </p>
        </div>
      )}
    </div>
  );
}
