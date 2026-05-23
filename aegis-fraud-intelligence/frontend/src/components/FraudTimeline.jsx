import RiskBadge from "./RiskBadge";

export default function FraudTimeline({ events = [] }) {
  return (
    <section className="rounded-lg border border-white/10 bg-slate-900/80 p-5">
      <h2 className="font-semibold text-white">Fraud Timeline</h2>
      <div className="mt-4 space-y-3">
        {!events.length ? (
          <p className="text-sm text-slate-400">No timeline events loaded.</p>
        ) : (
          events.slice(-8).map((event, index) => (
            <div key={`${event.event_type}-${event.created_at}-${index}`} className="border-l border-sky-500/40 pl-4">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium text-white">{event.title}</p>
                {event.severity && <RiskBadge severity={event.severity} />}
              </div>
              <p className="text-xs text-slate-400">{event.created_at ? new Date(event.created_at).toLocaleString() : ""}</p>
              <p className="mt-1 text-sm text-slate-300">{event.description}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

