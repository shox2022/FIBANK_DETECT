const rows = [
  ["Low risk", "ALLOW", "green", "Allow"],
  ["Medium risk", "REQUIRE_2FA", "yellow", "Require 2FA"],
  ["High risk", "HOLD_FOR_REVIEW", "orange", "Hold for Review"],
  ["Critical risk", "BLOCK_AND_ALERT", "red", "Block and Alert"]
];

const colors = {
  green: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
  yellow: "border-yellow-500/30 bg-yellow-500/10 text-yellow-200",
  orange: "border-orange-500/30 bg-orange-500/10 text-orange-200",
  red: "border-red-500/30 bg-red-500/10 text-red-200"
};

export default function AdaptiveFrictionCard() {
  return (
    <section className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
      <h2 className="text-lg font-semibold text-white">Adaptive Friction</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {rows.map(([risk, action, color, label]) => (
          <div key={action} className={`rounded-md border p-3 ${colors[color]}`}>
            <p className="text-sm font-semibold">{risk}</p>
            <p className="mt-1 text-xs opacity-90">{label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

