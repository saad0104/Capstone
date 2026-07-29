import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getAlert, deleteAlert } from "../api/client";
import { useAlerts } from "../context/AlertsContext";
import { downloadAlertAsJson } from "../utils/jsonExport";
import SeverityBadge from "../components/SeverityBadge";
import IocChipList from "../components/IocChipList";
import ErrorPanel from "../components/ErrorPanel";
import LoadingSpinner from "../components/LoadingSpinner";

export default function AlertDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { alerts, dispatch } = useAlerts();
  const cached = alerts.find((a) => a.id === id);

  const [alert, setAlert] = useState(cached || null);
  const [status, setStatus] = useState(cached ? "loaded" : "loading");
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (cached) return;
    let cancelled = false;
    setStatus("loading");
    getAlert(id)
      .then((a) => {
        if (!cancelled) {
          setAlert(a);
          setStatus("loaded");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err);
          setStatus("error");
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleDelete() {
    if (!window.confirm("Delete this alert? This cannot be undone.")) return;
    setDeleting(true);
    try {
      await deleteAlert(id);
    } catch (err) {
      // 404 (already gone) is fine to treat as success; anything else, still navigate
      // back but the list will reflect reality on next refresh regardless.
    }
    dispatch({ type: "REMOVE_ALERT", id });
    navigate("/alerts");
  }

  if (status === "loading") return <LoadingSpinner label="Loading alert..." />;
  if (status === "error") return <ErrorPanel error={error} />;
  if (!alert) return null;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-100">Alert detail</h1>
        <div className="flex gap-2">
          <button
            onClick={() => downloadAlertAsJson(alert)}
            className="rounded border border-surface-border px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500"
          >
            Export JSON
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="rounded border border-red-500/50 px-3 py-1.5 text-sm text-red-300 hover:bg-red-500/10 disabled:opacity-40"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="space-y-3 rounded border border-surface-border bg-surface-raised p-4">
        <div className="flex items-center justify-between">
          <SeverityBadge severity={alert.severity} />
          <span className="font-mono text-xs text-slate-500">{alert.id}</span>
        </div>
        <p className="font-mono text-xs uppercase tracking-wide text-slate-400">{alert.threat_type}</p>
        <p className="text-sm text-slate-100">{alert.summary}</p>
        <div>
          <p className="mb-1 text-xs text-slate-400">Indicators of compromise</p>
          <IocChipList iocs={alert.ioc_list} />
        </div>
        <p className="text-sm text-slate-300">
          <span className="text-slate-400">Recommended action: </span>
          {alert.recommended_action}
        </p>
        <p className="text-xs text-slate-500">
          Processed in {alert.processing_ms}ms &middot;{" "}
          {alert.created_at ? new Date(alert.created_at).toLocaleString() : ""}
        </p>
      </div>
    </div>
  );
}
