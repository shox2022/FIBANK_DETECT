import { useEffect, useState } from "react";
import { Loader2, PlusCircle } from "lucide-react";
import api, { apiErrorMessage } from "../api";

export default function AnalystNotesPanel({ alertId, refreshKey = 0, onChanged }) {
  const [notes, setNotes] = useState([]);
  const [note, setNote] = useState("");
  const [actionType, setActionType] = useState("NOTE");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    if (!alertId) return;
    setLoading(true);
    setError("");
    try {
      const response = await api.get(`/api/alerts/${alertId}/notes`);
      setNotes(response.data || []);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [alertId, refreshKey]);

  async function submitNote(event) {
    event.preventDefault();
    if (note.trim().length < 2) return;
    setSaving(true);
    setError("");
    try {
      await api.post(`/api/alerts/${alertId}/notes`, {
        note: note.trim(),
        action_type: actionType
      });
      setNote("");
      setActionType("NOTE");
      await load();
      onChanged?.();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-lg border border-white/10 bg-slate-900/80">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="font-semibold text-white">Analyst Notes</h2>
        <p className="mt-1 text-sm text-slate-400">Document review steps, customer contact, and investigation context.</p>
      </div>
      <form onSubmit={submitNote} className="space-y-3 p-5">
        {error && <p className="rounded-md bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
        <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
          <textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            rows={3}
            maxLength={2000}
            placeholder="Add an investigation note..."
            className="w-full rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-sky-400"
          />
          <div className="flex flex-col gap-3">
            <select
              value={actionType}
              onChange={(event) => setActionType(event.target.value)}
              className="rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
            >
              <option>NOTE</option>
              <option>ESCALATED</option>
              <option>MARKED_FRAUD</option>
              <option>CUSTOMER_CONTACTED</option>
              <option>REVIEW_COMPLETED</option>
            </select>
            <button
              disabled={saving || note.trim().length < 2}
              className="inline-flex items-center justify-center gap-2 rounded-md bg-sky-500 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400 disabled:opacity-60"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlusCircle className="h-4 w-4" />}
              Add Note
            </button>
          </div>
        </div>
      </form>
      <div className="divide-y divide-white/10 border-t border-white/10">
        {loading && <p className="p-5 text-sm text-slate-400">Loading notes...</p>}
        {!loading && !notes.length && <p className="p-5 text-sm text-slate-400">No analyst notes yet.</p>}
        {notes.map((item) => (
          <article key={item.id} className="p-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-sky-500/15 px-2.5 py-1 text-xs font-semibold text-sky-200">{item.action_type}</span>
              <span className="text-sm text-slate-300">{item.analyst_name || `Analyst #${item.analyst_user_id}`}</span>
              <span className="text-xs text-slate-500">{item.created_at ? new Date(item.created_at).toLocaleString() : "-"}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">{item.note}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
