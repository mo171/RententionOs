"use client";

import { useCausalModelStore } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";

const NODE_W = 88;
const NODE_H = 28;

export function CausalDagChart() {
  const dagNodes = useCausalModelStore((s) => s.dagNodes);
  const dagEdges = useCausalModelStore((s) => s.dagEdges);

  const nodeById = Object.fromEntries(dagNodes.map((n) => [n.id, n]));

  const edgePath = (from: string, to: string) => {
    const a = nodeById[from];
    const b = nodeById[to];
    if (!a || !b) return "";
    const x1 = a.x + NODE_W;
    const y1 = a.y + NODE_H / 2;
    const x2 = b.x;
    const y2 = b.y + NODE_H / 2;
    const mx = (x1 + x2) / 2;
    return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
  };

  return (
    <CausalChartCard
      subtitle="Model-assumed structure"
      title="Causal DAG"
      className="min-h-[260px]"
    >
      <svg viewBox="0 0 520 150" className="w-full h-[200px]">
        <defs>
          <marker
            id="arrow"
            markerWidth="8"
            markerHeight="8"
            refX="6"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L6,3 L0,6 Z" fill="var(--color-text-muted)" />
          </marker>
          <marker
            id="arrow-danger"
            markerWidth="8"
            markerHeight="8"
            refX="6"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L6,3 L0,6 Z" fill="var(--color-state-danger)" />
          </marker>
        </defs>
        {dagEdges.map((edge) => (
          <path
            key={`${edge.from}-${edge.to}`}
            d={edgePath(edge.from, edge.to)}
            fill="none"
            stroke={edge.danger ? "var(--color-state-danger)" : "var(--color-text-muted)"}
            strokeWidth={1.5}
            strokeDasharray={edge.dashed ? "4 4" : undefined}
            markerEnd={edge.danger ? "url(#arrow-danger)" : "url(#arrow)"}
          />
        ))}
        {dagNodes.map((node) => (
          <g key={node.id}>
            <rect
              x={node.x}
              y={node.y}
              width={NODE_W}
              height={NODE_H}
              rx={6}
              fill="var(--color-bg-surface)"
              stroke="var(--color-border-default)"
              strokeWidth={1}
            />
            <text
              x={node.x + NODE_W / 2}
              y={node.y + NODE_H / 2 + 4}
              textAnchor="middle"
              fontSize={10}
              fontWeight={600}
              fill="var(--color-text-primary)"
            >
              {node.label}
            </text>
          </g>
        ))}
      </svg>
    </CausalChartCard>
  );
}
