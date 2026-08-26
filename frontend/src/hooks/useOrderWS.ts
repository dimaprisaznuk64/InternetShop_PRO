import { useEffect, useRef, useState, useCallback } from "react";
import { getAccessToken } from "../api/client";

type WSStatus = "connecting" | "connected" | "disconnected" | "error";

interface OrderStatusMessage {
  type: "status_update" | "pong";
  status?: string;
  order_id?: string;
}

export function useOrderWS(orderId: string | undefined) {
  const [status, setStatus] = useState<string>("");
  const [wsState, setWsState] = useState<WSStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const connect = useCallback(() => {
    if (!orderId) return;
    let token: string | null = null;
    try {
      token = getAccessToken();
    } catch {
      token = null;
    }
    if (!token) return;

    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const raw = import.meta.env.VITE_API_URL || "";
    const host = raw
      ? raw.replace(/^https?:\/\//, `${proto}//`)
      : `${proto}//${window.location.host}`;
    const url = `${host}/ws/orders/${orderId}?token=${encodeURIComponent(token)}`;

    setWsState("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsState("connected");
      // Keep-alive ping every 30s
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send("ping");
      }, 30000);
      ws.addEventListener("close", () => clearInterval(pingInterval), { once: true });
    };

    ws.onmessage = (event) => {
      try {
        const data: OrderStatusMessage = JSON.parse(event.data);
        if (data.type === "status_update" && data.status) {
          setStatus(data.status);
        }
      } catch {}
    };

    ws.onclose = (event) => {
      setWsState("disconnected");
      wsRef.current = null;
      // Auto-reconnect after 3s if not intentional close
      if (event.code !== 4001 && event.code !== 4003 && event.code !== 4004) {
        reconnectTimer.current = setTimeout(connect, 3000);
      }
    };

    ws.onerror = () => {
      setWsState("error");
    };
  }, [orderId]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { status, setStatus, wsState };
}
