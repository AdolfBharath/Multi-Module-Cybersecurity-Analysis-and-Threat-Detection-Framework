import { useEffect, useState } from "react";
import { CheckCircle2, AlertCircle, X } from "lucide-react";

export function Toasts() {
  const [items, setItems] = useState<Array<{ id: number; message: string; kind: string }>>([]);
  useEffect(() => {
    const timers = new Set<number>();
    const listener = (event: Event) => {
      const detail = (event as CustomEvent).detail;
      const id = Date.now();
      setItems(current => [...current.filter(item => item.message !== detail.message), { ...detail, id }].slice(-3));
      const timer = window.setTimeout(() => { setItems(current => current.filter(item => item.id !== id)); timers.delete(timer); }, 6000);
      timers.add(timer);
    };
    window.addEventListener("cybershield:toast", listener);
    return () => { window.removeEventListener("cybershield:toast", listener); timers.forEach(window.clearTimeout); };
  }, []);
  return <div className="toast-stack" aria-live="polite">{items.map(item => <div role={item.kind === "error" ? "alert" : "status"} className={`toast ${item.kind}`} key={item.id}>
    {item.kind === "error" ? <AlertCircle size={20} /> : <CheckCircle2 size={20} />}<span>{item.message}</span><button className="icon-button" aria-label="Dismiss notification" onClick={() => setItems(current => current.filter(row => row.id !== item.id))}><X size={16} /></button>
  </div>)}</div>;
}
