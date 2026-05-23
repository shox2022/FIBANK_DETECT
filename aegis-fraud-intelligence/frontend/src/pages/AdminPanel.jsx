import { useEffect, useMemo, useState } from "react";
import { BrainCircuit, GlobeLock, RefreshCw, Settings, ShieldCheck, SlidersHorizontal, Users } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import Navbar from "../components/Navbar";
import TrustMeter from "../components/TrustMeter";
import MessageVerificationActivity from "../components/MessageVerificationActivity";

const roleStyles = {
  CUSTOMER: "bg-emerald-500/15 text-emerald-200 ring-emerald-500/30",
  ANALYST: "bg-sky-500/15 text-sky-200 ring-sky-500/30",
  ADMIN: "bg-purple-500/15 text-purple-200 ring-purple-500/30"
};

function RoleBadge({ role }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${roleStyles[role] || roleStyles.CUSTOMER}`}>
      {role || "UNKNOWN"}
    </span>
  );
}

export default function AdminPanel() {
  const [users, setUsers] = useState([]);
  const [rules, setRules] = useState([]);
  const [mlHealth, setMlHealth] = useState(null);
  const [mlFeatures, setMlFeatures] = useState([]);
  const [mlError, setMlError] = useState("");
  const [brandConfig, setBrandConfig] = useState(null);
  const [brandError, setBrandError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    setMlError("");
    setBrandError("");
    try {
      const [usersRes, rulesRes, healthRes, featuresRes, brandConfigRes] = await Promise.allSettled([
        api.get("/api/admin/users"),
        api.get("/api/admin/rules"),
        api.get("/api/fraud/health"),
        api.get("/api/fraud/features"),
        api.get("/api/brand-protection/config")
      ]);
      if (usersRes.status === "fulfilled") setUsers(usersRes.value.data || []);
      if (rulesRes.status === "fulfilled") setRules(rulesRes.value.data || []);
      if (healthRes.status === "fulfilled") setMlHealth(healthRes.value.data);
      if (featuresRes.status === "fulfilled") setMlFeatures(featuresRes.value.data?.feature_names || []);
      if (brandConfigRes.status === "fulfilled") setBrandConfig(brandConfigRes.value.data);
      if (usersRes.status === "rejected") setError(apiErrorMessage(usersRes.reason));
      if (rulesRes.status === "rejected") setError(apiErrorMessage(rulesRes.reason));
      if (healthRes.status === "rejected") setMlError(apiErrorMessage(healthRes.reason));
      if (featuresRes.status === "rejected") setMlError(apiErrorMessage(featuresRes.reason));
      if (brandConfigRes.status === "rejected") setBrandError(apiErrorMessage(brandConfigRes.reason));
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const summary = useMemo(() => {
    const enabledRules = rules.filter((rule) => rule.enabled).length;
    const adminCount = users.filter((user) => user.role === "ADMIN").length;
    return { enabledRules, adminCount };
  }, [rules, users]);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <Navbar />
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm uppercase tracking-wide text-purple-300">Administration</p>
            <h1 className="text-3xl font-bold">AEGIS Control Plane</h1>
          </div>
          <button onClick={load} className="inline-flex items-center gap-2 rounded-md bg-white/10 px-4 py-2 text-sm font-semibold hover:bg-white/15">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        {error && <p className="rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}

        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
            <div className="flex items-center gap-3">
              <Users className="h-5 w-5 text-sky-300" />
              <p className="text-sm text-slate-400">Managed users</p>
            </div>
            <p className="mt-3 text-3xl font-bold">{users.length}</p>
          </div>
          <div className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-5 w-5 text-purple-300" />
              <p className="text-sm text-slate-400">Admin accounts</p>
            </div>
            <p className="mt-3 text-3xl font-bold">{summary.adminCount}</p>
          </div>
          <div className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
            <div className="flex items-center gap-3">
              <SlidersHorizontal className="h-5 w-5 text-emerald-300" />
              <p className="text-sm text-slate-400">Enabled risk rules</p>
            </div>
            <p className="mt-3 text-3xl font-bold">{summary.enabledRules}</p>
          </div>
        </section>

        {loading ? (
          <p className="text-slate-300">Loading admin data...</p>
        ) : (
          <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <section className="rounded-lg border border-white/10 bg-slate-900/80">
              <div className="border-b border-white/10 px-5 py-4">
                <h2 className="font-semibold">Users</h2>
              </div>
              <div className="overflow-auto">
                <table className="w-full min-w-[780px] text-left text-sm">
                  <thead className="bg-slate-950 text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-4 py-3">Name</th>
                      <th className="px-4 py-3">Email</th>
                      <th className="px-4 py-3">Role</th>
                      <th className="px-4 py-3">Trust</th>
                      <th className="px-4 py-3">Account</th>
                      <th className="px-4 py-3">Balance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10 text-slate-300">
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td className="px-4 py-3 font-medium text-white">{user.name}</td>
                        <td className="px-4 py-3">{user.email}</td>
                        <td className="px-4 py-3"><RoleBadge role={user.role} /></td>
                        <td className="px-4 py-3 min-w-[170px]"><TrustMeter score={user.trust_score || 0} compact /></td>
                        <td className="px-4 py-3">{user.account_number || "-"}</td>
                        <td className="px-4 py-3">EUR {Number(user.balance || 0).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-lg border border-white/10 bg-slate-900/80">
              <div className="border-b border-white/10 px-5 py-4">
                <h2 className="font-semibold">Risk Rules</h2>
              </div>
              <div className="divide-y divide-white/10">
                {!rules.length && <p className="p-5 text-sm text-slate-400">No risk rules found.</p>}
                {rules.map((rule) => (
                  <div key={rule.id} className="p-5">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-white">{rule.code}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-400">{rule.description}</p>
                      </div>
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${rule.enabled ? "bg-emerald-500/15 text-emerald-200" : "bg-slate-700 text-slate-300"}`}>
                        {rule.enabled ? "Enabled" : "Disabled"}
                      </span>
                    </div>
                    <p className="mt-3 text-sm text-slate-300">Weight: <span className="font-semibold text-white">{rule.points}</span> points</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}

        <section className="rounded-lg border border-purple-400/20 bg-slate-900/80">
          <div className="border-b border-white/10 px-5 py-4">
            <div className="flex items-center gap-3">
              <BrainCircuit className="h-5 w-5 text-purple-300" />
              <div>
                <p className="text-xs uppercase tracking-wide text-purple-300">XGBoost Model Configuration</p>
                <h2 className="font-semibold">Fraud ML Runtime</h2>
              </div>
            </div>
          </div>
          <div className="grid gap-5 p-5 xl:grid-cols-[0.9fr_1.1fr]">
            <div className="space-y-3">
              {mlError && <p className="rounded-md bg-red-500/10 p-3 text-sm text-red-200">{mlError}</p>}
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Enabled</p>
                  <p className="mt-1 font-semibold">{mlHealth?.enabled ? "Yes" : "No"}</p>
                </div>
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Model loaded</p>
                  <p className="mt-1 font-semibold">{mlHealth?.model_loaded ? "Yes" : "No"}</p>
                </div>
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Version</p>
                  <p className="mt-1 font-semibold">{mlHealth?.model_version || "Unknown"}</p>
                </div>
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Threshold</p>
                  <p className="mt-1 font-semibold">{mlHealth?.threshold ?? "N/A"}</p>
                </div>
              </div>
              <div className="rounded-md bg-slate-950/70 p-3">
                <p className="text-xs text-slate-400">Model path</p>
                <p className="mt-1 break-all text-sm text-slate-200">{mlHealth?.model_path || "Unavailable"}</p>
              </div>
              {mlHealth?.error && (
                <div className="rounded-md border border-amber-400/30 bg-amber-500/10 p-3 text-sm text-amber-100">
                  Fallback status: {mlHealth.error}
                </div>
              )}
            </div>
            <div className="rounded-md border border-white/10 bg-slate-950/70">
              <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                <h3 className="font-semibold">Feature Vector</h3>
                <span className="rounded-full bg-purple-500/15 px-2.5 py-1 text-xs font-semibold text-purple-200">
                  {mlFeatures.length || mlHealth?.feature_count || 0} features
                </span>
              </div>
              <div className="max-h-72 overflow-auto p-4">
                {!mlFeatures.length ? (
                  <p className="text-sm text-slate-400">No feature names returned.</p>
                ) : (
                  <div className="grid gap-2 sm:grid-cols-2">
                    {mlFeatures.map((feature) => (
                      <span key={feature} className="rounded-md bg-slate-900 px-3 py-2 text-xs text-slate-300">
                        {feature}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <MessageVerificationActivity compact />

        <section className="rounded-lg border border-cyan-400/20 bg-slate-900/80 p-5">
          <div className="flex items-start gap-3">
            <div className="rounded-md bg-cyan-500/15 p-2 text-cyan-300">
              <GlobeLock className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs uppercase tracking-wide text-cyan-300">Brand Protection Configuration</p>
              <h2 className="font-semibold">Passive Web Threat Intelligence</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Analyst/admin scans check DNS and public page metadata for Fibank lookalike domains. No exploitation,
                authentication, form submission, or vulnerability testing is performed.
              </p>
              {brandError && <p className="mt-4 rounded-md bg-red-500/10 p-3 text-sm text-red-200">{brandError}</p>}
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Enabled</p>
                  <p className="mt-1 font-semibold">{brandConfig?.enabled ? "Yes" : "No"}</p>
                </div>
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Target domain</p>
                  <p className="mt-1 font-semibold">{brandConfig?.target_domain || "fibank.al"}</p>
                </div>
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Target brand</p>
                  <p className="mt-1 font-semibold">{brandConfig?.target_brand || "fibank"}</p>
                </div>
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Quick default</p>
                  <p className="mt-1 font-semibold">{brandConfig?.quick_default ? "Yes" : "No"}</p>
                </div>
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Max candidates</p>
                  <p className="mt-1 font-semibold">{brandConfig?.max_candidates ?? "300"}</p>
                </div>
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Request timeout</p>
                  <p className="mt-1 font-semibold">{brandConfig?.request_timeout ?? "8"}s</p>
                </div>
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Request delay</p>
                  <p className="mt-1 font-semibold">{brandConfig?.request_delay ?? "0.5"}s</p>
                </div>
                <div className="rounded-md bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Target URL</p>
                  <p className="mt-1 truncate font-semibold">{brandConfig?.target_url || "https://www.fibank.al"}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
          <div className="flex items-start gap-3">
            <Settings className="mt-1 h-5 w-5 text-sky-300" />
            <div>
              <h2 className="font-semibold">System Configuration</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Prototype controls are read-only in Phase 5. Future admin actions can manage model enablement,
                threshold tuning, rule activation, and analyst workflow policy from this panel.
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
