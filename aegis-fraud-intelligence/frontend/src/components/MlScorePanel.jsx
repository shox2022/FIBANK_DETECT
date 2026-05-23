import { BrainCircuit, CheckCircle2, CircleAlert, Cpu } from "lucide-react";
import RiskBadge from "./RiskBadge";

function asPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return `${(numeric * 100).toFixed(2)}%`;
}

function asScore(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return numeric.toFixed(numeric % 1 === 0 ? 0 : 2);
}

function yesNo(value) {
  return value ? "Yes" : "No";
}

function Metric({ label, value, accent = false }) {
  return (
    <div className={`rounded-md border p-3 ${accent ? "border-purple-400/30 bg-purple-500/10" : "border-slate-200 bg-white/70"}`}>
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-bold text-slate-950">{value ?? "N/A"}</p>
    </div>
  );
}

export default function MlScorePanel({ result, dark = false }) {
  if (!result) return null;

  const hasMlFields = [
    "ml_score",
    "ml_probability",
    "ml_risk_band",
    "ml_model_version",
    "ml_enabled"
  ].some((key) => Object.prototype.hasOwnProperty.call(result, key));

  if (!hasMlFields) return null;

  const enabled = Boolean(result.ml_enabled ?? result.enabled);
  const finalScore = result.risk_score ?? result.final_score;
  const finalSeverity = result.severity;
  const missingCount = Array.isArray(result.ml_missing_features)
    ? result.ml_missing_features.length
    : Array.isArray(result.missing_features)
      ? result.missing_features.length
      : Number(result.ml_missing_features_count ?? 0);
  const explanation = result.ml_explanation || result.explanation;
  const modelVersion = result.ml_model_version || result.model_version || "xgboost-unavailable";
  const mlBand = result.ml_risk_band || "DISABLED";
  const probability = result.ml_probability;
  const mlScore = result.ml_score;
  const flag = result.ml_flag;
  const shell = dark
    ? "border-purple-400/20 bg-slate-950/70 text-white"
    : "border-purple-200 bg-purple-50/70 text-slate-950";
  const metricAccent = dark ? "border-purple-400/20 bg-purple-500/10" : "border-purple-200 bg-white";

  return (
    <section className={`rounded-lg border p-5 shadow-sm ${shell}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-purple-500/15 p-2 text-purple-300">
            <BrainCircuit className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-purple-300">AI / XGBoost Fraud Score</p>
            <h2 className="text-lg font-semibold">Rule Risk + ML Suspicion Intelligence</h2>
          </div>
        </div>
        <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ring-1 ${
          enabled
            ? "bg-emerald-500/15 text-emerald-700 ring-emerald-500/30"
            : "bg-slate-500/15 text-slate-600 ring-slate-400/30"
        }`}>
          {enabled ? <CheckCircle2 className="h-3.5 w-3.5" /> : <CircleAlert className="h-3.5 w-3.5" />}
          ML enabled: {yesNo(enabled)}
        </span>
      </div>

      {!enabled && (
        <div className="mt-4 rounded-md border border-amber-300/40 bg-amber-100/70 p-3 text-sm text-amber-900">
          ML unavailable - using rule-based fallback.
        </div>
      )}

      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Rule score" value={asScore(result.rule_score)} />
        <Metric label="ML score" value={asScore(mlScore)} accent />
        <Metric label="ML probability" value={probability === undefined ? "N/A" : asPercent(probability)} accent />
        <Metric label="ML flag" value={flag === undefined || flag === null ? "N/A" : Number(flag) ? "Fraud" : "Legit"} />
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className={`rounded-md border p-3 ${metricAccent}`}>
          <p className="text-xs uppercase tracking-wide text-slate-500">ML risk band</p>
          <div className="mt-2">
            {mlBand && mlBand !== "DISABLED" ? <RiskBadge severity={mlBand} /> : <span className="text-sm font-semibold text-slate-500">DISABLED</span>}
          </div>
        </div>
        <Metric label="Missing features" value={Number.isFinite(missingCount) ? missingCount : "N/A"} />
        <Metric label="ML model" value={modelVersion} accent />
        <div className={`rounded-md border p-3 ${metricAccent}`}>
          <p className="text-xs uppercase tracking-wide text-slate-500">Final combined risk</p>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-lg font-bold text-slate-950">{finalScore ?? "N/A"}</span>
            {finalSeverity && <RiskBadge severity={finalSeverity} />}
          </div>
        </div>
      </div>

      {explanation && (
        <div className="mt-4 rounded-md border border-sky-300/30 bg-sky-500/10 p-3 text-sm leading-6 text-slate-700">
          <div className="mb-1 flex items-center gap-2 font-semibold text-slate-950">
            <Cpu className="h-4 w-4 text-purple-500" />
            Model explanation
          </div>
          {explanation}
        </div>
      )}
    </section>
  );
}
