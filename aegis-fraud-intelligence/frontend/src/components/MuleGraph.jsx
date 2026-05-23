import ReactFlow, { Background, Controls, MarkerType } from "reactflow";

export default function MuleGraph({ graph }) {
  const nodes = (graph?.nodes || []).map((node, index) => ({
    id: node.id,
    position: {
      x: (index % 4) * 230,
      y: Math.floor(index / 4) * 130
    },
    data: { label: node.label || node.id },
    style: {
      border: `2px solid ${node.suspicious ? "#ef4444" : "#38bdf8"}`,
      background: node.suspicious ? "#7f1d1d" : "#0f172a",
      color: "#fff",
      borderRadius: 8,
      padding: 10,
      minWidth: 150,
      fontSize: 12
    }
  }));

  const edges = (graph?.edges || []).map((edge) => ({
    id: String(edge.id),
    source: edge.source,
    target: edge.target,
    label: edge.amount ? `EUR ${Number(edge.amount).toLocaleString()}` : "",
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: edge.risk_score >= 80 ? "#f97316" : "#38bdf8", strokeWidth: 2 },
    labelStyle: { fill: "#cbd5e1", fontSize: 11 }
  }));

  return (
    <section className="rounded-lg border border-white/10 bg-slate-900/80">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="font-semibold text-white">Mule Network</h2>
      </div>
      <div className="h-[420px]">
        {nodes.length ? (
          <ReactFlow nodes={nodes} edges={edges} fitView>
            <Background color="#334155" gap={18} />
            <Controls />
          </ReactFlow>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">No mule graph data yet.</div>
        )}
      </div>
    </section>
  );
}
