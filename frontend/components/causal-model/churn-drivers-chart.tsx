"use client";

import { useCausalModelStore } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";
import { cn } from "@/lib/utils";

const MAX_PP = 20;

export function ChurnDriversChart() {
  const churnDrivers = useCausalModelStore((s) => s.churnDrivers);

  return (
    <CausalChartCard
      subtitle="Estimated effect · doubly-robust IPW"
      title="Top churn drivers"
      className="min-h-[320px]"
    >
      <div className="flex flex-col gap-3">
        {churnDrivers.map((driver) => {
          const isRisk = driver.direction === "risk";
          const width = `${Math.min((driver.effectPp / MAX_PP) * 100, 100)}%`;
          return (
            <div key={driver.label} className="flex flex-col gap-1">
              <div className="flex justify-between items-baseline text-[11px]">
                <span className="text-text-secondary font-medium truncate pr-2">
                  {driver.label}
                </span>
                <span className="text-text-muted flex-shrink-0">n={driver.n}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-bg-hover rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-300",
                      isRisk ? "bg-state-danger" : "bg-state-safe"
                    )}
                    style={{ width }}
                  />
                </div>
                <span
                  className={cn(
                    "text-[11px] font-bold w-10 text-right flex-shrink-0",
                    isRisk ? "text-state-danger" : "text-state-safe"
                  )}
                >
                  {isRisk ? "+" : "-"}
                  {driver.effectPp}pp
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </CausalChartCard>
  );
}
