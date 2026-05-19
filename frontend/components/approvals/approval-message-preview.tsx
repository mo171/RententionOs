"use client";

import { Approval } from "@/store/approvals-store";

export function ApprovalMessagePreview({ approval }: { approval: Approval }) {
  const { messagePreview } = approval;

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
        Message Preview
      </h3>
      <div className="bg-[#F4F2ED] rounded-xl p-4 text-xs">
        <div className="flex flex-col gap-1 mb-4">
          <span className="text-[10px] text-text-muted font-medium uppercase tracking-wider">Subject</span>
          <span className="font-semibold text-text-primary">{messagePreview.subject}</span>
        </div>
        <div className="flex flex-col gap-1 relative">
          <span className="text-[10px] text-text-muted font-medium uppercase tracking-wider">Body</span>
          <p className="text-text-secondary leading-relaxed max-h-[80px] overflow-hidden relative">
            {messagePreview.body}
            {/* Fade out for truncation */}
            <span className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-[#F4F2EC] to-transparent pointer-events-none" />
          </p>
        </div>
      </div>
    </div>
  );
}
