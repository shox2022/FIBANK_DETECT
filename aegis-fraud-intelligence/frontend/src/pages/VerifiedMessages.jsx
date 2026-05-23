import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ClipboardCheck, MailCheck, MailWarning, ShieldAlert } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import Navbar from "../components/Navbar";
import RiskBadge from "../components/RiskBadge";

const resultStyles = {
  VERIFIED_OFFICIAL: {
    label: "Verified official",
    shell: "border-emerald-200 bg-emerald-50 text-emerald-900",
    badge: "bg-emerald-500/15 text-emerald-700 ring-emerald-500/30"
  },
  POSSIBLE_PHISHING: {
    label: "Possible phishing attempt",
    shell: "border-red-200 bg-red-50 text-red-900",
    badge: "bg-red-500/15 text-red-700 ring-red-500/30"
  },
  SUSPICIOUS: {
    label: "Suspicious message",
    shell: "border-orange-200 bg-orange-50 text-orange-900",
    badge: "bg-orange-500/15 text-orange-700 ring-orange-500/30"
  },
  UNKNOWN: {
    label: "Unknown message",
    shell: "border-slate-200 bg-slate-50 text-slate-800",
    badge: "bg-slate-500/15 text-slate-700 ring-slate-400/30"
  }
};

const quickSamples = {
  official: {
    label: "Official message sample",
    text: "The bank will never ask for your password, PIN, card number, CVV, or OTP through email or SMS. Always verify messages inside the official banking app."
  },
  phishing: {
    label: "Phishing SMS sample",
    text: "URGENT: Your Fibank account has been blocked. Click http://fake-fibank-login.example to verify your password and OTP immediately."
  },
  suspicious: {
    label: "Suspicious email sample",
    text: "Final warning. Your account will be suspended unless you confirm your card number today."
  }
};

