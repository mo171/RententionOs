"use client";

import { useCausalModelStore } from "@/store/causal-model-store";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function MetricCell({
  label,
  value,
  delta,
}: {
  label: string;
  value: string;
  delta?: string;
}) {
  return (
    <div className="flex flex-col gap-0.5 px-4 py-3 border-r border-border-divider last:border-r-0 min-w-[100px]">
      <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
        {label}
      </span>
      <div className="flex items-baseline gap-2">
        <span className="text-sm font-bold text-text-primary">{value}</span>
        {delta && (
          <span className="text-[10px] font-semibold text-state-safe">+ {delta}</span>
        )}
      </div>
    </div>
  );
}

export function ModelMetricsStrip() {
  const { summary, retrainInProgress, setRetrainInProgress } = useCausalModelStore();

  return (
    <div className="bg-bg-surface border border-border-default rounded-xl flex items-stretch overflow-hidden">
      <div className="flex flex-1 flex-wrap">
        <MetricCell label="Model" value={summary.modelVersion} />
        <MetricCell
          label="AUUC"
          value={summary.auuc.toFixed(2)}
          delta={summary.auucDelta.toFixed(2)}
        />
        <MetricCell label="Calibration" value={summary.calibration.toFixed(2)} />
        <MetricCell
          label="Coverage"
          value={`${summary.coverage}%`}
          delta={`${summary.coverageDelta}pp`}
        />
        <MetricCell label="Drift (PSI)" value={summary.driftPsi.toFixed(2)} />
        <MetricCell label="Last retrain" value={summary.lastRetrain} />
        <MetricCell
          label="Outcomes"
          value={summary.outcomes.toLocaleString()}
        />
      </div>
      <div className="flex items-center px-4 border-l border-border-divider">
        <Button
          className={cn(
            "shadow-primary h-8 px-4 text-xs font-semibold",
            retrainInProgress && "opacity-70"
          )}
          disabled={retrainInProgress}
          onClick={() => {
            setRetrainInProgress(true);
            setTimeout(() => setRetrainInProgress(false), 2000);
          }}
        >
          {retrainInProgress ? "Retraining…" : "Retrain now"}
        </Button>
      </div>
    </div>
  );
}
