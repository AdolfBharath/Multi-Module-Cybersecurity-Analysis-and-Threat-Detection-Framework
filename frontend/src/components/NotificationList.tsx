import { Link } from "react-router-dom";
import { Archive, Bell, Check, ArrowUpRight } from "lucide-react";
import { notificationTarget, relativeTime, useNotifications, type NotificationItem } from "../lib/notifications";

export function NotificationList({ items, compact = false }: { items: NotificationItem[]; compact?: boolean }) {
  const { update, updating } = useNotifications();
  if (!items.length) return <div className="empty-state"><Bell size={24} /><strong>You're all caught up</strong><span>No notifications in this view.</span></div>;
  return <ul className="notification-list">{items.map(item => { const target = notificationTarget(item); return <li key={item.id} className={item.status === "unread" ? "unread" : ""}>
    <span className={`severity-dot ${item.severity}`} /><div className="notification-copy"><div className="notification-title">{item.title}</div><p>{item.message}</p><time dateTime={item.created_at}>{relativeTime(item.created_at)}</time>
    {target && <Link className="resource-link" to={target} onClick={() => { if (item.status === "unread") update({ id: item.id, action: "read" }); }}>Open resource <ArrowUpRight size={13} /></Link>}</div>
    <div className="notification-actions">{item.status === "unread" && <button className="icon-button" title="Mark as read" aria-label={`Mark ${item.title} as read`} disabled={updating} onClick={() => update({ id: item.id, action: "read" })}><Check size={16} /></button>}{!compact && item.status !== "archived" && <button className="icon-button" title="Archive" aria-label={`Archive ${item.title}`} disabled={updating} onClick={() => update({ id: item.id, action: "archive" })}><Archive size={16} /></button>}</div>
  </li>; })}</ul>;
}

export function NotificationContent({ compact = false }: { compact?: boolean }) {
  const { items, isPending, isError, refetch } = useNotifications();
  if (isPending) return <div aria-label="Loading notifications" className="skeleton-list">{[1, 2, 3].map(i => <div key={i} className="skeleton" />)}</div>;
  if (isError) return <div className="empty-state"><strong>Unable to load notifications</strong><button className="text-button" onClick={() => refetch()}>Retry</button></div>;
  return <NotificationList compact={compact} items={items.filter(item => item.status !== "archived").slice(0, compact ? 4 : undefined)} />;
}
