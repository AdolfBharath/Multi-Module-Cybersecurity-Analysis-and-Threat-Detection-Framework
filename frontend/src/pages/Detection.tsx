import { useState } from "react";
import { ScanSearch } from "lucide-react";
import { api } from "../lib/api";
import { Badge, Button, Card, SectionTitle, Textarea } from "../components/ui";

type DetectionResult = {
  matched: boolean;
  risk_score: number;
  alerts: Array<{ title: string; severity: string; source: string; description: string }>;
  recommendations: string[];
};

export function Detection() {
  const [text, setText] = useState("GET /search?q=' UNION SELECT password FROM users --");
  const [result, setResult] = useState<DetectionResult | null>(null);

  async function analyze() {
    const response = await api.post<DetectionResult>("/detection/analyze", { text, source: "analyst-console" });
    setResult(response.data);
  }

  return (
    <div className="space-y-6">
      <SectionTitle title="Threat Detection Engine" subtitle="Signature and behavior detection for SQLi, XSS, brute force, PowerShell abuse, ransomware, beaconing, and more." />
      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <Textarea value={text} onChange={(event) => setText(event.target.value)} />
          <Button className="mt-4" onClick={analyze}>
            <ScanSearch className="h-4 w-4" />
            Analyze Telemetry
          </Button>
        </Card>
        <Card>
          <SectionTitle title="Detection Result" />
          {result ? (
            <div className="mt-4 space-y-4">
              <div className="rounded-md border border-line bg-white/5 p-4">
                <div className="text-sm text-slate-400">Risk Score</div>
                <div className="mt-1 text-4xl font-bold text-dangerx">{result.risk_score}</div>
              </div>
              {result.alerts.map((alert) => (
                <div key={alert.title} className="rounded-md border border-line bg-white/5 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-semibold text-white">{alert.title}</div>
                    <Badge severity={alert.severity}>{alert.severity}</Badge>
                  </div>
                  <p className="mt-2 text-sm text-slate-400">{alert.description}</p>
                </div>
              ))}
              <div className="text-sm text-slate-300">{result.recommendations.join(" ")}</div>
            </div>
          ) : (
            <div className="mt-4 rounded-md border border-line bg-white/5 p-6 text-sm text-slate-400">Run analysis to generate alerts and recommendations.</div>
          )}
        </Card>
      </div>
    </div>
  );
}

