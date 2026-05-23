import { Copy, X } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import { useEffect, useState } from "react";
import RiskBadge from "./RiskBadge";

export default function IncidentReportModal({ alertId, onClose }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  async function loadReport() {
    setLoading(true);
    setError("");
    try {
      const response = await api.get(`/api/alerts/${alertId}/incident-report`);
      setReport(response.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport();
  }, [alertId]);

  async function copyReport() {
    await navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-auto rounded-lg border border-white/10 bg-slate-900 p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-sky-300">Investigation Report</p>
            <h2 className="mt-1 text-2xl font-bold text-white">AEGIS Incident Report</h2>
          </div>
          <button onClick={onClose} className="rounded-md bg-white/10 p-2 text-white hover:bg-white/15" aria-label="Close report">
            <X className="h-5 w-5" />
          </button>
        </div>

        {!report && !loading && (
          <button onClick={loadReport} className="mt-6 rounded-md bg-sky-500 px-4 py-2 font-semibold text-white hover:bg-sky-400">
            Try Again
          </button>
        )}
        {loading && <p className="mt-6 text-slate-300">Generating report...</p>}
        {error && <p className="mt-6 rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}

        {report && (
          <div className="mt-6 space-y-5">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-md bg-slate-950/70 p-3">
                <p className="text-xs text-slate-400">Incident ID</p>
                <p className="font-semibold text-white">{report.incident_id}</p>
              </div>
              <div className="rounded-md bg-slate-950/70 p-3">
                <p className="text-xs text-slate-400">Severity</p>
                <div className="mt-1"><RiskBadge severity={report.severity} /></div>
              </div>
              <div className="rounded-md bg-slate-950/70 p-3">
                <p className="text-xs text-slate-400">Risk / Trust</p>
                <p className="font-semibold text-white">{report.risk_score} / {report.trust_score ?? "N/A"}</p>
              </div>
            </div>
            <section>
              <h3 className="font-semibold text-white">Explanation</h3>
              <p className="mt-2 text-sm leading-6 text-slate-300">{report.explanation}</p>
            </section>
            <section>
              <h3 className="font-semibold text-white">Key Risk Indicators</h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {(report.key_risk_indicators || []).map((item) => (
                  <span key={item} className="rounded-full bg-red-500/10 px-3 py-1 text-xs text-red-200">{item}</span>
                ))}
              </div>
            </section>
            <section>
              <h3 className="font-semibold text-white">Timeline Summary</h3>
              <ul className="mt-2 space-y-2 text-sm text-slate-300">
                {(report.timeline_summary || []).map((item) => <li key={item}>{item}</li>)}
              </ul>
            </section>
            <section className="rounded-md border border-sky-500/20 bg-sky-500/10 p-4">
              <h3 className="font-semibold text-sky-100">Recommended Action</h3>
              <p className="mt-2 text-sm text-sky-100">{report.recommended_action}</p>
            </section>
            <button onClick={copyReport} className="inline-flex items-center gap-2 rounded-md bg-white px-4 py-2 font-semibold text-slate-950 hover:bg-slate-200">
              <Copy className="h-4 w-4" />
              {copied ? "Copied" : "Copy report"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
