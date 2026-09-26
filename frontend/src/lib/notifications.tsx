import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, authenticatedWsUrl, currentUser, hasPermission } from "./api";
import { notify } from "./feedback";

export type NotificationItem = { id: number; title: string; message: string; severity: string; status: string; created_at: string; related_entity?: string; related_id?: number; required_permission: string };
type Snapshot = { notifications: NotificationItem[]; unread_count: number };

function useNotificationState() {
  const client = useQueryClient();
  const [connected, setConnected] = useState(false);
  const user = currentUser();
  const key = ["notifications", user?.id ?? user?.email];
  const query = useQuery({ queryKey: key, queryFn: async (): Promise<Snapshot> => {
    const [list, count] = await Promise.all([api.get("/notifications"), api.get("/notifications/unread-count")]);
    return { notifications: list.data.data, unread_count: count.data.data.unread_count };
  }, enabled: !!hasPermission("dashboard:read"), staleTime: 15000, refetchInterval: connected ? false : 60000, retry: 1 });
  useEffect(() => {
    if (!hasPermission("dashboard:read")) return;
    let stopped = false;
    let socket: WebSocket | undefined;
    let timer: number;
    let delay = 1000;
    const connect = () => {
      if (stopped) return;
      socket = new WebSocket(authenticatedWsUrl());
      socket.onopen = () => { setConnected(true); delay = 1000; };
      socket.onmessage = event => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === "notification_snapshot" && Array.isArray(message.notifications) && typeof message.unread_count === "number") {
            client.setQueryData(["notifications", user?.id ?? user?.email], { notifications: message.notifications, unread_count: message.unread_count });
          }
          if (message.type === "alert") client.invalidateQueries({ queryKey: ["dashboard"] });
        } catch { /* Ignore malformed frames; the HTTP fallback remains available. */ }
      };
      socket.onclose = () => { if (!stopped) { setConnected(false); timer = window.setTimeout(connect, delay); delay = Math.min(delay * 2, 30000); } };
      socket.onerror = () => socket?.close();
    };
    connect();
    return () => { stopped = true; window.clearTimeout(timer); socket?.close(); };
  }, [client, user?.id, user?.email]);
  const mutation = useMutation({ mutationFn: async ({ id, action }: { id?: number; action: "read" | "archive" | "read-all" }) => {
    await api.put(action === "read-all" ? "/notifications/read-all" : `/notifications/${id}/${action}`);
  }, onSuccess: async () => { await client.invalidateQueries({ queryKey: key }); notify("Notifications updated.", "success"); } });
  return { ...query, items: query.data?.notifications ?? [], unread: query.data?.unread_count ?? 0, connected, update: mutation.mutate, updating: mutation.isPending };
}
const Context = createContext<ReturnType<typeof useNotificationState> | null>(null);
export function NotificationProvider({ children }: { children: ReactNode }) { const state = useNotificationState(); return <Context.Provider value={state}>{children}</Context.Provider>; }
export function useNotifications() { const state = useContext(Context); if (!state) throw new Error("NotificationProvider required"); return state; }
export function notificationTarget(item: NotificationItem) {
  const routes: Record<string, [string, string]> = { alert: ["/detection", "alerts:read"], incident: ["/incidents", "incidents:read"], malware: ["/malware", "malware:analyze"], vulnerability: ["/vulnerabilities", "vulnerability:scan"], report: ["/reports", "reports:read"], network: ["/network", "dashboard:read"] };
  const resource = (item.related_entity ?? "").replace(/s$/, "");
  const target = routes[resource];
  return target && hasPermission(target[1]) ? `${target[0]}${item.related_id ? `?id=${item.related_id}` : ""}` : null;
}
export function relativeTime(value: string) {
  const time = Date.parse(/(?:Z|[+-]\d\d:\d\d)$/.test(value) ? value : `${value}Z`);
  if (!Number.isFinite(time)) return "Time unavailable";
  const minutes = Math.max(0, Math.floor((Date.now() - time) / 60000));
  return minutes < 1 ? "Just now" : minutes < 60 ? `${minutes}m ago` : minutes < 1440 ? `${Math.floor(minutes / 60)}h ago` : `${Math.floor(minutes / 1440)}d ago`;
}
