import { useEffect } from "react";
import { useCausalModelStore } from "@/store/causal-model-store";

export function useLiveCausalModel() {
  const store = useCausalModelStore();

  useEffect(() => {
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
  }, []);

  return store;
}
