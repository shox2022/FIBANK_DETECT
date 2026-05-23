import { useEffect, useMemo, useState } from "react";
import { BrainCircuit, GitBranch, ShieldCheck, SlidersHorizontal } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import Navbar from "../components/Navbar";
import RiskBadge from "../components/RiskBadge";

function EnabledBadge({ enabled }) {
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${enabled ? "bg-emerald-500/15 text-emerald-200" : "bg-slate-700 text-slate-300"}`}>
      {enabled ? "Enabled" : "Disabled"}
    </span>
  );
}

export default function RiskTransparency() {
  const [transparency, setTransparency] = useState(null);
  const [rules, setRules] = useState([]);
  const [mlHealth, setMlHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [transparencyRes, rulesRes, mlRes] = await Promise.allSettled([
          api.get("/api/risk/transparency"),
          api.get("/api/risk/rules"),
          api.get("/api/fraud/health")
        ]);
        if (transparencyRes.status === "fulfilled") setTransparency(transparencyRes.value.data);
        if (rulesRes.status === "fulfilled") setRules(rulesRes.value.data || []);
        if (mlRes.status === "fulfilled") setMlHealth(mlRes.value.data);
        if (transparencyRes.status === "rejected") throw transparencyRes.reason;
      } catch (err) {
        setError(apiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const groupedRules = useMemo(() => {
    return rules.reduce((groups, rule) => {
      const category = rule.category || "OTHER";
      groups[category] = [...(groups[category] || []), rule];
      return groups;
    }, {});
  }, [rules]);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <Navbar />
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6">
        <section className="rounded-lg border border-sky-400/20 bg-slate-900/80 p-6">
          <div className="flex items-start gap-3">
            <div className="rounded-md bg-sky-500/15 p-2 text-sky-300">
              <SlidersHorizontal className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm uppercase tracking-wide text-sky-300">Explainable Risk Engine</p>
              <h1 className="mt-1 text-3xl font-bold">Risk Rule Transparency</h1>
              <p className="mt-2 max-w-3xl text-slate-300">Understand how AEGIS combines rules, trust score, adaptive friction, and XGBoost ML scoring.</p>
            </div>
          </div>
        </section>

        {error && <p className="rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
        {loading && <p className="text-slate-300">Loading risk transparency...</p>}

        {transparency && (
          <>
            <section className="grid gap-4 md:grid-cols-4">
              {transparency.risk_levels?.map((level) => (
                <div key={level.severity} className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
                  <div className="flex items-center justify-between gap-3">
                    <RiskBadge severity={level.severity} />
                    <span className="text-sm font-semibold text-slate-300">{level.range}</span>
                  </div>
                  <p className="mt-4 text-sm text-slate-400">Default action</p>
                  <p className="mt-1 font-semibold text-white">{level.action}</p>
                </div>
              ))}
            </section>

            <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
              <section className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
                <div className="flex items-center gap-3">
                  <ShieldCheck className="h-5 w-5 text-emerald-300" />
                  <h2 className="font-semibold">Adaptive Friction</h2>
                </div>
                <div className="mt-4 space-y-3">
                  {transparency.adaptive_friction?.map((item) => (
                    <div key={item.action} className="rounded-md bg-slate-950/70 p-4">
                      <p className="font-semibold text-white">{item.action}</p>
                      <p className="mt-1 text-sm leading-6 text-slate-400">{item.description}</p>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-lg border border-purple-400/20 bg-slate-900/80 p-5">
                <div className="flex items-center gap-3">
                  <BrainCircuit className="h-5 w-5 text-purple-300" />
                  <h2 className="font-semibold">ML Integration</h2>
                </div>
                <div className="mt-4 space-y-3 text-sm leading-6 text-slate-300">
                  <p>{transparency.ml_integration?.description}</p>
                  <p><span className="font-semibold text-white">Combination:</span> {transparency.ml_integration?.combination}</p>
                  <p><span className="font-semibold text-white">Fallback:</span> {transparency.ml_integration?.fallback}</p>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-md bg-slate-950/70 p-3">
                      <p className="text-xs text-slate-400">Model</p>
                      <p className="mt-1 font-semibold text-white">{mlHealth?.model_version || "Unknown"}</p>
                    </div>
                    <div className="rounded-md bg-slate-950/70 p-3">
                      <p className="text-xs text-slate-400">Loaded</p>
                      <p className="mt-1 font-semibold text-white">{mlHealth?.model_loaded ? "Yes" : "No"}</p>
                    </div>
                    <div className="rounded-md bg-slate-950/70 p-3">
                      <p className="text-xs text-slate-400">Enabled</p>
                      <p className="mt-1 font-semibold text-white">{mlHealth?.enabled ? "Yes" : "No"}</p>
                    </div>
                  </div>
                </div>
              </section>
            </div>

            <section className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
              <div className="flex items-center gap-3">
                <GitBranch className="h-5 w-5 text-sky-300" />
                <h2 className="font-semibold">Trust Score Impact</h2>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                {transparency.trust_score_impacts?.map((item) => (
                  <div key={item} className="rounded-md bg-slate-950/70 p-4 text-sm text-slate-300">{item}</div>
                ))}
              </div>
            </section>

            <section className="rounded-lg border border-white/10 bg-slate-900/80">
              <div className="border-b border-white/10 px-5 py-4">
                <h2 className="font-semibold">Risk Rules</h2>
              </div>
              <div className="space-y-6 p-5">
                {Object.entries(groupedRules).map(([category, categoryRules]) => (
                  <div key={category}>
                    <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-sky-300">{category}</h3>
                    <div className="overflow-auto rounded-md border border-white/10">
                      <table className="w-full min-w-[760px] text-left text-sm">
                        <thead className="bg-slate-950 text-xs uppercase text-slate-400">
                          <tr>
                            <th className="px-4 py-3">Code</th>
                            <th className="px-4 py-3">Description</th>
                            <th className="px-4 py-3">Points</th>
                            <th className="px-4 py-3">State</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/10 text-slate-300">
                          {categoryRules.map((rule) => (
                            <tr key={rule.id}>
                              <td className="px-4 py-3 font-semibold text-white">{rule.code}</td>
                              <td className="px-4 py-3">{rule.description}</td>
                              <td className="px-4 py-3">{rule.points}</td>
                              <td className="px-4 py-3"><EnabledBadge enabled={rule.enabled} /></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
