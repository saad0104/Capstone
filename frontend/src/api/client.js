const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

export class ApiError extends Error {
  constructor(status, body) {
    super(body?.error || `Request failed with status ${status}`);
    this.status = status;
    this.errorCode = body?.error;
    this.details = body?.details;
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (err) {
    // network failure (backend unreachable, CORS blocked, DNS, etc.) --
    // deliberately NOT wrapped in ApiError, so callers can distinguish
    // "the backend responded with an error" from "couldn't reach it at all"
    throw err;
  }

  if (response.status === 204) {
    return null;
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    // no/invalid JSON body -- fine for e.g. an unexpected 500 with an HTML error page
  }

  if (!response.ok) {
    throw new ApiError(response.status, body);
  }

  return body;
}

export function analyze({ text, provider }) {
  const payload = { text };
  if (provider) {
    payload.provider = provider;
  }
  return request("/api/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listAlerts() {
  return request("/api/alerts");
}

export function getAlert(id) {
  return request(`/api/alerts/${id}`);
}

export function deleteAlert(id) {
  return request(`/api/alerts/${id}`, { method: "DELETE" });
}
