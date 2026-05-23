function label(score) {
  if (score >= 80) return ["Trusted", "bg-emerald-400"];
  if (score >= 60) return ["Normal", "bg-sky-400"];
  if (score >= 40) return ["Caution", "bg-yellow-400"];
  if (score >= 20) return ["High Risk", "bg-orange-500"];
  return ["Critical", "bg-red-500"];
}

export default function TrustMeter({ score = 0, dark = false, compact = false }) {
  const value = Math.max(0, Math.min(100, Number(score) || 0));
  const [status, color] = label(value);
  return (
    <div className={dark ? "text-slate-100" : "text-slate-900"}>
      <div className="mb-2 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide opacity-70">Trust score</p>
          <p className={`${compact ? "text-lg" : "text-3xl"} font-bold`}>{value}</p>
        </div>
        <span className="text-sm font-semibold">{status}</span>
      </div>
      <div className={`${compact ? "h-2" : "h-3"} overflow-hidden rounded-full bg-slate-700/30`}>
        <div className={`h-full ${color}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
