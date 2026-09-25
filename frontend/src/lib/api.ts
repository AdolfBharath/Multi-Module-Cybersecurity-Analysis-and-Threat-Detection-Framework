import axios from "axios";

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

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const refreshToken = localStorage.getItem("cybershield_refresh_token");
    if (error.response?.status === 401 && refreshToken && !original.__retried) {
      original.__retried = true;
      const refreshed = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken });
      localStorage.setItem("cybershield_token", refreshed.data.access_token);
      localStorage.setItem("cybershield_refresh_token", refreshed.data.refresh_token);
      original.headers.Authorization = `Bearer ${refreshed.data.access_token}`;
      return api(original);
    }
    return Promise.reject(error);
  },
);

export type ApiEnvelope<T> = { success: boolean; data: T };

export function currentUser() {
  return JSON.parse(localStorage.getItem("cybershield_user") ?? "null");
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
