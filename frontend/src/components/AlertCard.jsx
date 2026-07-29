import React from "react";
import { Link } from "react-router-dom";
import SeverityBadge from "./SeverityBadge";

export default function AlertCard({ alert }) {
  const summary = alert.summary || "";
  const truncated = summary.length > 140 ? `${summary.slice(0, 140)}...` : summary;
  const created = alert.created_at ? new Date(alert.created_at).toLocaleString() : "";
  const iocCount = (alert.ioc_list || []).length;

  return (
    <Link
      to={`/alerts/${alert.id}`}
      className="block rounded border border-surface-border bg-surface-raised p-4 hover:border-slate-500"
    >
      <div className="flex items-center justify-between gap-2">
        <SeverityBadge severity={alert.severity} />
        <span className="text-xs text-slate-400">{created}</span>
      </div>
      <p className="mt-2 font-mono text-xs uppercase tracking-wide text-slate-400">
        {alert.threat_type || "unknown"}
      </p>
      <p className="mt-1 text-sm text-slate-200">{truncated}</p>
      <p className="mt-2 text-xs text-slate-500">
        {iocCount} IoC{iocCount === 1 ? "" : "s"}
      </p>
    </Link>
  );
}
