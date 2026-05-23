import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api, { apiErrorMessage } from "../api";
import Navbar from "../components/Navbar";
import StatsCards from "../components/StatsCards";
import AlertFeed from "../components/AlertFeed";
import LogViewer from "../components/LogViewer";
import MuleGraph from "../components/MuleGraph";
import AdaptiveFrictionCard from "../components/AdaptiveFrictionCard";
import PrivacyPanel from "../components/PrivacyPanel";

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
        <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
          <MuleGraph graph={graph} />
          <LogViewer logs={logs} />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <AdaptiveFrictionCard />
          <PrivacyPanel />
        </div>
      </div>
    </main>
  );
}
