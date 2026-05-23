import { useEffect, useState } from "react";
import { MailWarning, RefreshCw } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import { useAuth } from "../auth/AuthContext";

const resultStyles = {
  VERIFIED_OFFICIAL: "bg-emerald-500/15 text-emerald-200 ring-emerald-500/30",
  POSSIBLE_PHISHING: "bg-red-500/15 text-red-200 ring-red-500/30",
  SUSPICIOUS: "bg-orange-500/15 text-orange-200 ring-orange-500/30",
  UNKNOWN: "bg-slate-500/15 text-slate-200 ring-slate-500/30"
};

function parseReasons(value) {
  if (Array.isArray(value)) return value;
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [String(value)];
  } catch {
    return [String(value)];
  }
}

export default function MessageVerificationActivity({ compact = false }) {
  const { user } = useAuth();
  const [checks, setChecks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    if (!["ANALYST", "ADMIN"].includes(user?.role)) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/api/messages/checks");
      setChecks(response.data || []);
    } catch (err) {
      if (err.response?.status !== 403) setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [user?.role]);

  if (!["ANALYST", "ADMIN"].includes(user?.role)) return null;

  return (
    <section className="rounded-lg border border-white/10 bg-slate-900/80">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div className="flex items-center gap-3">
          <MailWarning className="h-5 w-5 text-purple-300" />
          <div>
            <p className="text-xs uppercase tracking-wide text-purple-300">Communication Trust</p>
            <h2 className="font-semibold text-white">Message Verification Activity</h2>
          </div>
        </div>
        <button onClick={load} className="rounded-md bg-white/10 p-2 text-slate-200 hover:bg-white/15" aria-label="Refresh message checks">
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>
      {loading && <p className="p-5 text-sm text-slate-400">Loading message checks...</p>}
      {error && <p className="m-5 rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
      {!loading && !error && !checks.length && <p className="p-5 text-sm text-slate-400">No message checks reported yet.</p>}
      <div className="divide-y divide-white/10">
        {checks.slice(0, compact ? 5 : 10).map((check) => {
          const reasons = parseReasons(check.reasons);
          return (
            <div key={check.id} className="grid gap-3 px-5 py-4 lg:grid-cols-[auto_1fr_auto] lg:items-start">
              <div>
                <p className="text-xs text-slate-400">User</p>
                <p className="font-semibold text-white">#{check.user_id}</p>
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${resultStyles[check.result] || resultStyles.UNKNOWN}`}>
                    {check.result}
                  </span>
                  <span className="text-sm text-slate-300">Risk {check.risk_score}</span>
                </div>
                <p className="mt-2 line-clamp-2 text-sm text-slate-400">{reasons.join(" ") || check.recommendation}</p>
              </div>
              <p className="text-xs text-slate-500">{check.created_at ? new Date(check.created_at).toLocaleString() : "-"}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
