"use client";

import { Fragment } from "react";
import { useCausalModelStore } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";
import { cn } from "@/lib/utils";

export function TreatmentHeatmap() {
  const heatmapSegments = useCausalModelStore((s) => s.heatmapSegments);
  const heatmapTreatments = useCausalModelStore((s) => s.heatmapTreatments);
  const treatmentHeatmap = useCausalModelStore((s) => s.treatmentHeatmap);

  const lifts = treatmentHeatmap.map((c) => c.lift);
  const minLift = Math.min(...lifts);
  const maxLift = Math.max(...lifts);

  const getLift = (segment: string, treatment: string) =>
    treatmentHeatmap.find((c) => c.segment === segment && c.treatment === treatment)?.lift ?? 0;

  const cellOpacity = (lift: number) => {
    if (maxLift === minLift) return 0.5;
    return 0.25 + ((lift - minLift) / (maxLift - minLift)) * 0.75;
  };

  return (
    <CausalChartCard
      subtitle="Lift × segment heatmap"
      title="Treatment effect by segment"
      className="min-h-[280px]"
    >
      <div className="overflow-x-auto">
        <div
          className="grid gap-1 min-w-[280px]"
          style={{
            gridTemplateColumns: `72px repeat(${heatmapTreatments.length}, 1fr)`,
          }}
        >
          <div />
          {heatmapTreatments.map((t) => (
            <div
              key={t}
              className="text-[9px] font-bold text-text-muted uppercase text-center py-1"
            >
              {t}
            </div>
          ))}
          {heatmapSegments.map((segment) => (
            <Fragment key={segment}>
              <div className="text-[10px] font-medium text-text-secondary flex items-center pr-2">
                {segment}
              </div>
              {heatmapTreatments.map((treatment) => {
                const lift = getLift(segment, treatment);
                return (
                  <div
                    key={`${segment}-${treatment}`}
                    className={cn(
                      "rounded-md flex items-center justify-center text-[11px] font-bold text-white min-h-[36px]",
                      "bg-state-safe"
                    )}
                    style={{ opacity: cellOpacity(lift) }}
                  >
                    +{lift}
                  </div>
                );
              })}
            </Fragment>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-2 mt-3 text-[9px] text-text-muted">
        <span>Low</span>
        <div className="flex-1 h-1.5 rounded-full bg-gradient-to-r from-state-safe/30 to-state-safe" />
        <span>High lift</span>
      </div>
    </CausalChartCard>
  );
}
