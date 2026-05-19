"use client";

import { useCausalModelStore } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";
import { cn } from "@/lib/utils";

function MiniSparkline({ values, trend }: { values: number[]; trend: "up" | "down" | "flat" }) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const w = 72;
  const h = 24;
  const points = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / range) * (h - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");

  const stroke =
    trend === "up"
      ? "var(--color-state-safe)"
      : trend === "down"
        ? "var(--color-accent-info)"
        : "var(--color-text-muted)";

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="flex-shrink-0">
      <polyline
        points={points}
        fill="none"
        stroke={stroke}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function HoldoutOutcomes() {
  const holdoutOutcomes = useCausalModelStore((s) => s.holdoutOutcomes);

  return (
    <CausalChartCard
      subtitle="14d post-treatment"
      title="Holdout outcomes"
      className="min-h-[260px]"
    >
      <div className="flex flex-col gap-4">
        {holdoutOutcomes.map((outcome) => (
          <div
            key={outcome.label}
            className="flex items-center justify-between gap-3 py-2 border-b border-border-divider last:border-b-0"
          >
            <div className="flex flex-col gap-0.5 min-w-0">
              <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                {outcome.label}
              </span>
              <span
                className={cn(
                  "text-lg font-bold",
                  outcome.trend === "up" && "text-state-safe",
                  outcome.trend === "down" && "text-accent-info",
                  outcome.trend === "flat" && "text-text-primary"
                )}
              >
                {outcome.value}
              </span>
            </div>
            <MiniSparkline values={outcome.sparkline} trend={outcome.trend} />
          </div>
        ))}
      </div>
    </CausalChartCard>
  );
}
