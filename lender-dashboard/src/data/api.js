const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
  } catch {
    throw new Error("The authentication server is offline. Start the backend on port 8000 and try again.");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed (${response.status})`);
  }

  return response.json();
}

export const fallbackAnalytics = {
  summary: { total: 24, approved: 16, pending: 5, rejected: 3, approval_rate: 67 },
  monthly: [
    { label: "Mar", applications: 12 },
    { label: "Apr", applications: 17 },
    { label: "May", applications: 14 },
    { label: "Jun", applications: 22 },
    { label: "Jul", applications: 20 },
    { label: "Aug", applications: 27 },
  ],
};

export const defaultSettings = {
  review_threshold: 650,
  auto_refresh_minutes: 15,
  email_notifications: true,
  weekly_report: true,
};

export function getAnalytics() {
  return request("/management/analytics");
}

export function getSettings() {
  return request("/management/settings");
}

export function updateSettings(settings) {
  return request("/management/settings", {
    method: "PUT",
    body: JSON.stringify(settings),
  });
}

export function register(credentials) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function login(credentials) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}
