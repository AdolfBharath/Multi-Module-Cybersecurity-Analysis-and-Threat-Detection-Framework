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

export type ApiEnvelope<T> = { success: boolean; data: T };

