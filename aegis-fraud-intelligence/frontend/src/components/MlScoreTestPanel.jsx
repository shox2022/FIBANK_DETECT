import { useState } from "react";
import { FlaskConical, Send } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import { useAuth } from "../auth/AuthContext";
import MlScorePanel from "./MlScorePanel";

export default function MlScoreTestPanel() {
  const { user } = useAuth();
  const [form, setForm] = useState({
    amount: "5000",
    recipient_is_new: true,
    login_vpn_count: "2",
    trust_score: "30"
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!["ANALYST", "ADMIN"].includes(user?.role)) return null;

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await api.post("/api/fraud/score", {
        transaction: {
          amount: Number(form.amount),
          recipient_is_new: form.recipient_is_new ? 1 : 0,
          login_vpn_count: Number(form.login_vpn_count),
          trust_score: Number(form.trust_score)
        },
        include_explanation: true
      });
      setResult(response.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-purple-400/20 bg-slate-900/80 p-5">
      <div className="flex items-start gap-3">
        <div className="rounded-md bg-sky-500/15 p-2 text-sky-300">
          <FlaskConical className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-sky-300">Direct ML Probe</p>
          <h2 className="font-semibold text-white">Test XGBoost Scoring</h2>
        </div>
      </div>
      <form onSubmit={submit} className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="text-sm text-slate-300">
          Amount
          <input type="number" className="mt-1 w-full rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-white" value={form.amount} onChange={(e) => update("amount", e.target.value)} />
        </label>
        <label className="text-sm text-slate-300">
          Login VPN count
          <input type="number" className="mt-1 w-full rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-white" value={form.login_vpn_count} onChange={(e) => update("login_vpn_count", e.target.value)} />
        </label>
        <label className="text-sm text-slate-300">
          Trust score
          <input type="number" className="mt-1 w-full rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-white" value={form.trust_score} onChange={(e) => update("trust_score", e.target.value)} />
        </label>
        <label className="flex items-center gap-2 self-end text-sm text-slate-300">
          <input type="checkbox" checked={form.recipient_is_new} onChange={(e) => update("recipient_is_new", e.target.checked)} />
          New recipient
        </label>
        <button disabled={loading} className="inline-flex items-center justify-center gap-2 rounded-md bg-purple-500 px-4 py-2 font-semibold text-white hover:bg-purple-400 disabled:opacity-60 sm:col-span-2">
          <Send className="h-4 w-4" />
          {loading ? "Scoring..." : "Score with XGBoost"}
        </button>
      </form>
      {error && <p className="mt-4 rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
      {result && <div className="mt-4"><MlScorePanel result={result} dark /></div>}
    </section>
  );
}
