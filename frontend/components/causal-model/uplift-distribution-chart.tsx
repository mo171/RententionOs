"use client";

import { useCausalModelStore } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

const chartConfig = {
  control: { label: "Control", color: "var(--color-text-muted)" },
  treated: { label: "Treated", color: "var(--color-primary)" },
};

export function UpliftDistributionChart() {
  const upliftDistribution = useCausalModelStore((s) => s.upliftDistribution);

  return (
    <CausalChartCard
      subtitle="Treated vs control responders"
      title="Uplift score distribution"
      className="min-h-[280px]"
    >
      <ChartContainer config={chartConfig} className="h-[220px] w-full">
        <BarChart data={upliftDistribution} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="bucket" tickLine={false} axisLine={false} fontSize={10} />
          <YAxis tickLine={false} axisLine={false} fontSize={10} width={28} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar dataKey="control" fill="var(--color-control)" radius={[2, 2, 0, 0]} />
          <Bar dataKey="treated" fill="var(--color-treated)" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ChartContainer>
    </CausalChartCard>
  );
}
