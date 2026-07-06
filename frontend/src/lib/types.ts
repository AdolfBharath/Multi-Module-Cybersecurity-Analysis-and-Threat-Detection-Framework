export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type AlertItem = {
  id?: number;
  title: string;
  severity: Severity;
  status?: string;
  source: string;
  confidence?: number;
  description?: string;
  created_at?: string;
};

export type DashboardMetrics = {
  total_logs: number;
  critical_alerts: number;
  incidents: number;
  high_threats: number;
  medium_threats: number;
  low_threats: number;
  network_status: string;
  cpu: number;
  memory: number;
  disk: number;
  todays_attacks: number;
  weekly_trend: Array<Record<string, number | string>>;
  monthly_trend: Array<Record<string, number | string>>;
  attack_timeline: Array<Record<string, string>>;
  alert_timeline: Array<Record<string, number | string>>;
  recent_activity: Array<Record<string, string>>;
  live_feed: AlertItem[];
  threat_map: Array<Record<string, number | string>>;
  top_attack_sources: Array<Record<string, number | string>>;
  mitre_matrix: Array<Record<string, number | string>>;
};

export type ModuleItem = {
  id?: number;
  title?: string;
  severity?: Severity;
  status?: string;
  description?: string;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
};

