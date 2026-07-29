import React from "react";
import { ApiError } from "../api/client";

function Panel({ title, message, children }) {
  return (
    <div className="rounded border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
      <p className="font-semibold">{title}</p>
      {message && <p className="mt-1">{message}</p>}
      {children}
    </div>
  );
}

export default function ErrorPanel({ error, providerHint }) {
  if (!error) return null;

  if (error instanceof ApiError) {
    if (error.status === 400) {
      return (
        <Panel title="Your input was invalid" message={formatDetails(error.details)} />
      );
    }
    if (error.status === 502) {
      return (
        <Panel title="The LLM provider failed to respond" message={formatDetails(error.details)}>
          {providerHint && (
            <p className="mt-2 text-amber-300">
              Note: this provider has not been verified end-to-end — this may be an unverified
              provider issue rather than a transient failure.
            </p>
          )}
        </Panel>
      );
    }
    if (error.status === 404) {
      return <Panel title="Not found" message="This alert no longer exists." />;
    }
    return <Panel title={`Request failed (${error.status})`} message={formatDetails(error.details)} />;
  }

  return (
    <Panel
      title="Could not reach the backend"
      message="Check your connection or that the API server is running."
    />
  );
}

function formatDetails(details) {
  if (!details) return null;
  if (typeof details === "string") return details;
  try {
    return JSON.stringify(details);
  } catch {
    return null;
  }
}
