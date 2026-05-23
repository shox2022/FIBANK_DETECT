import RiskBadge from "./RiskBadge";

export default function LogViewer({ logs = [] }) {
  return (
    <section className="rounded-lg border border-white/10 bg-slate-900/80">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="font-semibold text-white">Security Logs</h2>
      </div>
      <div className="max-h-96 overflow-auto">
        {!logs.length ? (
          <p className="p-5 text-sm text-slate-400">No security logs available.</p>
        ) : (
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="sticky top-0 bg-slate-950 text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Endpoint</th>
                <th className="px-4 py-3">IP</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Risk</th>
                <th className="px-4 py-3">Payload</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10 text-slate-300">
              {logs.map((log) => (
                <tr key={log.id} className={["CRITICAL", "HIGH"].includes(log.severity) ? "bg-red-950/20" : ""}>
                  <td className="px-4 py-3">{log.created_at ? new Date(log.created_at).toLocaleString() : "-"}</td>
                  <td className="px-4 py-3">{log.endpoint || "-"}</td>
                  <td className="px-4 py-3">{log.ip_address || "-"}</td>
                  <td className="px-4 py-3">{log.event_type}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <RiskBadge severity={log.severity} />
                      <span>{log.risk_score}</span>
                    </div>
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 font-mono text-xs">{log.payload_sample || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

