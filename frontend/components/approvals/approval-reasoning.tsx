"use client";

import { Approval } from "@/store/approvals-store";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export function ApprovalReasoning({ approval }: { approval: Approval }) {
  const { reasoning, alternatives } = approval;

  return (
    <div className="flex flex-col gap-6">
      {/* Why this action */}
      <div className="flex flex-col gap-3">
        <h3 className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
          Why this action
        </h3>
        <div className="border border-state-safe/20 rounded-xl p-5 bg-white shadow-sm">
          <p className="text-sm text-text-primary leading-relaxed mb-4">
            {/* Find the text in quotes and highlight it green */}
            {reasoning.text.split(/(".*?")/).map((part, i) => {
              if (part.startsWith('"') && part.endsWith('"')) {
                return <span key={i} className="text-state-safe font-medium">{part}</span>;
              }
              return part;
            })}
          </p>
          <ul className="flex flex-col gap-2.5">
            {reasoning.bullets.map((bullet, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                <Check className="w-4 h-4 text-state-safe flex-shrink-0 mt-0.5" />
                <span className="leading-relaxed">{bullet}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Alternatives */}
      <div className="flex flex-col gap-3">
        <h3 className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
          Alternatives Considered
        </h3>
        <div className="flex flex-col gap-1">
          {alternatives.map((alt, i) => (
            <div
              key={i}
              className={cn(
                "flex items-center justify-between px-4 py-3 rounded-lg text-xs font-medium border",
                alt.selected
                  ? "bg-white border-state-safe/30 text-text-primary shadow-sm"
                  : "bg-[#F4F2ED] border-transparent text-text-secondary"
              )}
            >
              <div className="flex items-center gap-2">
                <div className="w-4 flex items-center justify-center">
                  {alt.selected ? (
                    <Check className="w-3 h-3 text-state-safe" />
                  ) : (
                    <span className="text-text-faint">-</span>
                  )}
                </div>
                <span>{alt.label}</span>
              </div>
              <div className="flex items-center gap-4 text-right font-mono">
                <span className="w-12">{alt.amount}</span>
                <span className={cn("w-8", alt.selected ? "text-state-safe" : "text-text-secondary")}>
                  {alt.roi}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
