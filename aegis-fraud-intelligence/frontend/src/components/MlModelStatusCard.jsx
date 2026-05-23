import { useEffect, useState } from "react";
import { BrainCircuit, CircleAlert, ShieldCheck } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import { useAuth } from "../auth/AuthContext";

function StatusPill({ active, label }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${
      active
        ? "bg-emerald-500/15 text-emerald-200 ring-emerald-500/30"
        : "bg-red-500/15 text-red-200 ring-red-500/30"
    }`}>
      {label}: {active ? "Yes" : "No"}
    </span>
  );
}

export default function MlModelStatusCard() {
  const { user } = useAuth();
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      if (!["ANALYST", "ADMIN"].includes(user?.role)) {
        setLoading(false);
        return;
      }
      try {
        const response = await api.get("/api/fraud/health");
        if (!mounted) return;
        setHealth(response.data);
      } catch (err) {
        if (!mounted) return;
        if (err.response?.status === 403) {
          setError("ML status restricted");
        } else {
          setError(apiErrorMessage(err));
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [user?.role]);

  if (!["ANALYST", "ADMIN"].includes(user?.role)) return null;

  return (
    <section className="rounded-lg border border-purple-400/20 bg-slate-900/80 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-purple-500/15 p-2 text-purple-300">
            <BrainCircuit className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-purple-300">XGBoost ML Model</p>
            <h2 className="font-semibold text-white">Model Status</h2>
          </div>
        </div>
        {health?.model_loaded ? <ShieldCheck className="h-5 w-5 text-emerald-300" /> : <CircleAlert className="h-5 w-5 text-amber-300" />}
      </div>

      {loading && <p className="mt-4 text-sm text-slate-400">Checking ML model health...</p>}
      {!loading && error && <p className="mt-4 rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
      {!loading && health && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap gap-2">
            <StatusPill active={health.enabled} label="Enabled" />
            <StatusPill active={health.model_loaded} label="Loaded" />
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-md bg-slate-950/70 p-3">
              <p className="text-xs text-slate-400">Model version</p>
              <p className="mt-1 font-semibold text-white">{health.model_version || "Unknown"}</p>
            </div>
            <div className="rounded-md bg-slate-950/70 p-3">
              <p className="text-xs text-slate-400">Features</p>
              <p className="mt-1 font-semibold text-white">{health.feature_count ?? "N/A"}</p>
            </div>
            <div className="rounded-md bg-slate-950/70 p-3">
              <p className="text-xs text-slate-400">Threshold</p>
              <p className="mt-1 font-semibold text-white">{health.threshold ?? "N/A"}</p>
            </div>
          </div>
          {user?.role === "ADMIN" && health.model_path && (
            <div className="rounded-md bg-slate-950/70 p-3">
              <p className="text-xs text-slate-400">Model path</p>
              <p className="mt-1 break-all text-sm text-slate-200">{health.model_path}</p>
            </div>
          )}
          {health.error && (
            <div className="rounded-md border border-amber-400/30 bg-amber-500/10 p-3 text-sm text-amber-100">
              Fallback active: {health.error}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
