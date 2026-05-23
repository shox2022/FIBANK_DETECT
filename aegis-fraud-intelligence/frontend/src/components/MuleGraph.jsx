import ReactFlow, { Background, Controls, MarkerType } from "reactflow";

function AccountNodeLabel({ node }) {
  const shortAccount = `${node.id.slice(0, 6)}...${node.id.slice(-6)}`;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <span className="text-[10px] font-bold uppercase tracking-normal">
          {node.suspicious ? "Mule candidate" : "Account"}
        </span>
        <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${node.suspicious ? "bg-red-100 text-red-800" : "bg-sky-100 text-sky-800"}`}>
          Risk {node.risk_score}
        </span>
      </div>
      <div className="font-mono text-[12px] font-semibold leading-5">{shortAccount}</div>
      <div className="font-mono text-[10px] leading-4 opacity-70">{node.id}</div>
    </div>
  );
}

export default function MuleGraph({ graph }) {
  const nodes = (graph?.nodes || []).map((node, index) => ({
    id: node.id,
    position: {
      x: (index % 3) * 300,
      y: Math.floor(index / 3) * 165
    },
    data: { label: <AccountNodeLabel node={node} /> },
    style: {
      border: `2px solid ${node.suspicious ? "#dc2626" : "#0284c7"}`,
      background: node.suspicious ? "#fff1f2" : "#f8fafc",
      color: node.suspicious ? "#7f1d1d" : "#0f172a",
      borderRadius: 8,
      boxShadow: "0 12px 28px rgba(15, 23, 42, 0.22)",
      padding: 12,
      width: 220,
      fontSize: 12
    }
  }));

  const edges = (graph?.edges || []).map((edge) => ({
    id: String(edge.id),
    source: edge.source,
    target: edge.target,
    label: edge.amount ? `EUR ${Number(edge.amount).toLocaleString()}` : "",
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: edge.risk_score >= 80 ? "#f97316" : "#38bdf8", strokeWidth: 3 },
    labelBgPadding: [8, 5],
    labelBgBorderRadius: 6,
    labelBgStyle: { fill: "#ffffff", fillOpacity: 0.95 },
    labelStyle: {
      fill: "#0f172a",
      fontSize: 12,
      fontWeight: 700
    }
  }));

  return (
    <section className="rounded-lg border border-white/10 bg-slate-950">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
        <h2 className="font-semibold text-white">Mule Network</h2>
        <div className="flex items-center gap-3 text-xs text-slate-300">
          <span className="inline-flex items-center gap-1"><span className="h-2.5 w-2.5 rounded bg-sky-400" /> Account</span>
          <span className="inline-flex items-center gap-1"><span className="h-2.5 w-2.5 rounded bg-red-500" /> Mule candidate</span>
        </div>
      </div>
      <div className="h-[500px]">
        {nodes.length ? (
          <ReactFlow nodes={nodes} edges={edges} fitView fitViewOptions={{ padding: 0.22 }}>
            <Background color="#475569" gap={22} />
            <Controls />
          </ReactFlow>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">No mule graph data yet.</div>
        )}
      </div>
    </section>
  );
}
