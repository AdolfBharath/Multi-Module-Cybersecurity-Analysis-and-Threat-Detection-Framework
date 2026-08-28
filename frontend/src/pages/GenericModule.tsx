import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Activity, Database, ShieldCheck } from "lucide-react";
import { api } from "../lib/api";
import type { ModuleItem } from "../lib/types";
import { Badge, Card, PageFrame, SectionTitle, SkeletonCard } from "../components/ui";

function normalize(payload: unknown): ModuleItem[] {
  if (Array.isArray(payload)) return payload as ModuleItem[];
  if (payload && typeof payload === "object") {
    const objectPayload = payload as Record<string, unknown>;
    if (Array.isArray(objectPayload.data)) return objectPayload.data as ModuleItem[];
    return Object.entries(objectPayload).map(([key, value], index) => ({
      id: index,
      title: key,
      status: "configured",
      description: JSON.stringify(value),
    }));
  }
  return [];
}

export function GenericModule({ title, endpoint }: { title: string; endpoint: string }) {
  const { data = [], isLoading } = useQuery({
    queryKey: [endpoint],
    queryFn: async () => {
      const response = await api.get(endpoint);
      return normalize(response.data.data ?? response.data);
    },
  });

  return (
    <PageFrame>
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <SectionTitle title={title} subtitle="Operational module workspace with API-backed data and production extension points." />
        <div className="grid grid-cols-3 gap-2 rounded-lg border border-line bg-white/5 p-2">
          {[
            [Activity, "Live"],
            [ShieldCheck, "Guarded"],
            [Database, "Stored"],
          ].map(([Icon, label]) => {
            const IconComponent = Icon as typeof Activity;
            return (
              <div key={String(label)} className="flex min-w-24 items-center justify-center gap-2 rounded-md bg-abyss/70 px-3 py-2 text-xs text-slate-300">
                <IconComponent className="h-3.5 w-3.5 text-cyanx" />
                {String(label)}
              </div>
            );
          })}
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((item) => <SkeletonCard key={item} />)}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {!isLoading && data.length ? data.map((item, index) => (
          <motion.div key={String(item.id ?? index)} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.035, duration: 0.28 }}>
          <Card>
            <div className="flex items-center justify-between gap-3">
              <Badge severity={String(item.severity ?? "info")}>{String(item.severity ?? "info")}</Badge>
              <span className="text-xs uppercase tracking-[0.14em] text-slate-500">{String(item.status ?? "active")}</span>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-white">{String(item.title ?? item.name ?? item.target ?? `Record ${index + 1}`)}</h3>
            <p className="mt-2 line-clamp-4 text-sm text-slate-400">{String(item.description ?? item.message ?? JSON.stringify(item))}</p>
          </Card>
          </motion.div>
        )) : !isLoading ? (
          <Card className="md:col-span-2 xl:col-span-3">
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="grid h-12 w-12 place-items-center rounded-lg border border-cyanx/30 bg-cyanx/10">
                <Database className="h-6 w-6 text-cyanx" />
              </div>
              <div className="mt-4 text-base font-semibold text-white">No records yet</div>
              <div className="mt-2 max-w-lg text-sm text-slate-400">This module is API-ready and will populate as telemetry, reports, detections, or scan results are collected.</div>
            </div>
          </Card>
        ) : null}
      </div>
    </div>
    </PageFrame>
  );
}
