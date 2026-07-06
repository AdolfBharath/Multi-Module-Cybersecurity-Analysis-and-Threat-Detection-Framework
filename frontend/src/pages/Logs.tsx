import { useQuery } from "@tanstack/react-query";
import { UploadCloud } from "lucide-react";
import { api } from "../lib/api";
import { Badge, Card, SectionTitle } from "../components/ui";

type LogRow = {
  id: number;
  source: string;
  log_type: string;
  message: string;
  severity: string;
  tags: string[];
  created_at: string;
};

export function Logs() {
  const { data = [] } = useQuery({
    queryKey: ["logs"],
    queryFn: async () => (await api.get<LogRow[]>("/logs")).data,
  });

  async function upload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    await api.post("/logs/upload", form, { headers: { "Content-Type": "multipart/form-data" } });
    window.location.reload();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <SectionTitle title="Log Management" subtitle="Upload, search, tag, and triage raw telemetry from security tools." />
        <label className="inline-flex h-10 cursor-pointer items-center gap-2 rounded-md border border-cyanx/30 bg-cyanx/15 px-4 text-sm font-semibold text-cyan-50 hover:bg-cyanx/25">
          <UploadCloud className="h-4 w-4" />
          Upload Logs
          <input type="file" className="hidden" accept=".csv,.json,.txt,.log" onChange={upload} />
        </label>
      </div>
      <Card className="overflow-hidden p-0">
        <div className="grid grid-cols-[110px_100px_110px_1fr_180px] border-b border-line px-4 py-3 text-xs uppercase tracking-[0.14em] text-slate-500">
          <div>Severity</div>
          <div>Source</div>
          <div>Type</div>
          <div>Message</div>
          <div>Time</div>
        </div>
        <div className="divide-y divide-line">
          {data.map((row) => (
            <div key={row.id} className="grid grid-cols-[110px_100px_110px_1fr_180px] gap-3 px-4 py-3 text-sm text-slate-300">
              <Badge severity={row.severity}>{row.severity}</Badge>
              <div>{row.source}</div>
              <div>{row.log_type}</div>
              <div className="truncate">{row.message}</div>
              <div className="text-xs text-slate-500">{new Date(row.created_at).toLocaleString()}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

