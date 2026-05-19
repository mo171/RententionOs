"use client";

import { Approval, useApprovalsStore } from "@/store/approvals-store";
import { ApprovalAgentAction } from "@/components/approvals/approval-agent-action";
import { ApprovalMessagePreview } from "@/components/approvals/approval-message-preview";
import { ApprovalReasoning } from "@/components/approvals/approval-reasoning";
import { ApprovalMessageEdit } from "@/components/approvals/approval-message-edit";
import { X, ArrowRight, Check } from "lucide-react";
import { useState, useEffect } from "react";

interface ApprovalDetailViewProps {
  approval: Approval | undefined;
}

export function ApprovalDetailView({ approval }: ApprovalDetailViewProps) {
  const { setStatus, updateMessagePreview } = useApprovalsStore();
  const [isEditing, setIsEditing] = useState(false);
  const [draftPreview, setDraftPreview] = useState({ subject: "", body: "" });

  // Reset editing state when a new approval is selected
  useEffect(() => {
    setIsEditing(false);
    if (approval) {
      setDraftPreview({ ...approval.messagePreview });
    }
  }, [approval?.id]);

  if (!approval) {
    return (
      <div className="flex-1 flex items-center justify-center bg-bg-base text-text-muted text-sm font-medium">
        Select an approval from the queue to view details
      </div>
    );
  }

  const isDone = approval.status !== "pending";

  return (
    <div className="flex-1 flex flex-col bg-bg-base h-full overflow-hidden animate-in fade-in duration-200">
      {/* Detail Header */}
      <div className="px-8 py-6 border-b border-border-divider flex-shrink-0 flex items-start justify-between">
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
            Held for review
          </span>
          <h2 className="text-xl font-bold text-text-primary">{approval.type}</h2>
          <div className="flex items-center gap-1.5 text-xs text-text-secondary mt-1">
            <ArrowRight className="w-3.5 h-3.5 text-text-muted" />
            <span className="font-semibold text-text-primary">{approval.company}</span>
            <span>·</span>
            <span>{approval.summary}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {isDone ? (
            <div className="px-4 py-1.5 rounded-md bg-bg-hover text-text-secondary text-sm font-semibold flex items-center gap-1.5">
              <Check className="w-4 h-4" />
              {approval.status === "approved" ? "Approved" : "Dismissed"}
            </div>
          ) : isEditing ? (
            <>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setDraftPreview({ ...approval.messagePreview });
                }}
                className="px-3 py-1.5 rounded-md text-text-secondary text-xs font-semibold hover:bg-bg-hover hover:text-text-primary transition-colors duration-150"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  updateMessagePreview(approval.id, draftPreview);
                  setIsEditing(false);
                  // PENDING: API call → PATCH /api/approvals/:id
                }}
                className="shadow-primary px-4 py-1.5 rounded-md bg-primary text-white text-xs font-semibold hover:bg-primary/90 transition-all duration-150"
              >
                Save Changes
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setStatus(approval.id, "dismissed")}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-state-danger-dim text-state-danger text-xs font-semibold hover:bg-state-danger hover:text-white transition-colors duration-150"
              >
                <X className="w-3.5 h-3.5" />
                Reject
              </button>
              <button 
                onClick={() => setIsEditing(true)}
                className="px-3 py-1.5 rounded-md bg-bg-hover text-text-primary text-xs font-semibold hover:bg-bg-surface border border-transparent hover:border-border-default transition-all"
              >
                Modify
              </button>
              <button
                onClick={() => setStatus(approval.id, "approved")}
                className="shadow-primary flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-primary text-white text-xs font-semibold hover:bg-primary/90 transition-all duration-150"
              >
                <Check className="w-4 h-4" />
                Approve
              </button>
            </>
          )}
        </div>
      </div>

      {/* Detail Content — scrollable area */}
      <div className="flex-1 overflow-y-auto p-8 scroll-contain">
        <div className="grid grid-cols-[1fr_1.2fr] gap-12 max-w-5xl">
          {/* Left Column */}
          <div className="flex flex-col gap-8">
            <ApprovalAgentAction approval={approval} />
            {isEditing ? (
              <ApprovalMessageEdit 
                approval={approval} 
                draftPreview={draftPreview} 
                onChange={setDraftPreview} 
              />
            ) : (
              <ApprovalMessagePreview approval={approval} />
            )}
          </div>

          {/* Right Column */}
          <div>
            <ApprovalReasoning approval={approval} />
          </div>
        </div>
      </div>
    </div>
  );
}
