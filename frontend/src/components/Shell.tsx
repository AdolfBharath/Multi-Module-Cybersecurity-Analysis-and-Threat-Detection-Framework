import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Activity,
  Bell,
  Bug,
  ChartNoAxesCombined,
  FileBarChart,
  Fingerprint,
  Gauge,
  Globe2,
  HardDriveUpload,
  Lock,
  Network,
  Radar,
  Search,
  Settings,
  Shield,
  Siren,
  Terminal,
  UserCircle,
} from "lucide-react";
import { cn } from "../lib/utils";

const nav = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/logs", label: "Logs", icon: HardDriveUpload },
  { to: "/detection", label: "Detection", icon: Radar },
  { to: "/anomaly", label: "Anomaly", icon: ChartNoAxesCombined },
  { to: "/network", label: "Network", icon: Network },
  { to: "/malware", label: "Malware", icon: Bug },
  { to: "/vulnerabilities", label: "Vulnerabilities", icon: Terminal },
  { to: "/intel", label: "Threat Intel", icon: Globe2 },
  { to: "/incidents", label: "Incidents", icon: Siren },
  { to: "/reports", label: "Reports", icon: FileBarChart },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/audit", label: "Audit", icon: Fingerprint },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Shell() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("cybershield_user") ?? "null");

  return (
    <div className="min-h-screen cyber-grid">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-72 border-r border-line bg-abyss/86 p-4 backdrop-blur-xl lg:block">
        <div className="flex items-center gap-3 px-2 py-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-cyanx/40 bg-cyanx/15">
            <Shield className="h-6 w-6 text-cyanx" />
          </div>
          <div>
            <div className="text-lg font-bold text-white">CyberShield XDR</div>
            <div className="text-xs text-slate-400">Enterprise SOC Platform</div>
          </div>
        </div>
        <nav className="mt-6 space-y-1">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex h-10 items-center gap-3 rounded-md px-3 text-sm text-slate-300 transition hover:bg-white/7 hover:text-white",
                  isActive && "border border-cyanx/25 bg-cyanx/13 text-cyan-50 shadow-glow",
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="lg:pl-72">
        <header className="sticky top-0 z-10 border-b border-line bg-abyss/76 px-4 py-3 backdrop-blur-xl lg:px-8">
          <div className="flex items-center justify-between gap-4">
            <div className="relative max-w-xl flex-1">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input className="h-10 w-full rounded-md border border-line bg-white/5 pl-10 pr-3 text-sm outline-none focus:border-cyanx/60" placeholder="Search alerts, incidents, indicators..." />
            </div>
            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-2 rounded-full border border-mintx/30 bg-mintx/10 px-3 py-1.5 text-xs text-mintx md:flex">
                <Activity className="h-3.5 w-3.5" />
                Live telemetry
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-300">
                <UserCircle className="h-5 w-5" />
                <span className="hidden sm:inline">{user?.full_name ?? "SOC Analyst"}</span>
              </div>
              <button
                className="rounded-md border border-line p-2 text-slate-300 hover:bg-white/7"
                title="Sign out"
                onClick={() => {
                  localStorage.clear();
                  navigate("/login");
                }}
              >
                <Lock className="h-4 w-4" />
              </button>
            </div>
          </div>
        </header>
        <div className="p-4 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

