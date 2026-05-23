import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api, { apiErrorMessage } from "../api";
import Navbar from "../components/Navbar";
import RiskBadge from "../components/RiskBadge";
import IncidentReportModal from "../components/IncidentReportModal";

const statuses = ["OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"];

export default function AlertDetails() {
  const { alertId } = useParams();
  const [alert, setAlert] = useState(null);
  const [status, setStatus] = useState("OPEN");
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const response = await api.get(`/api/alerts/${alertId}`);
      setAlert(response.data);
      setStatus(response.data.status || "OPEN");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [alertId]);

  async function updateStatus(nextStatus) {
    setStatus(nextStatus);
    try {
      const response = await api.patch(`/api/alerts/${alertId}/status`, { status: nextStatus });
      setAlert(response.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <Navbar />
      <div className="mx-auto max-w-5xl px-4 py-6">
        {loading && <p className="text-slate-300">Loading alert...</p>}
        {error && <p className="rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
        {alert && (
          <section className="rounded-lg border border-white/10 bg-slate-900 p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-wide text-sky-300">{alert.alert_type}</p>
                <h1 className="mt-2 text-3xl font-bold">{alert.title}</h1>
                <p className="mt-2 text-slate-400">{alert.customer_name || "Network-level alert"} · trust {alert.trust_score ?? "N/A"}</p>
              </div>
              <RiskBadge severity={alert.severity} />
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <div className="rounded-md bg-slate-950 p-4">
                <p className="text-xs text-slate-400">Risk score</p>
                <p className="text-3xl font-bold">{alert.risk_score}</p>
              </div>
              <div className="rounded-md bg-slate-950 p-4">
                <p className="text-xs text-slate-400">Status</p>
                <select value={status} onChange={(e) => updateStatus(e.target.value)} className="mt-2 w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-white">
                  {statuses.map((item) => <option key={item}>{item}</option>)}
                </select>
              </div>
              <div className="rounded-md bg-slate-950 p-4">
                <p className="text-xs text-slate-400">Created</p>
                <p className="mt-2 font-semibold">{alert.created_at ? new Date(alert.created_at).toLocaleString() : "-"}</p>
              </div>
            </div>
            <section className="mt-6">
              <h2 className="font-semibold">Explanation</h2>
              <p className="mt-2 leading-7 text-slate-300">{alert.explanation}</p>
            </section>
            <section className="mt-6 rounded-md border border-sky-500/20 bg-sky-500/10 p-4">
              <h2 className="font-semibold text-sky-100">Recommended Action</h2>
              <p className="mt-2 text-sky-100">{alert.recommended_action}</p>
            </section>
            <button onClick={() => setModalOpen(true)} className="mt-6 rounded-md bg-sky-500 px-4 py-2 font-semibold text-white hover:bg-sky-400">
              Generate Incident Report
            </button>
          </section>
        )}
      </div>
      {modalOpen && <IncidentReportModal alertId={alertId} onClose={() => setModalOpen(false)} />}
    </main>
  );
}

