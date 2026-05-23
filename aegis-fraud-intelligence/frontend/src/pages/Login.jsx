import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { apiErrorMessage } from "../api";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const user = await login(email, password);
      navigate(user.role === "CUSTOMER" ? "/customer" : "/dashboard", {
        replace: true,
      });
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto grid min-h-screen max-w-6xl items-center gap-10 px-4 py-10 lg:grid-cols-[1.1fr_0.9fr]">
        <section>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-sky-400/30 bg-sky-400/10 px-3 py-1 text-sm text-sky-200">
            <ShieldCheck className="h-4 w-4" />
            Adaptive Engine for Guarded Intelligence & Security
          </div>

          <h1 className="text-5xl font-bold tracking-normal">
            AEGIS Fraud Intelligence
          </h1>

          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
            Behaviour, device, location, transaction signals, logs, and
            AI-assisted scoring combined into a risk intelligence command
            center.
          </p>

          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <p className="text-sm font-semibold text-sky-200">
                Risk Intelligence
              </p>
              <p className="mt-2 text-sm text-slate-400">
                Correlates customer activity, devices, sessions, logs, and
                transactions.
              </p>
            </div>

            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <p className="text-sm font-semibold text-sky-200">
                Fraud Prevention
              </p>
              <p className="mt-2 text-sm text-slate-400">
                Detects suspicious behavior before risky payments are approved.
              </p>
            </div>

            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <p className="text-sm font-semibold text-sky-200">
                Analyst Workflow
              </p>
              <p className="mt-2 text-sm text-slate-400">
                Supports alerts, investigation cases, decision trails, and
                reporting.
              </p>
            </div>
          </div>
        </section>

        <form
          onSubmit={submit}
          className="rounded-lg border border-white/10 bg-white p-6 text-slate-950 shadow-2xl"
        >
          <h2 className="text-2xl font-bold">Sign in</h2>

          <p className="mt-1 text-sm text-slate-500">
            Enter your authorized AEGIS credentials.
          </p>

          <label className="mt-6 block text-sm font-medium text-slate-700">
            Email
            <input
              type="email"
              autoComplete="email"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder=""
              required
            />
          </label>

          <label className="mt-4 block text-sm font-medium text-slate-700">
            Password
            <input
              type="password"
              autoComplete="current-password"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder=""
              required
            />
          </label>

          {error && (
            <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
              {error}
            </p>
          )}

          <button
            disabled={loading}
            className="mt-6 w-full rounded-md bg-slate-950 px-4 py-3 font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Enter AEGIS"}
          </button>
        </form>
      </div>
    </main>
  );
}