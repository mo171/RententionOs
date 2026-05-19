"use client";

import { TrendingUp, TrendingDown } from "lucide-react";
import { useDashboardStore } from "@/store/dashboard-store";

function MiniSparkline({ up }: { up: boolean }) {
  return (
    <svg width="60" height="24" viewBox="0 0 60 24" fill="none" className="flex-shrink-0">
      {up ? (
        <polyline
          points="0,20 10,16 20,18 30,12 40,10 50,6 60,2"
          stroke="#26B36A"
          strokeWidth="1.5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : (
        <polyline
          points="0,4 10,8 20,6 30,12 40,14 50,18 60,20"
          stroke="#DF5B3D"
          strokeWidth="1.5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
    </svg>
  );
}

function MiniDonut() {
  const r = 10;
  const cx = 14;
  const cy = 14;
  const circ = 2 * Math.PI * r;
  const filled = circ * 0.942;
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" className="flex-shrink-0">
      <circle cx={cx} cy={cy} r={r} stroke="#E7E2D8" strokeWidth="3.5" fill="none" />
      <circle
        cx={cx}
        cy={cy}
        r={r}
        stroke="#4D84FF"
        strokeWidth="3.5"
        fill="none"
        strokeDasharray={`${filled} ${circ}`}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}
      />
    </svg>
  );
}

export function KpiCards() {
  const { savedRevenue, netChurnRate, aiPrecision } = useDashboardStore();

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Saved Revenue */}
      <div className="bg-bg-surface border border-border-default rounded-xl p-5 flex flex-col gap-3 hover:-translate-y-0.5 transition-transform duration-150 will-change-transform cursor-default">
        <div className="flex items-start justify-between">
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider">Saved Revenue</p>
          <MiniSparkline up={true} />
        </div>
        <div>
          <p className="text-3xl font-bold text-text-primary tracking-tight">{savedRevenue.value}</p>
          <span className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 rounded-full bg-state-safe-dim text-state-safe text-xs font-semibold">
            <TrendingUp className="w-3 h-3" />
            {savedRevenue.trend}
          </span>
        </div>
      </div>

      {/* Net Churn Rate */}
      <div className="bg-bg-surface border border-border-default rounded-xl p-5 flex flex-col gap-3 hover:-translate-y-0.5 transition-transform duration-150 will-change-transform cursor-default">
        <div className="flex items-start justify-between">
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider">Net Churn Rate</p>
          <MiniSparkline up={false} />
        </div>
        <div>
          <p className="text-3xl font-bold text-text-primary tracking-tight">{netChurnRate.value}</p>
          <span className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 rounded-full bg-state-safe-dim text-state-safe text-xs font-semibold">
            <TrendingDown className="w-3 h-3" />
            {netChurnRate.trend}
          </span>
        </div>
      </div>

      {/* AI Precision */}
      <div className="bg-bg-surface border border-border-default rounded-xl p-5 flex flex-col gap-3 hover:-translate-y-0.5 transition-transform duration-150 will-change-transform cursor-default">
        <div className="flex items-start justify-between">
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider">AI Precision</p>
          <MiniDonut />
        </div>
        <div>
          <p className="text-3xl font-bold text-text-primary tracking-tight">{aiPrecision.value}</p>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-accent-info-dim text-accent-info text-xs font-semibold">
              High Confidence
            </span>
            <p className="text-xs text-text-muted">in latest cohort</p>
          </div>
        </div>
      </div>
    </div>
  );
}
