"use client";

import { cn } from "@/lib/utils";
import { Approval } from "@/store/approvals-store";

interface ApprovalListPanelProps {
  items: Approval[];
  selectedId: string;
  onSelect: (id: string) => void;
}

function timeAgo(isoString: string): string {
  const diff = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (diff < 3600) return `in ${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `in ${Math.floor(diff / 3600)}h`;
  return `in ${Math.floor(diff / 86400)}d`;
}

export function ApprovalListPanel({ items, selectedId, onSelect }: ApprovalListPanelProps) {
  const pendingCount = items.filter(i => i.status === "pending").length;

  return (
    <div className="w-[320px] flex-shrink-0 flex flex-col border-r border-border-default bg-bg-base">
      {/* Sub-header */}
      <div className="px-4 py-4 border-b border-border-divider">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <span className="bg-state-warning-dim text-state-warning text-[10px] font-bold px-2 py-0.5 rounded-full">
              {pendingCount} pending
            </span>
            <span className="text-xs text-text-muted">
              Actions held above policy — review and decide. Avg time to decide: 3.2m
            </span>
          </div>
          <button className="self-start text-xs font-medium text-text-secondary border border-border-default rounded-md px-2 py-1 hover:bg-bg-hover transition-colors flex items-center gap-1.5">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9"></path>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
            </svg>
            Edit policy
          </button>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 scroll-contain">
        {items.map((item) => {
          const isSelected = item.id === selectedId;
          const isDone = item.status !== "pending";
          return (
            <div
              key={item.id}
              onClick={() => onSelect(item.id)}
              className={cn(
                "p-3 border-l-4 rounded-r-lg cursor-pointer transition-all duration-150 will-change-transform",
                isSelected
                  ? "bg-bg-surface border-l-state-warning shadow-sm"
                  : "bg-transparent border-l-transparent hover:bg-bg-hover hover:-translate-y-px",
                isDone && "opacity-50 grayscale"
              )}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="text-sm font-semibold text-text-primary leading-tight">
                  {item.company}
                </span>
                <span className="text-[10px] font-medium text-state-warning">
                  {timeAgo(item.createdAt)}
                </span>
              </div>
              <p className="text-[11px] text-text-secondary mb-2">{item.type}</p>
              <div className="flex items-center gap-2">
                <span className="bg-state-warning-dim text-state-warning text-[10px] font-bold px-1.5 py-0.5 rounded-sm">
                  {item.amount}
                </span>
                <span className="text-[10px] text-text-muted">conf {item.confidence}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
