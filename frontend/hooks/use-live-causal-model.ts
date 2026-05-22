import { useEffect } from "react";
import { useCausalModelStore } from "@/store/causal-model-store";
import { apiRequest } from "@/lib/api";

interface CausalSnapshotResponse {
  snapshot: Partial<ReturnType<typeof useCausalModelStore.getState>>;
  model_metadata: Record<string, unknown>;
}

export function useLiveCausalModel() {
  const store = useCausalModelStore();
  const setSnapshot = useCausalModelStore((s) => s.setSnapshot);

  useEffect(() => {
    let cancelled = false;

    apiRequest<CausalSnapshotResponse>("/api/causal/snapshot")
      .then((data) => {
        if (!cancelled) {
          setSnapshot(data.snapshot);
        }
      })
      .catch((error) => {
        console.warn("[causal-model] Falling back to mock snapshot:", error);
      });

    // PENDING: Live Data
    // When the backend is ready, connect a WebSocket here.
    // On each message, call store.setSnapshot(parsedPayload).
    //
    // Example:
    // const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_CAUSAL_MODEL_URL!);
    // ws.onmessage = (event) => {
    //   const data = JSON.parse(event.data);
    //   store.setSnapshot(data);
    // };
    // return () => ws.close();
    return () => {
      cancelled = true;
    };
  }, [setSnapshot]);

  return store;
}
