import React, { useEffect, useState } from "react";

export default function App() {
  const [status, setStatus] = useState("loading");
  useEffect(() => {
    fetch("/health")
      .then((r) => r.json())
      .then((j) => setStatus(j.status))
      .catch(() => setStatus("offline"));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">ThreatGPT — Demo</h1>
      <p className="mt-4">Backend status: {status}</p>
      <p className="mt-6 text-sm text-gray-600">
        This is a minimal frontend placeholder. Build the UI pages in{" "}
        <code>src/</code>.
      </p>
    </div>
  );
}
