import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { Clock3, FileSearch, Plus, X } from "lucide-react";
import { api, hasPermission } from "../lib/api";
import { Badge, Button, Card, Input, SectionTitle } from "../components/ui";

type Incident = {
  id: number;
  title: string;
  severity: string;
  status: string;
  assignee: string;
  created_at: string;
  evidence?: Record<string, unknown>;
  timeline?: Array<{ event: string; actor?: string; time?: string }>;
};

export function Incidents() {
  const [params, setParams] = useSearchParams();
  const [title, setTitle] = useState("New suspicious privilege escalation");
  const selectedId = Number(params.get("id")) || null;
  const { data = [], refetch } = useQuery({
    queryKey: ["incidents"],
    queryFn: async () => (await api.get<Incident[]>("/incidents")).data,
  });
  const detail = useQuery({
    queryKey: ["incident", selectedId],
    enabled: !!selectedId,
    queryFn: async () => (await api.get<Incident>(`/incidents/${selectedId}`)).data,
  });

  async function create() {
    await api.post("/incidents", { title, severity: "high", assignee: "SOC Queue", evidence: { source: "console" } });
    setTitle("");
    refetch();
  }

  return (
    <div className="space-y-6">
      <SectionTitle title="Incident Management" subtitle="Create, assign, track evidence, and drive response timelines." />
      {hasPermission("incidents:create") && <Card>
        <div className="flex flex-col gap-3 md:flex-row">
          <Input value={title} onChange={(event) => setTitle(event.target.value)} />
          <Button onClick={create}>
            <Plus className="h-4 w-4" />
            Create
          </Button>
        </div>
      </Card>}
      <div className="incident-workspace">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.map((incident) => (
          <Card key={incident.id} className={`incident-card ${selectedId === incident.id ? "selected" : ""}`}>
            <div className="flex items-center justify-between gap-3">
              <Badge severity={incident.severity}>{incident.severity}</Badge>
              <span className="text-xs uppercase tracking-[0.14em] text-slate-500">{incident.status}</span>
            </div>
            <button className="mt-4 w-full text-left text-lg font-semibold text-white" onClick={() => setParams({ id: String(incident.id) })}>{incident.title}</button>
            <div className="mt-3 flex items-center gap-2 text-sm text-slate-400"><FileSearch className="h-4 w-4" /> Assigned to {incident.assignee}</div>
            <button className="mt-4 flex items-center gap-2 text-xs text-cyanx hover:text-white" onClick={() => setParams({ id: String(incident.id) })}><Clock3 className="h-3.5 w-3.5" /> Open investigation</button>
          </Card>
        ))}
      </div>
      {selectedId && <aside className="incident-detail" aria-live="polite">
        <div className="flex items-start justify-between gap-3"><div><span className="eyebrow">Incident {selectedId}</span><h2>{detail.data?.title ?? "Loading investigation"}</h2></div><button className="icon-button" title="Close incident details" onClick={() => setParams({})}><X className="h-4 w-4" /></button></div>
        {detail.isError ? <p className="detail-empty">This incident is no longer available for your organization.</p> : detail.isPending ? <div className="skeleton detail-skeleton" /> : detail.data && <>
          <div className="detail-meta"><Badge severity={detail.data.severity}>{detail.data.severity}</Badge><span>{detail.data.status}</span><span>{detail.data.assignee}</span></div>
          <section><h3>Evidence</h3><pre>{JSON.stringify(detail.data.evidence ?? {}, null, 2)}</pre></section>
          <section><h3>Investigation timeline</h3><ol>{(detail.data.timeline ?? []).map((entry, index) => <li key={`${entry.event}-${index}`}><span>{entry.event}</span><small>{entry.actor ?? "system"}{entry.time ? ` · ${new Date(entry.time).toLocaleString()}` : ""}</small></li>)}</ol></section>
        </>}
      </aside>}
      </div>
    </div>
  );
}
