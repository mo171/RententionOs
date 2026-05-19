"use client";

export function RevenueFlowChart() {
  // Static SVG Sankey-style flow chart matching the reference image
  // Left: AT-RISK (1,284), Middle: INTERVENED (842) + SKIPPED (442), Right: RETAINED (634) + LOST (650)

  const w = 560;
  const h = 280;

  // Node positions
  const nodes = {
    atRisk: { x: 10, y: 60, w: 80, h: 160, color: "#FBCBC1", label: "AT-RISK", value: "1,284" },
    intervened: { x: 230, y: 20, w: 80, h: 120, color: "#C5BDF7", label: "INTERVENED", value: "842" },
    skipped: { x: 230, y: 155, w: 80, h: 80, color: "#CBD5E1", label: "SKIPPED", value: "442" },
    retained: { x: 450, y: 10, w: 80, h: 140, color: "#A7ECD0", label: "RETAINED", value: "634" },
    lost: { x: 450, y: 165, w: 80, h: 100, color: "#FBCBC1", label: "LOST", value: "650" },
  };

  // Flow paths - smooth bezier curves
  const flows = [
    // AT-RISK → INTERVENED (top flow)
    {
      d: `M ${nodes.atRisk.x + nodes.atRisk.w} ${nodes.atRisk.y + 20}
         C ${nodes.atRisk.x + nodes.atRisk.w + 70} ${nodes.atRisk.y + 20},
           ${nodes.intervened.x - 70} ${nodes.intervened.y + 20},
           ${nodes.intervened.x} ${nodes.intervened.y + 20}
         L ${nodes.intervened.x} ${nodes.intervened.y + nodes.intervened.h - 20}
         C ${nodes.intervened.x - 70} ${nodes.intervened.y + nodes.intervened.h - 20},
           ${nodes.atRisk.x + nodes.atRisk.w + 70} ${nodes.atRisk.y + 90},
           ${nodes.atRisk.x + nodes.atRisk.w} ${nodes.atRisk.y + 90} Z`,
      color: "#C5BDF7",
      opacity: 0.35,
    },
    // AT-RISK → SKIPPED (bottom flow)
    {
      d: `M ${nodes.atRisk.x + nodes.atRisk.w} ${nodes.atRisk.y + 100}
         C ${nodes.atRisk.x + nodes.atRisk.w + 70} ${nodes.atRisk.y + 120},
           ${nodes.skipped.x - 70} ${nodes.skipped.y + 10},
           ${nodes.skipped.x} ${nodes.skipped.y + 10}
         L ${nodes.skipped.x} ${nodes.skipped.y + nodes.skipped.h - 10}
         C ${nodes.skipped.x - 70} ${nodes.skipped.y + nodes.skipped.h - 10},
           ${nodes.atRisk.x + nodes.atRisk.w + 70} ${nodes.atRisk.y + 150},
           ${nodes.atRisk.x + nodes.atRisk.w} ${nodes.atRisk.y + 150} Z`,
      color: "#CBD5E1",
      opacity: 0.35,
    },
    // INTERVENED → RETAINED
    {
      d: `M ${nodes.intervened.x + nodes.intervened.w} ${nodes.intervened.y + 10}
         C ${nodes.intervened.x + nodes.intervened.w + 70} ${nodes.intervened.y + 10},
           ${nodes.retained.x - 70} ${nodes.retained.y + 20},
           ${nodes.retained.x} ${nodes.retained.y + 20}
         L ${nodes.retained.x} ${nodes.retained.y + nodes.retained.h - 20}
         C ${nodes.retained.x - 70} ${nodes.retained.y + nodes.retained.h - 20},
           ${nodes.intervened.x + nodes.intervened.w + 70} ${nodes.intervened.y + nodes.intervened.h - 10},
           ${nodes.intervened.x + nodes.intervened.w} ${nodes.intervened.y + nodes.intervened.h - 10} Z`,
      color: "#A7ECD0",
      opacity: 0.4,
    },
    // INTERVENED → LOST (small)
    {
      d: `M ${nodes.intervened.x + nodes.intervened.w} ${nodes.intervened.y + nodes.intervened.h - 10}
         C ${nodes.intervened.x + nodes.intervened.w + 50} ${nodes.intervened.y + nodes.intervened.h + 10},
           ${nodes.lost.x - 50} ${nodes.lost.y + 10},
           ${nodes.lost.x} ${nodes.lost.y + 10}
         L ${nodes.lost.x} ${nodes.lost.y + 30}
         C ${nodes.lost.x - 50} ${nodes.lost.y + 30},
           ${nodes.intervened.x + nodes.intervened.w + 50} ${nodes.intervened.y + nodes.intervened.h + 30},
           ${nodes.intervened.x + nodes.intervened.w} ${nodes.intervened.y + nodes.intervened.h + 10} Z`,
      color: "#FBCBC1",
      opacity: 0.35,
    },
    // SKIPPED → LOST
    {
      d: `M ${nodes.skipped.x + nodes.skipped.w} ${nodes.skipped.y + 10}
         C ${nodes.skipped.x + nodes.skipped.w + 70} ${nodes.skipped.y + 10},
           ${nodes.lost.x - 70} ${nodes.lost.y + 40},
           ${nodes.lost.x} ${nodes.lost.y + 40}
         L ${nodes.lost.x} ${nodes.lost.y + nodes.lost.h - 10}
         C ${nodes.lost.x - 70} ${nodes.lost.y + nodes.lost.h - 10},
           ${nodes.skipped.x + nodes.skipped.w + 70} ${nodes.skipped.y + nodes.skipped.h - 10},
           ${nodes.skipped.x + nodes.skipped.w} ${nodes.skipped.y + nodes.skipped.h - 10} Z`,
      color: "#FBCBC1",
      opacity: 0.35,
    },
  ];

  return (
    <div className="bg-bg-surface border border-border-default rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-1">Last 28 Days</p>
          <h2 className="text-base font-semibold text-text-primary">Revenue Uplift Flow</h2>
        </div>
        <button className="text-xs font-medium text-accent-primary hover:underline">
          View details →
        </button>
      </div>

      <div className="w-full overflow-x-auto">
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ minWidth: 400 }}>
          {/* Flow paths */}
          {flows.map((f, i) => (
            <path key={i} d={f.d} fill={f.color} opacity={f.opacity} className="transition-opacity hover:opacity-60" />
          ))}

          {/* Nodes */}
          {Object.values(nodes).map((n, i) => (
            <g key={i}>
              <rect x={n.x} y={n.y} width={n.w} height={n.h} rx={6} fill={n.color} />
              <text x={n.x + n.w / 2} y={n.y + n.h / 2 - 8} textAnchor="middle" fill="#6E6A62" fontSize="9" fontWeight="600" letterSpacing="0.5">
                {n.label}
              </text>
              <text x={n.x + n.w / 2} y={n.y + n.h / 2 + 10} textAnchor="middle" fill="#1F1E1A" fontSize="16" fontWeight="700">
                {n.value}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-text-muted border-t border-border-divider pt-3">
        <span>Showing customer flow from</span>
        <span className="text-state-danger font-medium">At-Risk</span>
        <span>→</span>
        <span className="text-accent-ai font-medium">Intervened</span>
        <span>→</span>
        <span className="text-state-safe font-medium">Retained</span>
        <span className="ml-auto font-medium text-text-secondary">49.4% retention vs 16.2% baseline</span>
      </div>
    </div>
  );
}
