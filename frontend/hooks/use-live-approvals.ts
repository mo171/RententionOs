import { useEffect } from "react";
import { useApprovalsStore } from "@/store/approvals-store";

export function useLiveApprovals() {
  const store = useApprovalsStore();

  useEffect(() => {
    // PENDING: Live Data
    // When the backend is ready, connect a WebSocket here.
    // The store is append-only — just call store.addApproval() on each message.
    //
    // Example:
    // const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_APPROVALS_URL!);
    // ws.onmessage = (event) => {
    //   const approval = JSON.parse(event.data);
    //   store.addApproval(approval);
    // };
    // return () => ws.close();
    //
    // No UI changes needed — Zustand will reactively update all subscribed components.
  }, []);

  return store;
}
