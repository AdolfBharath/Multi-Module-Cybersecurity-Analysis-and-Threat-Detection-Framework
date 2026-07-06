import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { ModuleItem } from "../lib/types";
import { Badge, Card, SectionTitle } from "../components/ui";

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
  const { data = [] } = useQuery({
    queryKey: [endpoint],
    queryFn: async () => {
      const response = await api.get(endpoint);
      return normalize(response.data.data ?? response.data);
    },
  });

  return (
    <div className="space-y-6">
      <SectionTitle title={title} subtitle="Operational module workspace with API-backed data and production extension points." />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.length ? data.map((item, index) => (
          <Card key={String(item.id ?? index)}>
            <div className="flex items-center justify-between gap-3">
              <Badge severity={String(item.severity ?? "info")}>{String(item.severity ?? "info")}</Badge>
              <span className="text-xs uppercase tracking-[0.14em] text-slate-500">{String(item.status ?? "active")}</span>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-white">{String(item.title ?? item.name ?? item.target ?? `Record ${index + 1}`)}</h3>
            <p className="mt-2 line-clamp-4 text-sm text-slate-400">{String(item.description ?? item.message ?? JSON.stringify(item))}</p>
          </Card>
        )) : (
          <Card className="md:col-span-2 xl:col-span-3">
            <div className="text-sm text-slate-400">No records yet. This module is API-ready and will populate as telemetry is collected.</div>
          </Card>
        )}
      </div>
    </div>
  );
}

