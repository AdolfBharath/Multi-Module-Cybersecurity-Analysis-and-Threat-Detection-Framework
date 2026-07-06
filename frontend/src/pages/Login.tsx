import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import { api } from "../lib/api";
import { Button, Card, Input } from "../components/ui";

export function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@cybershield.dev");
  const [password, setPassword] = useState("CyberShield!2026");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const response = await api.post("/auth/login", { email, password });
      localStorage.setItem("cybershield_token", response.data.access_token);
      localStorage.setItem("cybershield_user", JSON.stringify(response.data.user));
      navigate("/");
    } catch {
      setError("Invalid credentials or backend unavailable.");
    }
  }

  return (
    <div className="grid min-h-screen place-items-center px-4">
      <div className="w-full max-w-5xl overflow-hidden rounded-lg border border-line bg-abyss/80 shadow-2xl backdrop-blur-xl md:grid md:grid-cols-[1.1fr_0.9fr]">
        <div className="relative min-h-[520px] p-8 cyber-grid">
          <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(53,211,255,0.14),transparent_42%),linear-gradient(35deg,rgba(61,242,183,0.12),transparent_55%)]" />
          <div className="relative z-10 flex h-full flex-col justify-between">
            <div className="flex items-center gap-3">
              <div className="grid h-12 w-12 place-items-center rounded-lg border border-cyanx/40 bg-cyanx/15">
                <ShieldCheck className="h-7 w-7 text-cyanx" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">CyberShield XDR</h1>
                <p className="text-sm text-slate-400">Unified detection, response, and intelligence</p>
              </div>
            </div>
            <div>
              <div className="max-w-xl text-5xl font-bold leading-tight text-white">Command the full attack surface from one SOC console.</div>
              <div className="mt-6 grid grid-cols-3 gap-3 text-sm">
                {["Real-time alerts", "MITRE mapping", "AI anomaly scoring"].map((item) => (
                  <div key={item} className="rounded-md border border-line bg-white/5 p-3 text-slate-200">{item}</div>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div className="grid place-items-center p-6">
          <Card className="w-full max-w-md">
            <div className="mb-6 flex items-center gap-3">
              <LockKeyhole className="h-5 w-5 text-cyanx" />
              <div>
                <h2 className="text-xl font-semibold text-white">Secure Sign In</h2>
                <p className="text-sm text-slate-400">JWT session with RBAC-ready claims</p>
              </div>
            </div>
            <form onSubmit={submit} className="space-y-4">
              <Input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" type="email" />
              <Input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" type="password" />
              {error ? <div className="rounded-md border border-dangerx/40 bg-dangerx/10 p-3 text-sm text-red-100">{error}</div> : null}
              <Button className="w-full" type="submit">Enter SOC</Button>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}
