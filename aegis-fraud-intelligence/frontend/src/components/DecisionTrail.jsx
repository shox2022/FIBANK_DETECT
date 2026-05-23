import { useEffect, useState } from "react";
import { CheckCircle2, CircleDot, FileText, RotateCcw } from "lucide-react";
import api, { apiErrorMessage } from "../api";

const iconByAction = {
  STATUS_CHANGE: RotateCcw,
  MARKED_FALSE_POSITIVE: CheckCircle2,
  REVIEW_COMPLETED: CheckCircle2,
  NOTE: FileText
};

export default function DecisionTrail({ alertId, refreshKey = 0 }) {
  const [trail, setTrail] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function load() {
      if (!alertId) return;
      setLoading(true);
      setError("");
      try {
        const response = await api.get(`/api/alerts/${alertId}/decision-trail`);
        if (mounted) setTrail(response.data || []);
      } catch (err) {
        if (mounted) setError(apiErrorMessage(err));
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [alertId, refreshKey]);

  return (
    <section className="rounded-lg border border-white/10 bg-slate-900/80">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="font-semibold text-white">Decision Trail</h2>
        <p className="mt-1 text-sm text-slate-400">Chronological record of analyst actions on this case.</p>
      </div>
      {error && <p className="m-5 rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
      {loading && <p className="p-5 text-sm text-slate-400">Loading decision trail...</p>}
      {!loading && !trail.length && <p className="p-5 text-sm text-slate-400">No decision trail entries yet.</p>}
      <div className="space-y-4 p-5">
        {trail.map((item) => {
          const Icon = iconByAction[item.action_type] || CircleDot;
          return (
            <article key={item.id} className="flex gap-3">
              <div className="mt-1 rounded-full bg-slate-950 p-2 text-sky-300">
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1 rounded-md bg-slate-950/70 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-white/10 px-2.5 py-1 text-xs font-semibold text-slate-200">{item.action_type}</span>
                  {item.old_status && item.new_status && (
                    <span className="text-xs text-slate-400">{item.old_status} to {item.new_status}</span>
                  )}
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-300">{item.note}</p>
                <p className="mt-2 text-xs text-slate-500">
                  {item.analyst_name || `Analyst #${item.analyst_user_id}`} - {item.created_at ? new Date(item.created_at).toLocaleString() : "-"}
                </p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
