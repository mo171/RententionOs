export function createReconnectingWebSocket(url: string, onMessage: (data: any) => void): () => void {
  let ws: WebSocket | null = null;
  let isClosed = false;
  let reconnectTimeout: NodeJS.Timeout;

  function connect() {
    ws = new WebSocket(url);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error("Failed to parse websocket message", e);
      }
    };

    ws.onclose = () => {
      if (!isClosed) {
        // Reconnect after 3 seconds
        reconnectTimeout = setTimeout(connect, 3000);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error", err);
      ws?.close();
    };
  }

  connect();

  return () => {
    isClosed = true;
    clearTimeout(reconnectTimeout);
    if (ws) {
      ws.close();
    }
  };
}
