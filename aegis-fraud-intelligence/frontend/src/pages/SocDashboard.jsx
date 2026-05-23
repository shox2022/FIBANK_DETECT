import { useEffect, useMemo, useState } from "react";
import { ExternalLink, RefreshCw, SlidersHorizontal } from "lucide-react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api, { apiErrorMessage } from "../api";
import Navbar from "../components/Navbar";
import StatsCards from "../components/StatsCards";
import AlertFeed from "../components/AlertFeed";
import LogViewer from "../components/LogViewer";
import MuleGraph from "../components/MuleGraph";
import AdaptiveFrictionCard from "../components/AdaptiveFrictionCard";
import PrivacyPanel from "../components/PrivacyPanel";
import MlModelStatusCard from "../components/MlModelStatusCard";
import MlScoreTestPanel from "../components/MlScoreTestPanel";
import MessageVerificationActivity from "../components/MessageVerificationActivity";
import BrandProtectionSummaryCard from "../components/BrandProtectionSummaryCard";

const severityColors = {
  LOW: "#34d399",
  MEDIUM: "#facc15",
  HIGH: "#fb923c",
  CRITICAL: "#ef4444"
};

export default function SocDashboard() {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [logs, setLogs] = useState([]);
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [statsRes, alertsRes, logsRes, graphRes] = await Promise.all([
        api.get("/api/dashboard/stats"),
        api.get("/api/alerts"),
        api.get("/api/logs"),
        api.get("/api/graph/mule-network")
      ]);
      setStats(statsRes.data);
      setAlerts(alertsRes.data || []);
      setLogs(logsRes.data || []);
      setGraph(graphRes.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const chartData = useMemo(() => {
    const counts = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
    alerts.forEach((alert) => {
      counts[alert.severity] = (counts[alert.severity] || 0) + 1;
    });
    return Object.entries(counts).map(([severity, count]) => ({ severity, count }));
  }, [alerts]);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <Navbar />
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm uppercase tracking-wide text-sky-300">Security Operations Center</p>
            <h1 className="text-3xl font-bold">AEGIS Risk Intelligence</h1>
          </div>
          <button onClick={load} className="inline-flex items-center gap-2 rounded-md bg-white/10 px-4 py-2 text-sm font-semibold hover:bg-white/15">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
        {error && <p className="rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
        {loading ? <p className="text-slate-300">Loading SOC telemetry...</p> : <StatsCards stats={stats} />}
        <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
          <AlertFeed alerts={alerts} />
          <section className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
            <h2 className="font-semibold text-white">Risk Distribution</h2>
            <div className="mt-4 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid stroke="#1e293b" />
                  <XAxis dataKey="severity" stroke="#94a3b8" />
                  <YAxis allowDecimals={false} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", color: "#fff" }} />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {chartData.map((entry) => <Cell key={entry.severity} fill={severityColors[entry.severity]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>
        <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <MlModelStatusCard />
          <MlScoreTestPanel />
        </div>
        <section className="rounded-lg border border-sky-400/20 bg-slate-900/80 p-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="rounded-md bg-sky-500/15 p-2 text-sky-300">
                <SlidersHorizontal className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-sky-300">Risk Transparency</p>
                <h2 className="font-semibold">Explainable Risk Rules</h2>
                <p className="mt-1 text-sm text-slate-400">View how AEGIS calculates risk and applies adaptive friction.</p>
              </div>
            </div>
            <Link to="/risk-transparency" className="inline-flex items-center gap-2 rounded-md bg-sky-500 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400">
              Open Transparency <ExternalLink className="h-4 w-4" />
            </Link>
          </div>
        </section>
        <section className="rounded-lg border border-purple-400/20 bg-slate-900/80 p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-purple-300">Investigation Cases</p>
              <h2 className="font-semibold">Recent High-Priority Alerts</h2>
            </div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {alerts.filter((alert) => alert.is_case).slice(0, 4).map((alert) => (
              <Link key={alert.id} to={`/alerts/${alert.id}`} className="rounded-md border border-white/10 bg-slate-950/70 p-4 hover:border-purple-400/40">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-white">{alert.title}</p>
                    <p className="mt-1 text-xs text-slate-400">{alert.customer_name || "Network alert"} - {alert.status}</p>
                  </div>
                  <span className="rounded-full bg-purple-500/15 px-2.5 py-1 text-xs font-semibold text-purple-200">
                    {alert.case_priority}
                  </span>
                </div>
              </Link>
            ))}
            {!alerts.some((alert) => alert.is_case) && <p className="text-sm text-slate-400">No HIGH or CRITICAL investigation cases are currently open.</p>}
          </div>
        </section>
        <BrandProtectionSummaryCard />
        <MessageVerificationActivity />
        <section className="rounded-lg border border-white/10 bg-slate-900/80">
          <div className="border-b border-white/10 px-5 py-4">
            <h2 className="font-semibold">Recent Transactions</h2>
          </div>
          <div className="overflow-auto">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="bg-slate-950 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Account</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Risk</th>
                  <th className="px-4 py-3">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10 text-slate-300">
                {(stats?.recent_transactions || []).map((tx) => (
                  <tr key={tx.id}>
                    <td className="px-4 py-3">{tx.id}</td>
                    <td className="px-4 py-3">{tx.to_account}</td>
                    <td className="px-4 py-3">EUR {Number(tx.amount || 0).toLocaleString()}</td>
                    <td className="px-4 py-3">{tx.status}</td>
                    <td className="px-4 py-3">{tx.risk_score}</td>
                    <td className="px-4 py-3">{tx.created_at ? new Date(tx.created_at).toLocaleString() : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <MuleGraph graph={graph} />
        <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
          <LogViewer logs={logs} />
          <div className="space-y-6">
            <AdaptiveFrictionCard />
            <PrivacyPanel />
          </div>
        </div>
      </div>
    </main>
  );
}
