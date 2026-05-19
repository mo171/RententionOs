"use client";

import { useCausalModelStore } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis } from "recharts";

const SHAP_COLORS = [
  "var(--color-accent-ai)",
  "var(--color-chart-3)",
  "var(--color-chart-1)",
  "var(--color-chart-4)",
  "var(--color-state-warning)",
  "var(--color-text-muted)",
];

const chartConfig = {
  value: { label: "|Φ|", color: "var(--color-accent-ai)" },
};

export function FeatureImportanceChart() {
  const featureImportance = useCausalModelStore((s) => s.featureImportance);

  return (
    <CausalChartCard
      subtitle="SHAP values, mean |Φ|"
      title="Feature importance"
      className="min-h-[280px]"
    >
      <ChartContainer config={chartConfig} className="h-[220px] w-full">
        <BarChart
          data={featureImportance}
          layout="vertical"
          margin={{ top: 4, right: 24, left: 4, bottom: 4 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" domain={[0, 0.4]} tickLine={false} axisLine={false} fontSize={10} />
          <YAxis
            type="category"
            dataKey="feature"
            tickLine={false}
            axisLine={false}
            width={120}
            fontSize={10}
          />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {featureImportance.map((_, i) => (
              <Cell key={i} fill={SHAP_COLORS[i % SHAP_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>
    </CausalChartCard>
  );
}
