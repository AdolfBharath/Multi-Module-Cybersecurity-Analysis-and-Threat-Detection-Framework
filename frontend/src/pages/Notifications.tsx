import { useState } from "react";
import { CheckCheck } from "lucide-react";
import { useNotifications } from "../lib/notifications";
import { NotificationContent, NotificationList } from "../components/NotificationList";

export function Notifications() {
  const [filter, setFilter] = useState("all");
  const { items, unread, update, updating, isError, isPending } = useNotifications();
  return <div className="soc-dashboard"><div className="page-heading"><div><p className="eyebrow">WORKSPACE</p><h1>Notifications</h1><p>{unread} unread notifications</p></div><button className="text-button" disabled={!unread || updating} onClick={() => update({ action: "read-all" })}><CheckCheck size={16} /> Mark all as read</button></div>
    <div className="segmented" aria-label="Notification filter">{["all", "unread", "read", "archived"].map(value => <button key={value} aria-pressed={filter === value} onClick={() => setFilter(value)}>{value}</button>)}</div>
    <section className="soc-section">{isError || isPending ? <NotificationContent /> : <NotificationList items={items.filter(item => filter === "all" ? item.status !== "archived" : item.status === filter)} />}</section>
  </div>;
}
