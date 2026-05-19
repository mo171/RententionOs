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
  Line,
  LineChart,
  XAxis,
  YAxis,
} from "recharts";

const chartConfig = {
  model: { label: "Model", color: "var(--color-primary)" },
  baseline: { label: "Baseline", color: "var(--color-state-warning)" },
  random: { label: "Random", color: "var(--color-text-muted)" },
};

export function QiniCurveChart() {
  const qiniCurve = useCausalModelStore((s) => s.qiniCurve);
  const auuc = useCausalModelStore((s) => s.summary.auuc);

  return (
    <CausalChartCard
      subtitle="Model vs baselines"
      title="Qini curve"
      badge={`AUUC ${auuc.toFixed(2)}`}
      className="min-h-[320px]"
    >
      <ChartContainer config={chartConfig} className="h-[240px] w-full">
        <LineChart data={qiniCurve} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="pctTreated"
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}%`}
            fontSize={10}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${Math.round(Number(v) * 100)}%`}
            fontSize={10}
            width={36}
          />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Line
            type="monotone"
            dataKey="model"
            stroke="var(--color-model)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="baseline"
            stroke="var(--color-baseline)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="random"
            stroke="var(--color-random)"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            dot={false}
          />
        </LineChart>
      </ChartContainer>
      <p className="text-[10px] text-text-muted text-center mt-1 uppercase tracking-wider">
        % treated · retained
      </p>
    </CausalChartCard>
  );
}
