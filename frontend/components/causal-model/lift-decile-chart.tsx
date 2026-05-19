"use client";

import { useCausalModelStore, LiftDecileTier } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, XAxis, YAxis } from "recharts";

const TIER_FILL: Record<LiftDecileTier, string> = {
  high: "var(--color-primary)",
  mid: "var(--color-accent-ai)",
  low: "var(--color-text-muted)",
};

const chartConfig = {
  lift: { label: "Lift", color: "var(--color-primary)" },
};

export function LiftDecileChart() {
  const liftDeciles = useCausalModelStore((s) => s.liftDeciles);

  return (
    <CausalChartCard
      subtitle="Decile chart"
      title="Lift / cumulative gain"
      className="min-h-[260px]"
    >
      <ChartContainer config={chartConfig} className="h-[200px] w-full">
        <BarChart data={liftDeciles} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="decile" tickLine={false} axisLine={false} fontSize={10} />
          <YAxis tickLine={false} axisLine={false} fontSize={10} width={28} />
          <ReferenceLine y={1} stroke="var(--color-border-strong)" strokeDasharray="4 4" label={{ value: "Baseline 1.0", fontSize: 9, position: "insideTopRight" }} />
          <ChartTooltip
            content={<ChartTooltipContent formatter={(v) => [`${v}+`, "Lift"]} />}
          />
          <Bar dataKey="lift" radius={[4, 4, 0, 0]}>
            {liftDeciles.map((entry) => (
              <Cell key={entry.decile} fill={TIER_FILL[entry.tier]} />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>
    </CausalChartCard>
  );
}
