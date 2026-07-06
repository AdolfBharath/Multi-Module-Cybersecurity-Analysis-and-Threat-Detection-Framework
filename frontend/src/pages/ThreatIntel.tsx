import { useState } from "react";
import { Globe2 } from "lucide-react";
import { api } from "../lib/api";
import { Button, Card, Input, SectionTitle } from "../components/ui";

export function ThreatIntel() {
  const [indicator, setIndicator] = useState("203.0.113.13");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  async function lookup() {
    const response = await api.get("/threat-intel/lookup", { params: { indicator, indicator_type: "ip" } });
    setResult(response.data.data);
  }

  return (
    <div className="space-y-6">
      <SectionTitle title="Threat Intelligence" subtitle="IOC enrichment across VirusTotal, AbuseIPDB, AlienVault OTX, and MITRE ATT&CK-ready sources." />
      <Card>
        <div className="flex flex-col gap-3 md:flex-row">
          <Input value={indicator} onChange={(event) => setIndicator(event.target.value)} />
          <Button onClick={lookup}>
            <Globe2 className="h-4 w-4" />
            Lookup
          </Button>
        </div>
      </Card>
      {result ? (
        <Card>
          <pre className="overflow-auto rounded-md bg-black/30 p-4 text-sm text-cyan-50">{JSON.stringify(result, null, 2)}</pre>
        </Card>
      ) : null}
    </div>
  );
}

