import axios from "axios";
import { notify } from "./feedback";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000/api/v1/ws/live";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("cybershield_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshRequest: Promise<void> | null = null;

export function clearSession() {
  ["cybershield_token", "cybershield_refresh_token", "cybershield_user"].forEach(key => localStorage.removeItem(key));
  window.dispatchEvent(new Event("cybershield:session-ended"));
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const refreshToken = localStorage.getItem("cybershield_refresh_token");
    if (error.response?.status === 401 && refreshToken && original && !original.__retried && !original.url?.startsWith("/auth/")) {
      original.__retried = true;
      try {
        refreshRequest ??= axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken }).then(({ data }) => {
          localStorage.setItem("cybershield_token", data.access_token);
          localStorage.setItem("cybershield_refresh_token", data.refresh_token);
        }).finally(() => { refreshRequest = null; });
        await refreshRequest;
        original.headers.Authorization = `Bearer ${localStorage.getItem("cybershield_token")}`;
        return api(original);
      } catch {
        clearSession();
        notify("Your session has expired. Please sign in again.");
        return Promise.reject(error);
      }
    }
    const status = error.response?.status;
    if (status === 401 && !original?.url?.startsWith("/auth/")) clearSession();
    notify(status === 403 ? "Access denied. You don't have permission to perform this action." : status === 401 ? "Please sign in with valid credentials." : status === 429 ? "Too many requests. Please wait and try again." : !error.response ? "Unable to connect to the server. Check your connection and try again." : "Unable to complete the request. Please try again.");
    return Promise.reject(error);
  },
);

export type ApiEnvelope<T> = { success: boolean; data: T };

export function currentUser() {
  try { return JSON.parse(localStorage.getItem("cybershield_user") ?? "null"); } catch { return null; }
}

export function hasPermission(permission: string) {
  const user = currentUser();
  return user?.role === "Admin" || user?.permissions?.includes(permission);
}

export function authenticatedWsUrl() {
  const token = localStorage.getItem("cybershield_token");
  const separator = WS_URL.includes("?") ? "&" : "?";
  return token ? `${WS_URL}${separator}token=${encodeURIComponent(token)}` : WS_URL;
}
