import { LockKeyhole } from "lucide-react";

const items = [
  "Device identifiers are hashed",
  "Logs are minimized",
  "Only risk-relevant metadata is stored",
  "Every decision has an explanation",
  "High-risk decisions are reviewable by human analysts",
  "Prototype does not use real banking data"
];

export default function PrivacyPanel() {
  return (
    <section className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
      <div className="flex items-center gap-2 text-white">
        <LockKeyhole className="h-5 w-5 text-sky-300" />
        <h2 className="text-lg font-semibold">Privacy By Design</h2>
      </div>
      <ul className="mt-4 space-y-2 text-sm text-slate-300">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 rounded-full bg-sky-300" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

