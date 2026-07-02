export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function apiJson(path, { token, method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const payload = await readPayload(response);
  if (!response.ok) throw new Error(errorMessage(payload, "Request failed"));
  return payload;
}

export async function apiForm(path, formData, token) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });
  const payload = await readPayload(response);
  if (!response.ok) throw new Error(errorMessage(payload, "Request failed"));
  return payload;
}

export async function downloadBlob(path, token) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    const payload = await readPayload(response);
    throw new Error(errorMessage(payload, "Download failed"));
  }
  return response.blob();
}

async function readPayload(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return response.json();
  return response.text();
}

function errorMessage(payload, fallback) {
  if (payload && typeof payload === "object" && "detail" in payload) return payload.detail;
  if (typeof payload === "string" && payload) return payload;
  return fallback;
}