function Badge({ children, tone = "slate" }) {
  const tones = {
    slate: "bg-slate-100 text-slate-700 ring-slate-200",
    sky: "bg-sky-100 text-sky-700 ring-sky-200",
    purple: "bg-purple-100 text-purple-700 ring-purple-200",
    emerald: "bg-emerald-100 text-emerald-700 ring-emerald-200"
  };
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tones[tone] || tones.slate}`}>{children}</span>;
}

export default function VerifiedMessages() {
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState("");
  const [result, setResult] = useState(null);
  const [loadingMessages, setLoadingMessages] = useState(true);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");

  async function loadMessages() {
    setLoadingMessages(true);
    setError("");
    try {
      const response = await api.get("/api/messages/my");
      setMessages(response.data || []);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoadingMessages(false);
    }
  }

  useEffect(() => {
    loadMessages();
  }, []);

  const officialSample = useMemo(() => {
    const antiPhishing = messages.find((message) => message.title === "Protect yourself from phishing");
    return antiPhishing?.body || quickSamples.official.text;
  }, [messages]);

  async function verify(event) {
    event.preventDefault();
    setChecking(true);
    setError("");
    setResult(null);
    try {
      const response = await api.post("/api/messages/verify", { message_text: messageText });
      setResult(response.data);
      loadMessages();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setChecking(false);
    }
  }

  function fillSample(type) {
    setResult(null);
    setMessageText(type === "official" ? officialSample : quickSamples[type].text);
  }

  const style = resultStyles[result?.result] || resultStyles.UNKNOWN;

  return (
    <main className="min-h-screen bg-slate-100">
      <Navbar variant="light" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6">
        <section className="rounded-lg bg-slate-950 p-6 text-white">
          <div className="flex items-start gap-3">
            <div className="rounded-md bg-sky-500/15 p-2 text-sky-300">
              <MailCheck className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm uppercase tracking-wide text-sky-300">Communication Trust Center</p>
              <h1 className="mt-1 text-3xl font-bold">Verified Bank Messages</h1>
              <p className="mt-2 max-w-3xl text-slate-300">
                Check whether a message really came from the bank before clicking links or sharing information.
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-950">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-5 w-5" />
            <p className="text-sm leading-6">
              <b>AEGIS Tip:</b> If a message asks for your password, PIN, card number, CVV, or OTP, treat it as suspicious.
              Banks should direct you to open the official app, not click unknown links.
            </p>
          </div>
        </section>

        {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}

        <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-5 py-4">
              <h2 className="text-lg font-semibold text-slate-950">Official Bank Messages</h2>
              <p className="mt-1 text-sm text-slate-500">Simulated messages generated inside AEGIS.</p>
            </div>
            <div className="max-h-[720px] space-y-4 overflow-auto p-5">
              {loadingMessages && <p className="text-sm text-slate-500">Loading official messages...</p>}
              {!loadingMessages && !messages.length && <p className="text-sm text-slate-500">No official messages yet.</p>}
              {messages.map((message) => (
                <article key={message.id} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-slate-950">{message.title}</h3>
                      <p className="mt-1 text-xs text-slate-500">{message.created_at ? new Date(message.created_at).toLocaleString() : "-"}</p>
                    </div>
                    <Badge tone="emerald">{message.official ? "Official" : "Unverified"}</Badge>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Badge tone="sky">{message.channel}</Badge>
                    <Badge tone="purple">{message.message_type}</Badge>
                    <RiskBadge severity={message.risk_level} />
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-700">{message.body}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="space-y-5">
            <form onSubmit={verify} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="rounded-md bg-purple-100 p-2 text-purple-700">
                  <ClipboardCheck className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Message Verification / Phishing Checker</h2>
                  <p className="mt-1 text-sm text-slate-500">Paste an email, SMS, or message claiming to be from the bank.</p>
                </div>
              </div>
              <textarea
                className="mt-4 min-h-44 w-full rounded-md border border-slate-300 px-3 py-2 text-slate-950"
                value={messageText}
                minLength={5}
                maxLength={5000}
                onChange={(event) => setMessageText(event.target.value)}
                placeholder="Paste a suspicious message here..."
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button type="button" onClick={() => fillSample("official")} className="rounded-md bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700 hover:bg-emerald-100">
                  {quickSamples.official.label}
                </button>
                <button type="button" onClick={() => fillSample("phishing")} className="rounded-md bg-red-50 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-100">
                  {quickSamples.phishing.label}
                </button>
                <button type="button" onClick={() => fillSample("suspicious")} className="rounded-md bg-orange-50 px-3 py-2 text-sm font-semibold text-orange-700 hover:bg-orange-100">
                  {quickSamples.suspicious.label}
                </button>
              </div>
              <button disabled={checking || messageText.trim().length < 5} className="mt-4 inline-flex items-center gap-2 rounded-md bg-slate-950 px-4 py-2 font-semibold text-white hover:bg-slate-800 disabled:opacity-60">
                <MailWarning className="h-4 w-4" />
                {checking ? "Checking..." : "Check Message"}
              </button>
            </form>

            {result && (
              <section className={`rounded-lg border p-5 shadow-sm ${style.shell}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-wide opacity-70">Verification Result</p>
                    <h2 className="mt-1 text-2xl font-bold">{style.label}</h2>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${style.badge}`}>
                    {result.result}
                  </span>
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-md bg-white/70 p-3">
                    <p className="text-xs uppercase tracking-wide opacity-70">Risk score</p>
                    <p className="text-3xl font-bold">{result.risk_score}</p>
                  </div>
                  <div className="rounded-md bg-white/70 p-3">
                    <p className="text-xs uppercase tracking-wide opacity-70">Checked</p>
                    <p className="mt-2 font-semibold">{result.checked_at ? new Date(result.checked_at).toLocaleString() : "-"}</p>
                  </div>
                </div>
                <div className="mt-4">
                  <h3 className="font-semibold">Reasons</h3>
                  <ul className="mt-2 space-y-2 text-sm">
                    {(result.reasons || []).map((reason) => <li key={reason}>- {reason}</li>)}
                  </ul>
                </div>
                <div className="mt-4 rounded-md bg-white/70 p-3 text-sm leading-6">
                  <b>Recommendation:</b> {result.recommendation}
                </div>
                {result.matched_message && (
                  <div className="mt-4 rounded-md border border-emerald-200 bg-white/80 p-3">
                    <div className="flex items-center gap-2 text-emerald-700">
                      <CheckCircle2 className="h-4 w-4" />
                      <p className="font-semibold">Matched official message</p>
                    </div>
                    <p className="mt-2 text-sm font-semibold">{result.matched_message.title}</p>
                    <p className="mt-1 text-sm leading-6">{result.matched_message.body}</p>
                  </div>
                )}
              </section>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
