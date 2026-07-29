import React, { useEffect, useMemo } from "react";
import { listAlerts } from "../api/client";
import { useAlerts } from "../context/AlertsContext";
import { exportAlertsToCsv } from "../utils/csvExport";
import AlertCard from "../components/AlertCard";
import ErrorPanel from "../components/ErrorPanel";
import LoadingSpinner from "../components/LoadingSpinner";

const THREAT_TYPES = [
  "all",
  "vulnerability",
  "supply-chain",
  "ransomware",
  "phishing",
  "DDoS",
  "exploit",
  "malware",
  "APT",
  "other",
];
const SEVERITIES = ["all", "Critical", "High", "Medium", "Low"];

export default function AlertsListPage() {
  const { alerts, status, error, filters, dispatch } = useAlerts();

  useEffect(() => {
    if (status === "idle") {
      refresh();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  async function refresh() {
    dispatch({ type: "FETCH_START" });
    try {
      const data = await listAlerts();
      dispatch({ type: "FETCH_SUCCESS", alerts: data });
    } catch (err) {
      dispatch({ type: "FETCH_ERROR", error: err });
    }
  }

  const filteredAlerts = useMemo(() => {
    return alerts.filter(
      (a) =>
        (filters.threatType === "all" || a.threat_type === filters.threatType) &&
        (filters.severity === "all" || a.severity === filters.severity),
    );
  }, [alerts, filters]);

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-slate-100">Alerts</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={refresh}
            className="rounded border border-surface-border px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500"
          >
            Refresh
          </button>
          <button
            onClick={() => exportAlertsToCsv(filteredAlerts)}
            disabled={filteredAlerts.length === 0}
            className="rounded bg-severity-medium/90 px-3 py-1.5 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Export CSV
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          value={filters.threatType}
          onChange={(e) => dispatch({ type: "SET_FILTER", key: "threatType", value: e.target.value })}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1 text-sm text-slate-200"
        >
          {THREAT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t === "all" ? "All threat types" : t}
            </option>
          ))}
        </select>
        <select
          value={filters.severity}
          onChange={(e) => dispatch({ type: "SET_FILTER", key: "severity", value: e.target.value })}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1 text-sm text-slate-200"
        >
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s === "all" ? "All severities" : s}
            </option>
          ))}
        </select>
      </div>

      {status === "loading" && <LoadingSpinner label="Loading alerts..." />}
      {status === "error" && <ErrorPanel error={error} />}

      {status === "loaded" && filteredAlerts.length === 0 && (
        <p className="text-sm text-slate-400">
          {alerts.length === 0 ? "No alerts yet — analyze a report to create one." : "No alerts match the current filters."}
        </p>
      )}

      {status === "loaded" && filteredAlerts.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filteredAlerts.map((a) => (
            <AlertCard key={a.id} alert={a} />
          ))}
        </div>
      )}
    </div>
  );
}
