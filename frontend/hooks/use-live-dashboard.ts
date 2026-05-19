import { useEffect } from "react";
import { useDashboardStore } from "@/store/dashboard-store";

export function useLiveDashboard() {
  const store = useDashboardStore();

  useEffect(() => {
    // In the future, this is where we will establish a WebSocket connection
    // and listen for real-time events to update the store using store.updateMetrics.
    
    // Example placeholder for future WS implementation:
    // const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL!);
    // ws.onmessage = (event) => {
    //   const data = JSON.parse(event.data);
    //   store.updateMetrics(data);
    // };
    // return () => ws.close();
  }, []);

  return store;
}
