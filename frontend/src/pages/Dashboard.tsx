import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, Cpu, Database, HardDrive, MemoryStick, RadioTower, ShieldAlert, Siren } from "lucide-react";
import { api, WS_URL } from "../lib/api";
import type { AlertItem, DashboardMetrics } from "../lib/types";
import { Badge, Card, Metric, SectionTitle } from "../components/ui";

const fallback: DashboardMetrics = {
  total_logs: 0,
  critical_alerts: 0,
  incidents: 0,
  high_threats: 0,
  medium_threats: 0,
  low_threats: 0,
  network_status: "Loading",
  cpu: 0,
  memory: 0,
  disk: 0,
  todays_attacks: 0,
  weekly_trend: [],
  monthly_trend: [],
  attack_timeline: [],
  alert_timeline: [],
  recent_activity: [],
  live_feed: [],
  threat_map: [],
  top_attack_sources: [],
  mitre_matrix: [],
};

export function Dashboard() {
  const [live, setLive] = useState<AlertItem[]>([]);
  const { data = fallback } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get<DashboardMetrics>("/dashboard")).data,
    refetchInterval: 30000,
  });

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onmessage = (event) => setLive((current) => [JSON.parse(event.data), ...current].slice(0, 6));
    return () => ws.close();
  }, []);

  const severityData = [
    { name: "Critical", value: data.critical_alerts, color: "#ff526d" },
    { name: "High", value: data.high_threats, color: "#fb923c" },
    { name: "Medium", value: data.medium_threats, color: "#f4b860" },
    { name: "Low", value: data.low_threats, color: "#3df2b7" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <SectionTitle title="SOC Dashboard" subtitle="Live enterprise security posture, attack telemetry, and incident response signal." />
        <div className="flex items-center gap-2 rounded-full border border-mintx/30 bg-mintx/10 px-4 py-2 text-sm text-mintx">
          <RadioTower className="h-4 w-4" />
          {data.network_status}
        </div>
      </div>

      <div className="metric-grid">
        <Metric label="Total Logs" value={data.total_logs} />
        <Metric label="Critical Alerts" value={data.critical_alerts} accent="red" />
        <Metric label="Incidents" value={data.incidents} accent="amber" />
        <Metric label="Today's Attacks" value={data.todays_attacks} accent="mint" />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
        <Card>
          <div className="mb-4 flex items-center gap-2 text-white">
            <ShieldAlert className="h-5 w-5 text-cyanx" />
            Weekly Attack Trend
          </div>
          <div className="h-72">
            <ResponsiveContainer>
              <AreaChart data={data.weekly_trend}>
                <defs>
                  <linearGradient id="attacks" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#35d3ff" stopOpacity={0.55} />
                    <stop offset="95%" stopColor="#35d3ff" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(140,164,190,0.12)" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ background: "#0d1926", border: "1px solid rgba(140,164,190,.2)" }} />
                <Area type="monotone" dataKey="attacks" stroke="#35d3ff" fill="url(#attacks)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <div className="mb-4 flex items-center gap-2 text-white">
            <AlertTriangle className="h-5 w-5 text-amberx" />
            Severity Mix
          </div>
          <div className="h-72">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={severityData} dataKey="value" innerRadius={64} outerRadius={92} paddingAngle={3}>
                  {severityData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ background: "#0d1926", border: "1px solid rgba(140,164,190,.2)" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card>
          <div className="mb-4 grid grid-cols-3 gap-3">
            {[["CPU", data.cpu, Cpu], ["Memory", data.memory, MemoryStick], ["Disk", data.disk, HardDrive]].map(([label, value, Icon]) => {
              const IconComponent = Icon as typeof Cpu;
              return (
                <div key={label as string} className="rounded-md border border-line bg-white/5 p-3">
                  <IconComponent className="mb-2 h-4 w-4 text-cyanx" />
                  <div className="text-xs text-slate-400">{label as string}</div>
                  <div className="text-xl font-bold text-white">{Math.round(value as number)}%</div>
                </div>
              );
            })}
          </div>
          <div className="h-52">
            <ResponsiveContainer>
              <BarChart data={data.monthly_trend}>
                <XAxis dataKey="name" stroke="#94a3b8" />
                <Tooltip contentStyle={{ background: "#0d1926", border: "1px solid rgba(140,164,190,.2)" }} />
                <Bar dataKey="alerts" fill="#3df2b7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <SectionTitle title="Live Feed" />
          <div className="mt-4 space-y-3">
            {[...live, ...data.live_feed].slice(0, 7).map((item, index) => (
              <motion.div key={`${item.title}-${index}`} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} className="rounded-md border border-line bg-white/5 p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-white">{item.title}</div>
                  <Badge severity={item.severity}>{item.severity}</Badge>
                </div>
                <div className="mt-1 text-xs text-slate-400">{item.source}</div>
              </motion.div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionTitle title="MITRE ATT&CK" />
          <div className="mt-4 space-y-3">
            {data.mitre_matrix.map((row) => (
              <div key={`${row.tactic}-${row.technique}`} className="rounded-md border border-line bg-white/5 p-3">
                <div className="text-sm font-semibold text-cyan-50">{row.tactic}</div>
                <div className="mt-1 text-xs text-slate-400">{row.technique}</div>
                <div className="mt-2 h-1.5 rounded-full bg-white/10">
                  <div className="h-1.5 rounded-full bg-cyanx" style={{ width: `${Math.min(100, Number(row.count) * 5)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card>
        <div className="mb-4 flex items-center gap-2 text-white">
          <Database className="h-5 w-5 text-mintx" />
          Recent Activity
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {data.recent_activity.map((item, index) => (
            <div key={index} className="rounded-md border border-line bg-white/5 p-3 text-sm text-slate-300">{item.action}</div>
          ))}
        </div>
      </Card>
    </div>
  );
}

