import { AlertTriangle, Ban, Fingerprint, Network, ShieldAlert, Users } from "lucide-react";

const cards = [
  ["total_alerts", "Total alerts", AlertTriangle],
  ["critical_alerts", "Critical alerts", ShieldAlert],
  ["blocked_transactions", "Blocked tx", Ban],
  ["average_trust_score", "Avg trust", Fingerprint],
  ["suspicious_log_count", "Suspicious logs", Users],
  ["mule_accounts_count", "Mule accounts", Network]
];

export default function StatsCards({ stats }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
      {cards.map(([key, labelText, Icon]) => (
        <div key={key} className="rounded-lg border border-white/10 bg-slate-900/80 p-4 shadow-glow">
          <div className="mb-3 flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase tracking-wide">{labelText}</span>
            <Icon className="h-4 w-4 text-sky-300" />
          </div>
          <p className="text-2xl font-bold text-white">{stats?.[key] ?? "0"}</p>
        </div>
      ))}
    </div>
  );
}

