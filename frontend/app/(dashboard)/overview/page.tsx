import { KpiCards } from "@/components/dashboard/kpi-cards";
import { RevenueFlowChart } from "@/components/dashboard/revenue-flow-chart";
import { AlertCenter } from "@/components/dashboard/alert-center";
import { StrategyCards } from "@/components/dashboard/strategy-cards";

export default function OverviewPage() {
  return (
    <div className="flex flex-col gap-6 max-w-[1400px]">
      {/* Row 1: KPI cards — full width */}
      <KpiCards />

      {/* Row 2: Revenue Flow Chart (left) + Alert Center (right) */}
      <div className="grid grid-cols-[1fr_340px] gap-4 items-start">
        <RevenueFlowChart />
        <AlertCenter />
      </div>

      {/* Row 3: Top Performing Strategies — full width */}
      <StrategyCards />
    </div>
  );
}
