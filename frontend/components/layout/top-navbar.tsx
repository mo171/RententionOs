"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export function TopNavbar() {
  return (
    <header className="h-[60px] flex-shrink-0 flex items-center justify-between px-6 bg-background border-b border-border-default sticky top-0 z-10">
      {/* Left section: Title & Context */}
      <div className="flex items-baseline gap-3">
        <h1 className="text-lg font-semibold text-text-primary">Overview</h1>
        <span className="text-sm font-medium text-text-muted">Live agent activity</span>
      </div>

      {/* Right section: Controls */}
      <div className="flex items-center gap-4">
        {/* Refresh Action */}
        <button className="text-text-muted hover:text-text-primary transition-colors flex items-center justify-center">
          <RefreshCw className="w-4 h-4" />
        </button>

        {/* Autonomous Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border-default bg-bg-surface">
          <div className="w-2 h-2 rounded-full bg-state-safe" />
          <span className="text-xs font-semibold text-text-primary">Autonomous on</span>
        </div>

        {/* Ask Agent CTA */}
        <Button className="shadow-primary bg-primary text-primary-foreground hover:bg-primary/90 h-8 px-4 text-xs font-semibold rounded-md flex items-center gap-2 transition-all duration-150">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          Ask agent
        </Button>
      </div>
    </header>
  );
}
