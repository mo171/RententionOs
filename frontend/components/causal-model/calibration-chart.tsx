"use client";

import { useCausalModelStore } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  CartesianGrid,
  ReferenceLine,
  Scatter,
  ScatterChart,
  XAxis,
  YAxis,
} from "recharts";

const chartConfig = {
  observed: { label: "Observed", color: "var(--color-accent-ai)" },
};

export function CalibrationChart() {
  const calibration = useCausalModelStore((s) => s.calibration);

  return (
    <CausalChartCard
      subtitle="Predicted vs observed"
      title="Calibration"
      className="min-h-[320px]"
    >
      <ChartContainer config={chartConfig} className="h-[240px] w-full">
        <ScatterChart margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="predicted"
            domain={[0, 1]}
            tickLine={false}
            axisLine={false}
            fontSize={10}
            name="Predicted"
          />
          <YAxis
            type="number"
            dataKey="observed"
            domain={[0, 1]}
            tickLine={false}
            axisLine={false}
            fontSize={10}
            width={36}
            name="Observed"
          />
          <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="var(--color-border-default)" strokeDasharray="4 4" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Scatter data={calibration} fill="var(--color-observed)" />
        </ScatterChart>
      </ChartContainer>
    </CausalChartCard>
  );
}
