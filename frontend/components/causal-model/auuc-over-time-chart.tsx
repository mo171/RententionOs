"use client";

import { useCausalModelStore } from "@/store/causal-model-store";
import { CausalChartCard } from "@/components/causal-model/causal-chart-card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts";

const chartConfig = {
  auuc: { label: "AUUC", color: "var(--color-primary)" },
};

export function AuucOverTimeChart() {
  const auucOverTime = useCausalModelStore((s) => s.auucOverTime);
  const auucTarget = useCausalModelStore((s) => s.auucTarget);

  return (
    <CausalChartCard
      subtitle="Weekly · 12-week trail"
      title="AUUC over time"
      className="min-h-[260px]"
    >
      <ChartContainer config={chartConfig} className="h-[200px] w-full">
        <AreaChart data={auucOverTime} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="week" tickLine={false} axisLine={false} fontSize={10} />
          <YAxis
            domain={[0.5, 0.8]}
            tickLine={false}
            axisLine={false}
            fontSize={10}
            width={32}
          />
          <ReferenceLine
            y={auucTarget}
            stroke="var(--color-state-warning)"
            strokeDasharray="4 4"
            label={{ value: `Target ${auucTarget}`, position: "insideTopRight", fontSize: 10 }}
          />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Area
            type="monotone"
            dataKey="auuc"
            stroke="var(--color-auuc)"
            fill="var(--color-auuc)"
            fillOpacity={0.15}
            strokeWidth={2}
            dot={{ r: 3, fill: "var(--color-auuc)" }}
          />
        </AreaChart>
      </ChartContainer>
    </CausalChartCard>
  );
}
