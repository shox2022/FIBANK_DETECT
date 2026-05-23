import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, CreditCard } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import { useAuth } from "../auth/AuthContext";
import Navbar from "../components/Navbar";
import RiskBadge from "../components/RiskBadge";
import TransactionSimulator from "../components/TransactionSimulator";
import DemoAttackPanel from "../components/DemoAttackPanel";
import MlScorePanel from "../components/MlScorePanel";

function ResultCard({ result }) {
  if (!result) return null;

  const risk = result.risk_score ?? result.risk?.risk_score;
  const severity = result.severity ?? result.risk?.severity;
  const reasons = result.reasons ?? result.risk?.reasons ?? [];
  const tx = result.transaction;
  const balance = result.balance;

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-950">
          Latest Decision
        </h2>
        {severity && <RiskBadge severity={severity} />}
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <div>
          <p className="text-xs uppercase text-slate-500">Risk score</p>
          <p className="text-3xl font-bold text-slate-950">{risk ?? "N/A"}</p>
        </div>

        <div>
          <p className="text-xs uppercase text-slate-500">Friction</p>
          <p className="font-semibold text-slate-950">
            {result.friction?.label || result.recommendation || "None"}
          </p>
        </div>

        <div>
          <p className="text-xs uppercase text-slate-500">
            Transaction status
          </p>
          <p className="font-semibold text-slate-950">{tx?.status || "N/A"}</p>
        </div>
      </div>

      <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-700">
        {result.friction?.customer_message ||
          result.message ||
          "AEGIS completed the analysis."}
      </div>

      {balance && (
        <div className="mt-4 rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-700">
          <p className="font-semibold text-slate-950">{balance.message}</p>

          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            <span>
              Source:{" "}
              <b>EUR {Number(balance.from_before || 0).toLocaleString()}</b>
              {" -> "}
              <b>EUR {Number(balance.from_after || 0).toLocaleString()}</b>
            </span>

            {balance.to_after !== null && balance.to_after !== undefined && (
              <span>
                Recipient:{" "}
                <b>EUR {Number(balance.to_before || 0).toLocaleString()}</b>
                {" -> "}
                <b>EUR {Number(balance.to_after || 0).toLocaleString()}</b>
              </span>
            )}
          </div>
        </div>
      )}

      {reasons.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {reasons.map((reason) => (
            <span
              key={reason}
              className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
            >
              {reason}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4">
        <MlScorePanel result={result} />
      </div>
    </section>
  );
}

export default function CustomerApp() {
  const { user } = useAuth();

  const [profile, setProfile] = useState(user);
  const [result, setResult] = useState(null);
  const [events, setEvents] = useState([]);
  const [toast, setToast] = useState("");
  const [error, setError] = useState("");
  const [loadingAction, setLoadingAction] = useState("");

  async function refreshMe() {
    try {
      const response = await api.get("/api/auth/me");
      setProfile(response.data);
    } catch {
      setProfile(user);
    }
  }

  useEffect(() => {
    refreshMe();
  }, []);

  function remember(label, data) {
    setResult(data);
    setEvents((current) =>
      [{ label, data, at: new Date().toISOString() }, ...current].slice(0, 6)
    );
    setToast(`${label} completed`);
    setTimeout(() => setToast(""), 2200);
    refreshMe();
  }

  async function runRequest(label, action, request) {
    setLoadingAction(action);
    setError("");

    try {
      const response = await request();
      remember(label, response.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoadingAction("");
    }
  }

  async function submitTransfer(payload) {
    const response = await api.post("/api/simulate/transaction", payload);
    return response;
  }

  async function runDemo(action) {
    const commonLogin = {
      device_hash: "dev_hash_ardit_trusted_laptop",
      device_label: "Trusted laptop",
      browser: "Chrome",
      os: "Windows",
      ip_address: "185.53.12.15",
      country: "Albania",
      city: "Tirana",
      is_vpn: false,
      is_proxy: false,
      success: true,
      failed_attempts: 0,
    };

    const actions = {
      "normal-login": () => api.post("/api/simulate/login", commonLogin),

      "germany-vpn": () =>
        api.post("/api/simulate/login", {
          ...commonLogin,
          device_hash: "phase5_germany_vpn",
          ip_address: "93.184.216.34",
          country: "Germany",
          city: "Berlin",
          is_vpn: true,
          failed_attempts: 3,
        }),

      "impossible-travel": async () => {
        await api.post("/api/simulate/login", commonLogin);
        return api.post("/api/simulate/login", {
          ...commonLogin,
          device_hash: "phase5_impossible_device",
          ip_address: "93.184.216.35",
          country: "Germany",
          city: "Berlin",
          is_vpn: true,
          failed_attempts: 3,
        });
      },

      "token-theft": () =>
        api.post("/api/simulate/token-theft", {
          session_token_hash: "phase5_token_theft",
          original_ip_address: "185.53.12.15",
          new_ip_address: "203.0.113.77",
          original_country: "Albania",
          new_country: "Germany",
          original_device_hash: "dev_hash_ardit_trusted_laptop",
          new_device_hash: "phase5_attacker_device",
          is_vpn: true,
          is_proxy: false,
        }),

      "high-value-transfer": () =>
        submitTransfer({
          to_account: "AL472091000000009999",
          amount: 2500,
          currency: "EUR",
          recipient_name: "New Beneficiary",
          recipient_is_new: true,
        }),

      "sql-injection": () =>
        api.post("/api/simulate/security-log", {
          event_type: "SQL_INJECTION_ATTEMPT",
          endpoint: "/api/auth/login",
          ip_address: "91.220.33.44",
          payload_sample: "' OR '1'='1 --",
        }),

      "mule-ring": () =>
        api.post("/api/simulate/mule-ring", {
          mule_account: "AL472091000000009998",
          amount: 450,
        }),
    };

    await runRequest(
      actions[action] ? action.replaceAll("-", " ") : "demo",
      action,
      actions[action]
    );
  }

  async function onTransfer(payload) {
    await runRequest("transfer analysis", "transfer", () =>
      submitTransfer(payload)
    );
  }

  return (
    <main className="min-h-screen bg-slate-100">
      <Navbar variant="light" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6">
        {(toast || error) && (
          <div
            className={`flex items-center gap-2 rounded-md p-3 text-sm ${
              error ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"
            }`}
          >
            {error ? (
              <AlertCircle className="h-4 w-4" />
            ) : (
              <CheckCircle2 className="h-4 w-4" />
            )}
            {error || toast}
          </div>
        )}

        <section>
          <div className="rounded-lg bg-slate-950 p-6 text-white shadow-sm">
            <div className="flex items-center gap-3">
              <CreditCard className="h-6 w-6 text-sky-300" />
              <div>
                <p className="text-sm text-slate-400">Primary account</p>
                <h1 className="text-2xl font-bold">
                  {profile?.name || "Customer"}
                </h1>
              </div>
            </div>

            <p className="mt-6 text-sm text-slate-400">Available balance</p>
            <p className="text-5xl font-bold">
              EUR {Number(profile?.balance || 0).toLocaleString()}
            </p>
            <p className="mt-3 text-sm text-slate-400">
              {profile?.account_number || "Account pending"}
            </p>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[1fr_0.95fr]">
          <div className="space-y-6">
            <TransactionSimulator
              onSubmit={onTransfer}
              loading={loadingAction === "transfer"}
            />
            <ResultCard result={result} />
          </div>

          <div className="space-y-6">
            <DemoAttackPanel onRun={runDemo} loadingAction={loadingAction} />

            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-950">
                Recent Simulation Events
              </h2>

              <div className="mt-4 space-y-3">
                {!events.length ? (
                  <p className="text-sm text-slate-500">
                    Run a demo action to populate this feed.
                  </p>
                ) : (
                  events.map((event) => (
                    <div key={event.at} className="rounded-md bg-slate-50 p-3">
                      <p className="font-medium text-slate-900">
                        {event.label}
                      </p>
                      <p className="text-xs text-slate-500">
                        {new Date(event.at).toLocaleString()}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}