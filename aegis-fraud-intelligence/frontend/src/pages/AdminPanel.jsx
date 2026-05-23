import { useEffect, useMemo, useState } from "react";
import { RefreshCw, Settings, ShieldCheck, SlidersHorizontal, Users } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import Navbar from "../components/Navbar";
import TrustMeter from "../components/TrustMeter";

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [usersRes, rulesRes] = await Promise.all([
        api.get("/api/admin/users"),
        api.get("/api/admin/rules")
      ]);
      setUsers(usersRes.data || []);
      setRules(rulesRes.data || []);
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
