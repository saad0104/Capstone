import React from "react";

export default function IocChipList({ iocs }) {
  if (!iocs || iocs.length === 0) {
    return <p className="text-sm text-slate-400">No indicators of compromise extracted.</p>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {iocs.map((v) => (
        <span
          key={v}
          className="rounded border border-surface-border bg-surface-raised px-2 py-0.5 font-mono text-xs text-slate-200"
        >
          {v}
        </span>
      ))}
    </div>
  );
}
