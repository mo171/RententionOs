"use client";

import { cn } from "@/lib/utils";

interface CausalChartCardProps {
  subtitle: string;
  title: string;
  badge?: string;
  className?: string;
  children: React.ReactNode;
}

export function CausalChartCard({
  subtitle,
  title,
  badge,
  className,
  children,
}: CausalChartCardProps) {
  return (
    <div
      className={cn(
        "bg-bg-surface border border-border-default rounded-xl p-5 flex flex-col animate-in fade-in duration-300",
        className
      )}
    >
      <div className="flex items-start justify-between mb-4 flex-shrink-0">
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
            {subtitle}
          </span>
          <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
        </div>
        {badge && (
          <span className="text-[10px] font-bold text-state-safe bg-state-safe-dim px-2 py-0.5 rounded-full">
            {badge}
          </span>
        )}
      </div>
      <div className="flex-1 min-h-0">{children}</div>
    </div>
  );
}
