const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  getBusiness: (businessId = 1) => request(`/business?business_id=${businessId}`),
  getVentures: (businessId = 1) => request(`/ventures?business_id=${businessId}`),
  getVenture: (ventureId) => request(`/ventures/${ventureId}`),
  evaluateVenture: (ventureId) =>
    request(`/ventures/${ventureId}/evaluate`, { method: "POST" }),
  chat: (businessId, message) =>
    request(`/chat`, {
      method: "POST",
      body: JSON.stringify({ business_id: businessId, message }),
    }),
};
