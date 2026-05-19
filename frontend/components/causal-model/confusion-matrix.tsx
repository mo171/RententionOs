"use client";

import { useCausalModelStore } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";
import { cn } from "@/lib/utils";

export function ConfusionMatrixChart() {
  const { tp, fp, fn, tn, precision, recall, f1 } = useCausalModelStore(
    (s) => s.confusion
  );

  return (
    <CausalChartCard
      subtitle="Threshold = 0.5"
      title="Confusion — risk model"
      className="min-h-[260px]"
    >
      <div className="grid grid-cols-2 gap-2 flex-1">
        <div className={cn("rounded-lg p-4 flex flex-col", "bg-state-safe-dim")}>
          <span className="text-[10px] font-bold text-state-safe uppercase">TP</span>
          <span className="text-2xl font-bold text-text-primary mt-1">{tp}</span>
          <span className="text-[10px] text-text-muted mt-1">True positive — saved</span>
        </div>
        <div className={cn("rounded-lg p-4 flex flex-col", "bg-state-warning-dim")}>
          <span className="text-[10px] font-bold text-state-warning uppercase">FP</span>
          <span className="text-2xl font-bold text-text-primary mt-1">{fp}</span>
          <span className="text-[10px] text-text-muted mt-1">False positive</span>
        </div>
        <div className={cn("rounded-lg p-4 flex flex-col", "bg-state-danger-dim")}>
          <span className="text-[10px] font-bold text-state-danger uppercase">FN</span>
          <span className="text-2xl font-bold text-text-primary mt-1">{fn}</span>
          <span className="text-[10px] text-text-muted mt-1">False negative</span>
        </div>
        <div className={cn("rounded-lg p-4 flex flex-col", "bg-accent-info-dim")}>
          <span className="text-[10px] font-bold text-accent-info uppercase">TN</span>
          <span className="text-2xl font-bold text-text-primary mt-1">{tn.toLocaleString()}</span>
          <span className="text-[10px] text-text-muted mt-1">True negative</span>
        </div>
      </div>
      <div className="flex justify-between mt-4 pt-3 border-t border-border-divider text-[11px] text-text-secondary">
        <span>
          Precision <strong className="text-text-primary">{precision.toFixed(2)}</strong>
        </span>
        <span>
          Recall <strong className="text-text-primary">{recall.toFixed(2)}</strong>
        </span>
        <span>
          F1 <strong className="text-text-primary">{f1.toFixed(2)}</strong>
        </span>
      </div>
    </CausalChartCard>
  );
}
