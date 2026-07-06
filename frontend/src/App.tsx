import { Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "./components/Shell";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { Logs } from "./pages/Logs";
import { Detection } from "./pages/Detection";
import { Incidents } from "./pages/Incidents";
import { GenericModule } from "./pages/GenericModule";
import { ThreatIntel } from "./pages/ThreatIntel";

function Protected() {
  return localStorage.getItem("cybershield_token") ? <Shell /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Protected />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/detection" element={<Detection />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="/intel" element={<ThreatIntel />} />
        <Route path="/anomaly" element={<GenericModule title="Anomaly Detection" endpoint="/anomaly" />} />
        <Route path="/network" element={<GenericModule title="Network Monitoring" endpoint="/network" />} />
        <Route path="/malware" element={<GenericModule title="Malware Analysis" endpoint="/malware" />} />
        <Route path="/vulnerabilities" element={<GenericModule title="Vulnerability Scanner" endpoint="/vulnerabilities" />} />
        <Route path="/reports" element={<GenericModule title="Reports" endpoint="/reports" />} />
        <Route path="/notifications" element={<GenericModule title="Notifications" endpoint="/notifications" />} />
        <Route path="/audit" element={<GenericModule title="Audit Logs" endpoint="/audit" />} />
        <Route path="/settings" element={<GenericModule title="System Settings" endpoint="/settings" />} />
      </Route>
    </Routes>
  );
}

