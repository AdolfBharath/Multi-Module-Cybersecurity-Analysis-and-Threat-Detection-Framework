import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { api } from "../lib/api";
import { Badge, Button, Card, Input, SectionTitle } from "../components/ui";

type Incident = {
  id: number;
  title: string;
  severity: string;
  status: string;
  assignee: string;
  created_at: string;
};

export function Incidents() {
  const [title, setTitle] = useState("New suspicious privilege escalation");
  const { data = [], refetch } = useQuery({
    queryKey: ["incidents"],
    queryFn: async () => (await api.get<Incident[]>("/incidents")).data,
  });

  async function create() {
    await api.post("/incidents", { title, severity: "high", assignee: "SOC Queue", evidence: { source: "console" } });
    setTitle("");
    refetch();
  }

  return (
    <div className="space-y-6">
      <SectionTitle title="Incident Management" subtitle="Create, assign, track evidence, and drive response timelines." />
      <Card>
        <div className="flex flex-col gap-3 md:flex-row">
          <Input value={title} onChange={(event) => setTitle(event.target.value)} />
          <Button onClick={create}>
            <Plus className="h-4 w-4" />
            Create
          </Button>
        </div>
      </Card>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.map((incident) => (
          <Card key={incident.id}>
            <div className="flex items-center justify-between gap-3">
              <Badge severity={incident.severity}>{incident.severity}</Badge>
              <span className="text-xs uppercase tracking-[0.14em] text-slate-500">{incident.status}</span>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-white">{incident.title}</h3>
            <div className="mt-3 text-sm text-slate-400">Assigned to {incident.assignee}</div>
          </Card>
        ))}
      </div>
    </div>
  );
}

