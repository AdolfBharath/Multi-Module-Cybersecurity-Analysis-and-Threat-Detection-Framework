import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { cn, severityClass } from "../lib/utils";

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("glass card-lift rounded-lg p-4", className)}>{children}</div>;
}

export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={cn(
        "inline-flex h-10 items-center justify-center gap-2 rounded-md border border-cyanx/30 bg-cyanx/15 px-4 text-sm font-semibold text-cyan-50 transition hover:bg-cyanx/25 disabled:cursor-not-allowed disabled:opacity-50",
        props.className,
      )}
    />
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn("h-11 w-full rounded-md border border-line bg-white/5 px-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyanx/70", props.className)} />;
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={cn("min-h-32 w-full rounded-md border border-line bg-white/5 px-3 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyanx/70", props.className)} />;
}

export function Badge({ severity, children }: { severity?: string; children: ReactNode }) {
  return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold capitalize", severityClass(severity))}>{children}</span>;
}

export function Metric({ label, value, accent = "cyan" }: { label: string; value: string | number; accent?: "cyan" | "mint" | "amber" | "red" }) {
  const color = { cyan: "text-cyanx", mint: "text-mintx", amber: "text-amberx", red: "text-dangerx" }[accent];
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass card-lift animated-panel rounded-lg p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{label}</div>
        <span className={cn("h-2 w-2 rounded-full", accent === "red" ? "bg-dangerx" : accent === "amber" ? "bg-amberx" : accent === "mint" ? "bg-mintx" : "bg-cyanx")} />
      </div>
      <div className={cn("mt-3 text-3xl font-bold tabular-nums", color)}>{value}</div>
      <div className="mt-4 h-1 overflow-hidden rounded-full bg-white/10">
        <motion.div
          initial={{ width: "12%" }}
          animate={{ width: `${Math.max(18, Math.min(100, Number(value) || 42))}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={cn("h-full rounded-full", accent === "red" ? "bg-dangerx" : accent === "amber" ? "bg-amberx" : accent === "mint" ? "bg-mintx" : "bg-cyanx")}
        />
      </div>
    </motion.div>
  );
}

export function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div>
      <h2 className="text-xl font-semibold text-white">{title}</h2>
      {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
    </div>
  );
}

export function PageFrame({ children }: { children: ReactNode }) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.32, ease: "easeOut" }}>
      {children}
    </motion.div>
  );
}

export function SkeletonCard() {
  return (
    <div className="glass rounded-lg p-4">
      <div className="skeleton h-5 w-28 rounded" />
      <div className="skeleton mt-5 h-8 w-44 rounded" />
      <div className="skeleton mt-4 h-20 rounded" />
    </div>
  );
}

export function StatusPill({ label }: { label: string }) {
  return (
    <div className="status-pill flex items-center gap-2 rounded-full border border-mintx/30 bg-mintx/10 px-4 py-2 text-sm text-mintx">
      <span className="status-pulse h-2 w-2 rounded-full bg-mintx" />
      {label}
    </div>
  );
}
