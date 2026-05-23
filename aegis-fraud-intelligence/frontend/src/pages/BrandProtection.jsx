import { useEffect, useState } from "react";
import { GlobeLock, Loader2, RefreshCw, ShieldAlert } from "lucide-react";
import api from "../api";
import Navbar from "../components/Navbar";

const riskStyles = {
  HIGH: "bg-red-500/15 text-red-200 ring-red-500/30",
  MEDIUM: "bg-orange-500/15 text-orange-200 ring-orange-500/30",
  LOW: "bg-yellow-500/15 text-yellow-200 ring-yellow-500/30",
  NONE: "bg-emerald-500/15 text-emerald-200 ring-emerald-500/30",
};

function RiskPill({ level }) {
  const normalized = level || "NONE";

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${
        riskStyles[normalized] || riskStyles.NONE
      }`}
    >
      {normalized}
    </span>
  );
}

function SummaryCards({ scan }) {
  const cards = [
    ["Status", scan?.status || "No scan"],
    ["Candidates", scan?.total_candidates ?? 0],
    ["Live domains", scan?.live_domains_count ?? 0],
    ["High risk", scan?.high_count ?? 0],
    ["Medium risk", scan?.medium_count ?? 0],
    ["Low risk", scan?.low_count ?? 0],
  ];

  return (
    <section className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
      {cards.map(([label, value]) => (
        <div
          key={label}
          className="rounded-lg border border-white/10 bg-slate-900/80 p-4"
        >
          <p className="text-xs uppercase tracking-wide text-slate-400">
            {label}
          </p>
          <p className="mt-2 text-2xl font-bold text-white">{value}</p>
        </div>
      ))}
    </section>
  );
}

function brandScanErrorMessage(error) {
  if (
    error?.code === "ECONNABORTED" ||
    error?.message?.toLowerCase().includes("timeout")
  ) {
    return "Brand scan timed out. The backend is running, but the scan may take longer than expected. Try a smaller candidate limit.";
  }

  if (error?.response?.status === 403) {
    return "You are not authorized to run brand protection scans.";
  }

  if (error?.response?.status === 401) {
    return "Your session expired. Please log in again.";
  }

  if (error?.response?.status >= 500) {
    return (
      error?.response?.data?.detail ||
      "Brand scan failed on the server. Try again with a smaller candidate limit."
    );
  }

  if (error?.response?.data?.detail) {
    return error.response.data.detail;
  }

  if (!error?.response) {
    return "Brand scan request failed or was interrupted. The backend may still be running; try again with fewer candidates.";
  }

  return "Brand scan failed. Please try again.";
}

function brandDataLoadErrorMessage(error) {
  if (error?.response?.status === 403) {
    return "You are not authorized to view brand protection data.";
  }

  if (error?.response?.status === 401) {
    return "Your session expired. Please log in again.";
  }

  if (error?.response?.data?.detail) {
    return error.response.data.detail;
  }

  return "Could not load brand protection data. Please refresh the page.";
}

export default function BrandProtection() {
  const [runs, setRuns] = useState([]);
  const [activeScan, setActiveScan] = useState(null);
  const [maxCandidates, setMaxCandidates] = useState(30);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);

    try {
      const [latestRes, runsRes] = await Promise.all([
        api.get("/api/brand-protection/latest"),
        api.get("/api/brand-protection/runs"),
      ]);

      setRuns(runsRes.data || []);
      setActiveScan(latestRes.data?.id ? latestRes.data : null);

      // Clear stale errors once the page data loads successfully.
      setError("");
    } catch (err) {
      console.error("Failed to load brand protection data:", err);
      setError(brandDataLoadErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function runScan() {
    setScanning(true);
    setError("");

    try {
      const safeMaxCandidates = Math.min(
        Math.max(Number(maxCandidates) || 30, 10),
        300
      );

      const response = await api.post(
        "/api/brand-protection/scan",
        {
          quick: true,
          max_candidates: safeMaxCandidates,
        },
        {
          // Brand protection performs DNS checks and passive page metadata collection,
          // so this endpoint needs more time than normal dashboard requests.
          timeout: 120000,
        }
      );

      setActiveScan(response.data);
      setError("");

      try {
        await load();
      } catch (refreshError) {
        console.error("Brand scan completed, but refresh failed:", refreshError);
      }
    } catch (err) {
      console.error("Brand scan failed:", err);
      setError(brandScanErrorMessage(err));
    } finally {
      setScanning(false);
    }
  }

  async function loadRun(scanId) {
    setError("");

    try {
      const response = await api.get(`/api/brand-protection/runs/${scanId}`);
      setActiveScan(response.data);
      setError("");
    } catch (err) {
      console.error("Failed to load brand scan run:", err);
      setError(brandDataLoadErrorMessage(err));
    }
  }

  const findings = activeScan?.findings || [];

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6">
        <section className="rounded-lg border border-cyan-400/20 bg-slate-900/80 p-6">
          <div className="flex items-start gap-3">
            <div className="rounded-md bg-cyan-500/15 p-2 text-cyan-300">
              <GlobeLock className="h-6 w-6" />
            </div>

            <div>
              <p className="text-sm uppercase tracking-wide text-cyan-300">
                Passive Web Threat Intelligence
              </p>
              <h1 className="mt-1 text-3xl font-bold">
                Brand Protection Intelligence
              </h1>
              <p className="mt-2 max-w-3xl text-slate-300">
                Detect possible lookalike domains and phishing pages
                impersonating Fibank.
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-amber-400/30 bg-amber-500/10 p-4 text-amber-100">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-5 w-5" />
            <p className="text-sm leading-6">
              This module performs passive defensive checks only. It does not
              exploit, attack, authenticate, submit forms, or bypass any
              website.
            </p>
          </div>
        </section>

        {error && (
          <p className="rounded-md bg-red-500/10 p-3 text-sm text-red-200">
            {error}
          </p>
        )}

        <section className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="font-semibold">Scan Controls</h2>
              <p className="mt-1 text-sm text-slate-400">
                Quick mode checks targeted Fibank-like domains only using DNS
                and page metadata.
              </p>
            </div>

            <div className="flex flex-wrap items-end gap-3">
              <label className="text-sm text-slate-300">
                Max candidates
                <input
                  type="number"
                  min="10"
                  max="300"
                  className="mt-1 w-36 rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-white"
                  value={maxCandidates}
                  onChange={(event) => setMaxCandidates(event.target.value)}
                />
              </label>

              <button
                onClick={runScan}
                disabled={scanning}
                className="inline-flex items-center gap-2 rounded-md bg-cyan-500 px-4 py-2 font-semibold text-slate-950 hover:bg-cyan-300 disabled:opacity-60"
              >
                {scanning ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                {scanning ? "Scanning..." : "Run Quick Brand Scan"}
              </button>

              <p className="w-full text-xs text-slate-400">
                Brand scans can take several seconds because they perform DNS
                checks and passive page metadata collection. For demos, keep max
                candidates around 30.
              </p>
            </div>
          </div>
        </section>

        {loading ? (
          <p className="text-slate-300">Loading brand protection data...</p>
        ) : (
          <SummaryCards scan={activeScan} />
        )}

        <section className="rounded-lg border border-white/10 bg-slate-900/80">
          <div className="border-b border-white/10 px-5 py-4">
            <h2 className="font-semibold">Findings</h2>
          </div>

          {!findings.length ? (
            <p className="p-5 text-sm text-slate-400">
              Run a quick brand scan to check for possible Fibank lookalike
              domains.
            </p>
          ) : (
            <div className="overflow-auto">
              <table className="w-full min-w-[1000px] text-left text-sm">
                <thead className="bg-slate-950 text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Risk</th>
                    <th className="px-4 py-3">Score</th>
                    <th className="px-4 py-3">Domain</th>
                    <th className="px-4 py-3">Title</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Redirect</th>
                    <th className="px-4 py-3">Brand Keywords</th>
                    <th className="px-4 py-3">Phishing Signals</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-white/10 text-slate-300">
                  {findings.map((finding) => (
                    <tr key={finding.id}>
                      <td className="px-4 py-3">
                        <RiskPill level={finding.risk_level} />
                      </td>
                      <td className="px-4 py-3 font-semibold text-white">
                        {finding.risk_score}
                      </td>
                      <td className="px-4 py-3">{finding.domain}</td>
                      <td className="max-w-xs px-4 py-3">
                        {finding.title || finding.error || "-"}
                      </td>
                      <td className="px-4 py-3">
                        {finding.status_code || "-"}
                      </td>
                      <td className="max-w-xs break-all px-4 py-3">
                        {finding.redirected_to || "-"}
                      </td>
                      <td className="px-4 py-3">
                        {(finding.matched_brand_keywords || []).join(", ") ||
                          "-"}
                      </td>
                      <td className="px-4 py-3">
                        {(finding.matched_phishing_signals || []).join(", ") ||
                          "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="rounded-lg border border-white/10 bg-slate-900/80">
          <div className="border-b border-white/10 px-5 py-4">
            <h2 className="font-semibold">Scan History</h2>
          </div>

          <div className="divide-y divide-white/10">
            {!runs.length && (
              <p className="p-5 text-sm text-slate-400">
                No scan history yet.
              </p>
            )}

            {runs.map((run) => (
              <button
                key={run.id}
                onClick={() => loadRun(run.id)}
                className="grid w-full gap-3 px-5 py-4 text-left hover:bg-white/5 md:grid-cols-[auto_1fr_auto_auto] md:items-center"
              >
                <span className="font-semibold text-white">#{run.id}</span>
                <span className="text-sm text-slate-300">
                  {run.mode} - {run.status} - {run.total_candidates} candidates
                </span>
                <span className="text-sm text-slate-400">
                  High {run.high_count} / Medium {run.medium_count}
                </span>
                <span className="text-xs text-slate-500">
                  {run.completed_at
                    ? new Date(run.completed_at).toLocaleString()
                    : "Running"}
                </span>
              </button>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}