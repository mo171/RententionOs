import { useEffect } from "react";
import { useApprovalsStore } from "@/store/approvals-store";
import { fetchApprovals } from "@/lib/api";
import { createReconnectingWebSocket } from "@/lib/websocket";

export function useLiveApprovals() {
  const store = useApprovalsStore();

  useEffect(() => {
    // 1. Hydrate from API
    fetchApprovals()
      .then((approvals) => {
        if (approvals && approvals.length > 0) {
          store.hydrateFromAPI(approvals);
        }
      })
      .catch((err) => console.error("Failed to fetch initial approvals:", err));

    // 2. Connect to WebSocket for real-time updates
    const wsUrl = process.env.NEXT_PUBLIC_WS_APPROVALS_URL || "ws://localhost:8000/ws/approvals";
    
    const cleanup = createReconnectingWebSocket(wsUrl, (data) => {
      if (data && data.id) {
        // Simple heuristic: if we already have it, we might want to update it
        // For now, we rely on the store having optimistic updates for local changes,
        // and we just prepend new ones. A more robust implementation would check if it exists
        // and update or add accordingly.
        store.addApproval(data);
      }
    });

    return cleanup;
  }, []);

  return store;
}
