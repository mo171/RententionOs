"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useDashboardStore, Alert } from "@/store/dashboard-store";

const riskConfig = {
  High: {
    label: "High Risk",
    badgeClass: "bg-state-danger-dim text-state-danger",
    borderClass: "border-l-state-danger",
    actionClass: "bg-state-danger text-white hover:bg-state-danger/90",
  },
  Medium: {
    label: "Medium Risk",
    badgeClass: "bg-state-warning-dim text-state-warning",
    borderClass: "border-l-state-warning",
    actionClass: "bg-primary text-white hover:bg-primary/90",
  },
  Low: {
    label: "Low Risk",
    badgeClass: "bg-state-safe-dim text-state-safe",
    borderClass: "border-l-state-safe",
    actionClass: "bg-primary text-white hover:bg-primary/90",
  },
};

function AlertCard({ alert }: { alert: Alert }) {
  const config = riskConfig[alert.risk];
  return (
    <div
      className={cn(
        "p-4 border-l-4 border border-border-default rounded-r-lg bg-bg-surface hover:opacity-90 hover:-translate-y-px transition-transform duration-150 will-change-transform",
        config.borderClass
      )}
    >
      <div className="flex items-start justify-between mb-1.5">
        <span className="text-sm font-semibold text-text-primary">{alert.company}</span>
        <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full", config.badgeClass)}>
          {config.label}
        </span>
      </div>
      <p className="text-xs text-text-secondary mb-3 leading-relaxed">{alert.summary}</p>
      <div className="flex items-center gap-2 justify-end">
        <button className="text-xs text-text-muted hover:text-text-primary transition-colors px-2 py-1">
          Ignore
        </button>
        {alert.actions.slice(1).map((action) => (
          <button
            key={action}
            className={cn(
              "text-xs font-semibold px-3 py-1.5 rounded-md transition-colors",
              config.actionClass
            )}
          >
            {action}
          </button>
        ))}
      </div>
    </div>
  );
}

export function AlertCenter() {
  const { alerts } = useDashboardStore();
  const [showAll, setShowAll] = useState(false);

  const visibleAlerts = showAll ? alerts : alerts.slice(0, 3);
  const highRiskCount = alerts.filter((a) => a.risk === "High" || a.risk === "Medium").length;

  return (
    <div className="bg-bg-surface border border-border-default rounded-xl flex flex-col" style={{ height: "100%" }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-border-divider flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-state-danger animate-pulse" />
          <span className="text-sm font-semibold text-text-primary">Alert Center</span>
        </div>
        {highRiskCount > 0 && (
          <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-state-danger-dim text-state-danger">
            {highRiskCount} Require Action
          </span>
        )}
      </div>

      {/* Alert list — fixed height, scrolls internally if showing all */}
      <div
        className={cn(
          "flex flex-col gap-3 p-4 overflow-y-auto flex-1",
          showAll ? "max-h-[420px]" : "max-h-[360px]"
        )}
      >
        {visibleAlerts.map((alert) => (
          <AlertCard key={alert.id} alert={alert} />
        ))}
      </div>

      {/* View All / Collapse toggle */}
      {alerts.length > 3 && (
        <div className="border-t border-border-divider px-5 py-3 flex-shrink-0">
          <button
            onClick={() => setShowAll((s) => !s)}
            className="w-full text-xs font-semibold text-accent-primary hover:text-accent-primary-text transition-colors text-center"
          >
            {showAll ? "Show less ↑" : `View all ${alerts.length} alerts →`}
          </button>
        </div>
      )}
    </div>
  );
}
