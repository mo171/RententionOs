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
    
    const cleanup = createReconnectingWebSocket(wsUrl, (message) => {
      if (message && message.type && message.data) {
        const { type, data } = message;
        if (data && data.id) {
          if (type === "approval_new") {
            store.addApproval(data);
          } else {
            store.updateApproval(data);
          }
        }
      } else if (message && message.id) {
        // Fallback for unwrapped messages
        store.addApproval(message);
      }
    });

    return cleanup;
  }, []);

  return store;
}
