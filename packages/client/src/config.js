const API_BASE = import.meta.env.VITE_API_URL;

if (!API_BASE) {
  throw new Error("VITE_API_URL is not set");
}

export const config = {
  apiBase: API_BASE,
  authBase: `${API_BASE}/api/v1/auth`,
  wsUrl: `${API_BASE.replace(/^http/, "ws")}/ws`,
};