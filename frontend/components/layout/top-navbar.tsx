"use client";

import { usePathname } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

const PAGE_META: Record<string, { title: string; subtitle: string }> = {
  "/overview": { title: "Overview", subtitle: "Live agent activity" },
  "/approvals": { title: "Approvals", subtitle: "Actions held for review" },
  "/causal-model": {
    title: "Causal model",
    subtitle: "Drivers, uplift curves, validation",
  },
};

const DEFAULT_META = { title: "RetentionOS", subtitle: "" };

export function TopNavbar() {
  const pathname = usePathname();
  const meta = PAGE_META[pathname] ?? DEFAULT_META;

  return (
    <header className="h-[60px] flex-shrink-0 flex items-center justify-between px-6 bg-background border-b border-border-default sticky top-0 z-10">
      <div className="flex items-baseline gap-3">
        <h1 className="text-lg font-semibold text-text-primary">{meta.title}</h1>
        {meta.subtitle && (
          <span className="text-sm font-medium text-text-muted">{meta.subtitle}</span>
        )}
      </div>

      <div className="flex items-center gap-4">
        <button
          type="button"
          className="text-text-muted hover:text-text-primary transition-colors flex items-center justify-center"
          aria-label="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border-default bg-bg-surface">
          <div className="w-2 h-2 rounded-full bg-state-safe" />
          <span className="text-xs font-semibold text-text-primary">Autonomous on</span>
        </div>

        <Button className="shadow-primary bg-primary text-primary-foreground hover:bg-primary/90 h-8 px-4 text-xs font-semibold rounded-md flex items-center gap-2 transition-all duration-150">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          Ask agent
        </Button>
      </div>
    </header>
  );
}
