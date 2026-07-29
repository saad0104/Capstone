export function downloadAlertAsJson(alert) {
  const blob = new Blob([JSON.stringify(alert, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `alert-${alert.id}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
