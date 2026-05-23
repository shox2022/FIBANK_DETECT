import { useEffect, useState } from "react";
import { ExternalLink, GlobeLock } from "lucide-react";
import { Link } from "react-router-dom";
import api, { apiErrorMessage } from "../api";
import { useAuth } from "../auth/AuthContext";

export default function BrandProtectionSummaryCard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      if (!["ANALYST", "ADMIN"].includes(user?.role)) return;
      try {
        const response = await api.get("/api/brand-protection/summary");
        if (mounted) setSummary(response.data);
      } catch (err) {
        if (mounted && err.response?.status !== 403) setError(apiErrorMessage(err));
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [user?.role]);

  if (!["ANALYST", "ADMIN"].includes(user?.role)) return null;

  return (
    <section className="rounded-lg border border-cyan-400/20 bg-slate-900/80 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-cyan-500/15 p-2 text-cyan-300">
            <GlobeLock className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-cyan-300">Brand Protection</p>
            <h2 className="font-semibold text-white">Lookalike Domain Watch</h2>
          </div>
        </div>
        <Link to="/brand-protection" className="inline-flex items-center gap-1 rounded-md bg-cyan-500 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-300">
          Open <ExternalLink className="h-3.5 w-3.5" />
        </Link>
      </div>
      {error && <p className="mt-4 rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
      {!error && !summary?.latest_scan_id && (
        <p className="mt-4 text-sm text-slate-400">No brand scan has been run yet.</p>
      )}
      {summary?.latest_scan_id && (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <div className="rounded-md bg-slate-950/70 p-3">
            <p className="text-xs text-slate-400">High risk</p>
            <p className="text-2xl font-bold text-red-200">{summary.high_count}</p>
          </div>
          <div className="rounded-md bg-slate-950/70 p-3">
            <p className="text-xs text-slate-400">Medium risk</p>
            <p className="text-2xl font-bold text-orange-200">{summary.medium_count}</p>
          </div>
          <div className="rounded-md bg-slate-950/70 p-3">
            <p className="text-xs text-slate-400">Latest scan</p>
            <p className="mt-1 text-sm font-semibold text-white">{summary.latest_scan_time ? new Date(summary.latest_scan_time).toLocaleString() : "-"}</p>
          </div>
        </div>
      )}
    </section>
  );
}
