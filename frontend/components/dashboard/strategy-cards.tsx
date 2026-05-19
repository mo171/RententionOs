"use client";

import { SlidersHorizontal, Zap, Tag, BookOpen, Lightbulb, Plus } from "lucide-react";
import { useDashboardStore } from "@/store/dashboard-store";
import { cn } from "@/lib/utils";

const strategyIcons = [Zap, Tag, BookOpen, Lightbulb];
const strategyColors = [
  { bar: "bg-state-safe", impact: "text-state-safe" },
  { bar: "bg-accent-ai", impact: "text-accent-ai" },
  { bar: "bg-accent-info", impact: "text-accent-info" },
  { bar: "bg-state-warning", impact: "text-state-warning" },
];
const strategyBgs = [
  "bg-state-safe-dim",
  "bg-accent-ai-dim",
  "bg-accent-info-dim",
  "bg-state-warning-dim",
];

export function StrategyCards() {
  const { strategies } = useDashboardStore();

  return (
    <div className="flex flex-col gap-4">
      {/* Section header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-1">Last 90 Days</p>
          <h2 className="text-base font-semibold text-text-primary">Top Performing Strategies</h2>
        </div>
        <button className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors border border-border-default rounded-lg px-3 py-1.5">
          <SlidersHorizontal className="w-3 h-3" />
          Filter
        </button>
      </div>

      {/* Strategy cards grid */}
      <div className="grid grid-cols-4 gap-3">
        {strategies.map((strategy, i) => {
          const Icon = strategyIcons[i % strategyIcons.length];
          const colors = strategyColors[i % strategyColors.length];
          const bg = strategyBgs[i % strategyBgs.length];
          return (
            <div
              key={strategy.id}
              className="bg-bg-surface border border-border-default rounded-xl p-4 hover:-translate-y-0.5 transition-transform duration-150 will-change-transform cursor-default"
            >
              <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center mb-3", bg)}>
                <Icon className={cn("w-4 h-4", colors.impact)} />
              </div>
              <p className="text-sm font-medium text-text-primary leading-snug mb-3">{strategy.title}</p>
              <div className="flex items-end justify-between mb-2">
                <div>
                  <p className="text-2xl font-bold text-text-primary">{strategy.successRate}%</p>
                  <p className="text-[10px] text-text-muted uppercase tracking-wider">Success Rate</p>
                </div>
                <p className={cn("text-sm font-bold", colors.impact)}>{strategy.impact}</p>
              </div>
              {/* Progress bar */}
              <div className="h-1 bg-bg-hover rounded-full overflow-hidden">
                <div
                  className={cn("h-full rounded-full transition-all duration-700", colors.bar)}
                  style={{ width: `${strategy.successRate}%` }}
                />
              </div>
              <p className="text-[10px] text-text-muted uppercase tracking-wider mt-1">Impact</p>
            </div>
          );
        })}

        {/* Build New Strategy card */}
        <div className="bg-bg-surface border border-dashed border-border-strong rounded-xl p-4 flex flex-col items-center justify-center gap-2 hover:-translate-y-0.5 hover:border-primary/40 transition-transform duration-150 will-change-transform cursor-pointer group">
          <div className="w-8 h-8 rounded-lg bg-accent-primary-dim flex items-center justify-center group-hover:bg-primary/20 transition-colors">
            <Plus className="w-4 h-4 text-accent-primary" />
          </div>
          <p className="text-sm font-medium text-text-primary text-center">Build New Strategy</p>
          <p className="text-[10px] text-accent-primary font-medium">Open the designer →</p>
        </div>
      </div>
    </div>
  );
}
