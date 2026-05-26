"use client";

import { useLiveCausalModel } from "@/hooks/use-live-causal-model";
import { ModelMetricsStrip } from "@/components/causal-model/model-metrics-strip";
import { ChurnDriversChart } from "@/components/causal-model/churn-drivers-chart";
import { QiniCurveChart } from "@/components/causal-model/qini-curve-chart";
import { CalibrationChart } from "@/components/causal-model/calibration-chart";
import { UpliftDistributionChart } from "@/components/causal-model/uplift-distribution-chart";
import { FeatureImportanceChart } from "@/components/causal-model/feature-importance-chart";
import { TreatmentHeatmap } from "@/components/causal-model/treatment-heatmap";
import { AuucOverTimeChart } from "@/components/causal-model/auuc-over-time-chart";
import { PolicyValueChart } from "@/components/causal-model/policy-value-chart";
import { ConfusionMatrixChart } from "@/components/causal-model/confusion-matrix";
import { LiftDecileChart } from "@/components/causal-model/lift-decile-chart";
import { CausalDagChart } from "@/components/causal-model/causal-dag-chart";
import { HoldoutOutcomes } from "@/components/causal-model/holdout-outcomes";
import { LiveRiskFeed } from "@/components/LiveRiskFeed";
import { FinancialImpactMap } from "@/components/FinancialImpactMap";
import { GraphVisualization } from "@/components/GraphVisualization";

export default function CausalModelPage() {
  useLiveCausalModel();

  return (
    <div className="flex flex-col gap-4 max-w-[1400px] pb-8">
      <ModelMetricsStrip />
      
      {/* Gatekeeper Architecture MVP Components */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <LiveRiskFeed />
        <FinancialImpactMap />
        <GraphVisualization />
      </div>

      <div className="grid grid-cols-3 gap-4 mt-4">
        <ChurnDriversChart />
        <QiniCurveChart />
        <CalibrationChart />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <UpliftDistributionChart />
        <FeatureImportanceChart />
        <TreatmentHeatmap />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <AuucOverTimeChart />
        <PolicyValueChart />
        <ConfusionMatrixChart />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <LiftDecileChart />
        <CausalDagChart />
        <HoldoutOutcomes />
      </div>
    </div>
  );
}
