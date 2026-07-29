const HEADERS = [
  "id",
  "summary",
  "threat_type",
  "severity",
  "ioc_list",
  "recommended_action",
  "processing_ms",
  "created_at",
];

function csvEscape(value) {
  const s = String(value);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function exportAlertsToCsv(alerts) {
  const rows = alerts.map((a) =>
    HEADERS.map((h) => {
      const v = h === "ioc_list" ? (a.ioc_list || []).join(";") : (a[h] ?? "");
      return csvEscape(v);
    }).join(","),
  );
  const csv = [HEADERS.join(","), ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "alerts-export.csv";
  a.click();
  URL.revokeObjectURL(url);
}
