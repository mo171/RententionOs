"use client";

import { Approval } from "@/store/approvals-store";
import { useState, useEffect } from "react";

interface ApprovalMessageEditProps {
  approval: Approval;
  draftPreview: { subject: string; body: string };
  onChange: (preview: { subject: string; body: string }) => void;
}

export function ApprovalMessageEdit({ approval, draftPreview, onChange }: ApprovalMessageEditProps) {
  return (
    <div className="flex flex-col gap-2 animate-in fade-in duration-200">
      <h3 className="text-[10px] font-bold text-text-muted uppercase tracking-widest flex items-center justify-between">
        <span>Message Preview (Edit Mode)</span>
        <span className="text-primary normal-case">Drafting...</span>
      </h3>
      <div className="bg-[#F4F2ED] rounded-xl p-4 text-xs border border-primary/20 shadow-[0_0_0_1px_rgba(38,179,106,0.1)] focus-within:shadow-[0_0_0_2px_rgba(38,179,106,0.2)] transition-shadow">
        <div className="flex flex-col gap-1.5 mb-4">
          <label className="text-[10px] text-text-muted font-medium uppercase tracking-wider">Subject</label>
          <input
            type="text"
            value={draftPreview.subject}
            onChange={(e) => onChange({ ...draftPreview, subject: e.target.value })}
            className="w-full bg-white border border-border-default rounded-md px-3 py-2 text-text-primary font-semibold focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
            placeholder="Email subject..."
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] text-text-muted font-medium uppercase tracking-wider">Body</label>
          <textarea
            value={draftPreview.body}
            onChange={(e) => onChange({ ...draftPreview, body: e.target.value })}
            className="w-full bg-white border border-border-default rounded-md px-3 py-2 text-text-secondary leading-relaxed min-h-[120px] resize-y focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
            placeholder="Email body..."
          />
        </div>
      </div>
    </div>
  );
}
