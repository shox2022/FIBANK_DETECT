const styles = {
  LOW: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
  MEDIUM: "bg-yellow-500/15 text-yellow-200 ring-yellow-500/30",
  HIGH: "bg-orange-500/15 text-orange-200 ring-orange-500/30",
  CRITICAL: "bg-red-500/15 text-red-200 ring-red-500/30"
};

export default function RiskBadge({ severity = "LOW" }) {
  const normalized = severity || "LOW";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${styles[normalized] || styles.LOW}`}>
      {normalized}
    </span>
  );
}

