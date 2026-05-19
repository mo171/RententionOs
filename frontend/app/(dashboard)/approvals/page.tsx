"use client";

import { useState } from "react";
import { useLiveApprovals } from "@/hooks/use-live-approvals";
import { useApprovalsStore } from "@/store/approvals-store";
import { ApprovalListPanel } from "@/components/approvals/approval-list-panel";
import { ApprovalDetailView } from "@/components/approvals/approval-detail-view";

export default function ApprovalsPage() {
  useLiveApprovals(); // Boot WS stub
  const { items } = useApprovalsStore();
  
  // Default selection to the first pending item, or first item if none pending
  const firstPending = items.find((i) => i.status === "pending")?.id || items[0]?.id;
  const [selectedId, setSelectedId] = useState<string>(firstPending || "");

  const selectedApproval = items.find((i) => i.id === selectedId);

  return (
    <div className="flex h-full w-full overflow-hidden bg-bg-base shadow-sm border border-border-default rounded-xl">
      <ApprovalListPanel items={items} selectedId={selectedId} onSelect={setSelectedId} />
      <ApprovalDetailView approval={selectedApproval} />
    </div>
  );
}
