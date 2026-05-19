"use client";

import { Approval } from "@/store/approvals-store";
import { cn } from "@/lib/utils";

export function ApprovalAgentAction({ approval }: { approval: Approval }) {
  const { agentAction } = approval;

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
        What the agent will do
      </h3>
      <div className="bg-[#F4F2ED] rounded-xl p-4 font-mono text-[11px] leading-relaxed">
        <div className="grid grid-cols-[100px_1fr] gap-x-4 gap-y-2">
          <span className="text-text-muted">action</span>
          <span className="text-accent-ai font-medium">{agentAction.action}</span>

          <span className="text-text-muted">amount</span>
          <span className="text-text-primary">{agentAction.amount}</span>

          <span className="text-text-muted">channel</span>
          <span className="text-text-primary">{agentAction.channel}</span>

          <span className="text-text-muted">template</span>
          <span className="text-text-primary">{agentAction.template}</span>

          <span className="text-text-muted">send_at</span>
          <span className="text-text-primary">{agentAction.send_at}</span>

          <span className="text-text-muted mt-2">expected_lift</span>
          <span className="text-state-safe font-semibold mt-2">{agentAction.expected_lift}</span>

          <span className="text-text-muted">expected_roi</span>
          <span className="text-state-safe font-semibold">{agentAction.expected_roi}</span>
        </div>
      </div>
    </div>
  );
}
