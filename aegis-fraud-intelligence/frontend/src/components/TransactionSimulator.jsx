import { Send } from "lucide-react";
import { useState } from "react";

export default function TransactionSimulator({ onSubmit, loading }) {
  const [form, setForm] = useState({
    to_account: "AL472091000000009999",
    recipient_name: "New Beneficiary",
    amount: "2500",
    currency: "EUR",
    recipient_is_new: true
  });

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function submit(event) {
    event.preventDefault();
    onSubmit({
      ...form,
      amount: Number(form.amount),
      recipient_is_new: Boolean(form.recipient_is_new)
    });
  }

  return (
    <form onSubmit={submit} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">Transfer Simulator</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <label className="text-sm text-slate-600">
          Recipient account
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-slate-950" value={form.to_account} onChange={(e) => update("to_account", e.target.value)} />
        </label>
        <label className="text-sm text-slate-600">
          Recipient name
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-slate-950" value={form.recipient_name} onChange={(e) => update("recipient_name", e.target.value)} />
        </label>
        <label className="text-sm text-slate-600">
          Amount
          <input type="number" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-slate-950" value={form.amount} onChange={(e) => update("amount", e.target.value)} />
        </label>
        <label className="text-sm text-slate-600">
          Currency
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-slate-950" value={form.currency} onChange={(e) => update("currency", e.target.value)} />
        </label>
      </div>
      <label className="mt-4 flex items-center gap-2 text-sm text-slate-700">
        <input type="checkbox" checked={form.recipient_is_new} onChange={(e) => update("recipient_is_new", e.target.checked)} />
        New beneficiary
      </label>
      <button disabled={loading} className="mt-5 inline-flex items-center gap-2 rounded-md bg-slate-950 px-4 py-2 font-semibold text-white hover:bg-slate-800 disabled:opacity-60">
        <Send className="h-4 w-4" />
        {loading ? "Analyzing..." : "Send transfer"}
      </button>
    </form>
  );
}

