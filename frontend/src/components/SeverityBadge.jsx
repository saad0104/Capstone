import React from "react";

const SEVERITY_CLASSES = {
  Critical: "bg-severity-critical/20 text-severity-critical border-severity-critical",
  High: "bg-severity-high/20 text-severity-high border-severity-high",
  Medium: "bg-severity-medium/20 text-severity-medium border-severity-medium",
  Low: "bg-severity-low/20 text-severity-low border-severity-low",
};

export default function SeverityBadge({ severity }) {
  const cls = SEVERITY_CLASSES[severity] || "bg-slate-700 text-slate-300 border-slate-600";
  return (
    <span className={`inline-block rounded border px-2 py-0.5 text-xs font-mono ${cls}`}>
      {severity || "Unknown"}
    </span>
  );
}
