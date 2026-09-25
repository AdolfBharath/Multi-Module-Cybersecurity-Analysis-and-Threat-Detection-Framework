import { Navigate, Route, Routes } from "react-router-dom";
import type React from "react";
import { Shell } from "./components/Shell";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { Logs } from "./pages/Logs";
import { Detection } from "./pages/Detection";
import { Incidents } from "./pages/Incidents";
import { GenericModule } from "./pages/GenericModule";
import { ThreatIntel } from "./pages/ThreatIntel";
import { currentUser, hasPermission } from "./lib/api";

function Protected() {
  return localStorage.getItem("cybershield_token") ? <Shell /> : <Navigate to="/login" replace />;
}

function RequirePermission({ permission, children }: { permission: string; children: React.ReactNode }) {
  return currentUser() && hasPermission(permission) ? children : <Navigate to="/unauthorized" replace />;
}

function Unauthorized() {
  return (
    <div className="grid min-h-[60vh] place-items-center text-center">
      <div className="glass rounded-lg p-8">
        <h1 className="text-2xl font-semibold text-white">Unauthorized</h1>
        <p className="mt-2 text-sm text-slate-400">Your role does not include permission to access this workspace.</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Protected />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/logs" element={<RequirePermission permission="logs:read"><Logs /></RequirePermission>} />
        <Route path="/detection" element={<RequirePermission permission="alerts:read"><Detection /></RequirePermission>} />
        <Route path="/incidents" element={<RequirePermission permission="incidents:read"><Incidents /></RequirePermission>} />
        <Route path="/intel" element={<RequirePermission permission="threat_intel:read"><ThreatIntel /></RequirePermission>} />
        <Route path="/anomaly" element={<RequirePermission permission="alerts:read"><GenericModule title="Anomaly Detection" endpoint="/anomaly" /></RequirePermission>} />
        <Route path="/network" element={<RequirePermission permission="dashboard:read"><GenericModule title="Network Monitoring" endpoint="/network" /></RequirePermission>} />
        <Route path="/malware" element={<RequirePermission permission="malware:analyze"><GenericModule title="Malware Analysis" endpoint="/malware" /></RequirePermission>} />
        <Route path="/vulnerabilities" element={<RequirePermission permission="vulnerability:scan"><GenericModule title="Vulnerability Scanner" endpoint="/vulnerabilities" /></RequirePermission>} />
        <Route path="/reports" element={<RequirePermission permission="reports:read"><GenericModule title="Reports" endpoint="/reports" /></RequirePermission>} />
        <Route path="/notifications" element={<GenericModule title="Notifications" endpoint="/notifications" />} />
        <Route path="/audit" element={<RequirePermission permission="audit:read"><GenericModule title="Audit Logs" endpoint="/audit" /></RequirePermission>} />
        <Route path="/settings" element={<RequirePermission permission="settings:read"><GenericModule title="System Settings" endpoint="/settings" /></RequirePermission>} />
        <Route path="/unauthorized" element={<Unauthorized />} />
      </Route>
    </Routes>
  );
}
