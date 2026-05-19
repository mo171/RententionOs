"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  CheckCircle,
  Users,
  PenTool,
  Megaphone,
  Activity,
  MoreHorizontal,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const navItems = [
  { name: "Overview", href: "/overview", icon: LayoutDashboard },
  { name: "Approvals", href: "/approvals", icon: CheckCircle, badge: 3 },
  { name: "Customers", href: "/customers", icon: Users },
  { name: "Designer", href: "/designer", icon: PenTool },
  { name: "Campaigns", href: "/campaigns", icon: Megaphone },
  { name: "Causal model", href: "/causal-model", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-[240px] flex-shrink-0 flex flex-col h-screen bg-sidebar border-r border-sidebar-border text-sidebar-foreground p-4">
      {/* Brand Header */}
      <div className="flex items-center gap-2 px-2 mb-6">
        <div className="bg-primary/20 p-1 rounded-md text-primary">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
          </svg>
        </div>
        <div className="flex flex-col">
          <span className="font-semibold text-sm leading-tight text-text-primary">RetentionOS</span>
          <span className="text-[10px] font-medium text-text-muted uppercase tracking-wider">
            Autonomous - V2.3
          </span>
        </div>
      </div>

      {/* Agent Live Status Card */}
      <div className="bg-state-safe-dim border border-state-safe/20 rounded-lg p-3 mb-6">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-2 h-2 rounded-full bg-state-safe" />
          <span className="text-xs font-semibold text-state-safe uppercase tracking-wider">
            Agent · Live
          </span>
        </div>
        <p className="text-sm text-text-secondary">Scoring 1,284 accounts</p>
      </div>

      {/* Navigation */}
      <div className="mb-2">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider px-2 mb-2">
          Workspace
        </h3>
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-2 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-bg-hover text-text-primary"
                    : "text-text-secondary hover:bg-bg-hover/50 hover:text-text-primary"
                )}
              >
                <item.icon className={cn("w-4 h-4", isActive ? "text-primary" : "text-text-muted")} />
                <span className="flex-1">{item.name}</span>
                {item.badge && (
                  <span className="bg-amber-100 text-amber-700 text-[10px] font-bold px-1.5 py-0.5 rounded-full flex items-center justify-center min-w-[20px]">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex-grow" />

      {/* User Profile */}
      <div className="flex items-center gap-3 px-2 py-2 mt-auto">
        <Avatar className="w-8 h-8">
          <AvatarFallback className="bg-bg-hover text-text-primary text-xs font-medium">
            MK
          </AvatarFallback>
        </Avatar>
        <div className="flex flex-col flex-1 overflow-hidden">
          <span className="text-sm font-medium text-text-primary truncate">Mira Kovac</span>
          <span className="text-xs text-text-muted truncate">Head of Retention</span>
        </div>
        <button className="text-text-muted hover:text-text-primary transition-colors">
          <MoreHorizontal className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
