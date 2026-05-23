import { Activity, Bug, Globe2, KeyRound, Network, ShieldCheck, Zap } from "lucide-react";

const actions = [
  ["normal-login", "Normal login from Albania", ShieldCheck],
  ["germany-vpn", "Login with VPN from Germany", Globe2],
  ["impossible-travel", "Impossible travel Albania to Germany", Zap],
  ["token-theft", "Token theft simulation", KeyRound],
  ["high-value-transfer", "High-value transfer", Activity],
  ["sql-injection", "SQL injection attempt", Bug],
  ["mule-ring", "Mule ring simulation", Network]
];

export default function DemoAttackPanel({ onRun, loadingAction }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">Demo Attack Panel</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {actions.map(([key, label, Icon]) => (
          <button
            key={key}
            onClick={() => onRun(key)}
            disabled={Boolean(loadingAction)}
            className="flex items-center gap-3 rounded-md border border-slate-200 px-3 py-3 text-left text-sm font-semibold text-slate-700 hover:border-sky-300 hover:bg-sky-50 disabled:opacity-60"
          >
            <Icon className="h-4 w-4 text-sky-600" />
            {loadingAction === key ? "Running..." : label}
          </button>
        ))}
      </div>
    </section>
  );
}

