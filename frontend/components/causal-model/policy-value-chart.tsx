"use client";

import { useCausalModelStore, PolicyBar } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";
import { cn } from "@/lib/utils";

const COLOR_MAP: Record<PolicyBar["colorKey"], string> = {
  primary: "bg-primary",
  warning: "bg-state-warning",
  info: "bg-accent-info",
  ai: "bg-accent-ai",
  muted: "bg-text-faint",
};

export function PolicyValueChart() {
  const policyValue = useCausalModelStore((s) => s.policyValue);

  return (
    <CausalChartCard
      subtitle="Off-policy evaluation"
      title="Policy value"
      className="min-h-[260px]"
    >
      <div className="flex flex-col gap-3 py-2">
        {policyValue.map((row) => (
          <div key={row.policy} className="flex flex-col gap-1">
            <div className="flex justify-between text-[11px]">
              <span className="font-medium text-text-secondary">{row.policy}</span>
              <span className="font-bold text-text-primary">{row.value.toFixed(2)}</span>
            </div>
            <div className="h-2 bg-bg-hover rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-300",
                  COLOR_MAP[row.colorKey],
                  row.value === 0 && "h-0.5 mt-0.5"
                )}
                style={{ width: `${Math.max(row.value * 100, row.value === 0 ? 2 : 4)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </CausalChartCard>
  );
}
