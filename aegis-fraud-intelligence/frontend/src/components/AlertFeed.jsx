import { Link } from "react-router-dom";
import RiskBadge from "./RiskBadge";

export default function AlertFeed({ alerts = [], compact = false }) {
  if (!alerts.length) {
    return <div className="rounded-lg border border-white/10 bg-slate-900/80 p-5 text-sm text-slate-400">No alerts yet.</div>;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-white/10 bg-slate-900/80">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="font-semibold text-white">Live Fraud Alerts</h2>
      </div>
      <div className="divide-y divide-white/10">
        {alerts.slice(0, compact ? 5 : 12).map((alert) => (
          <div key={alert.id} className="grid gap-3 px-5 py-4 md:grid-cols-[1fr_auto_auto] md:items-center">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium text-white">{alert.title}</p>
                {alert.is_case && (
                  <span className="rounded-full bg-purple-500/15 px-2.5 py-1 text-xs font-semibold text-purple-200">
                    {alert.case_priority} Case
                  </span>
                )}
              </div>
              <p className="mt-1 text-xs text-slate-400">
                {alert.customer_name || "Network alert"} - risk {alert.risk_score ?? 0} - {alert.status}
              </p>
            </div>
            <RiskBadge severity={alert.severity} />
            <Link to={`/alerts/${alert.id}`} className="rounded-md bg-sky-500 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-sky-400">
              {alert.is_case ? "Open Case" : "View"}
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
