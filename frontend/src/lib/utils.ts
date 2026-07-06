import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function severityClass(severity = "info") {
  const classes: Record<string, string> = {
    critical: "border-dangerx/50 bg-dangerx/12 text-red-100",
    high: "border-orange-400/50 bg-orange-400/12 text-orange-100",
    medium: "border-amberx/50 bg-amberx/12 text-amber-100",
    low: "border-mintx/50 bg-mintx/12 text-emerald-100",
    info: "border-cyanx/50 bg-cyanx/12 text-cyan-100",
  };
  return classes[severity] ?? classes.info;
}

