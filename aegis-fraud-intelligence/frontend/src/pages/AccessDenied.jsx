import { Link } from "react-router-dom";

export default function AccessDenied() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">
      <div className="max-w-md rounded-lg border border-white/10 bg-slate-900 p-8 text-center">
        <h1 className="text-3xl font-bold">Access denied</h1>
        <p className="mt-3 text-slate-300">Your current role does not have permission to open this workspace.</p>
        <Link to="/" className="mt-6 inline-block rounded-md bg-sky-500 px-4 py-2 font-semibold text-white hover:bg-sky-400">
          Return to AEGIS
        </Link>
      </div>
    </main>
  );
}

