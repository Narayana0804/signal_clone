"use client";

import { useEffect, useRef, useCallback, useState } from "react";

export type ConnectionStatus = "CONNECTED" | "DISCONNECTED" | "RECONNECTING";

export interface WSEventEnvelope {
  type: string;
  event_id: string;
  timestamp: string;
  payload: any;
}

export function useWebSocket(
  onEvent?: (event: WSEventEnvelope) => void,
  onReconnect?: () => void
) {
  const [status, setStatus] = useState<ConnectionStatus>("DISCONNECTED");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef<number>(0);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const onEventRef = useRef(onEvent);
  const onReconnectRef = useRef(onReconnect);

  useEffect(() => {
    onEventRef.current = onEvent;
    onReconnectRef.current = onReconnect;
  }, [onEvent, onReconnect]);

  const connect = useCallback(() => {
    if (typeof window === "undefined") return;

    // Build clean WebSocket URL (HTTP-only cookie passed automatically by browser)
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = process.env.NEXT_PUBLIC_WS_URL || `${protocol}//${window.location.host}`;
    const wsUrl = `${host.replace(/\/$/, "")}/ws`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setStatus("CONNECTED");
        const wasReconnecting = reconnectAttempts.current > 0;
        reconnectAttempts.current = 0;
        if (wasReconnecting && onReconnectRef.current) {
          onReconnectRef.current();
        }
      };

      ws.onmessage = (event) => {
        try {
          const envelope: WSEventEnvelope = JSON.parse(event.data);
          if (onEventRef.current) {
            onEventRef.current(envelope);
          }
        } catch {
          // Ignore invalid JSON frame
        }
      };

      ws.onerror = () => {
        // Handle error silently, onclose handles reconnect
      };

      ws.onclose = (event) => {
        wsRef.current = null;
        // Don't reconnect if normal closure
        if (event.code === 1000) {
          setStatus("DISCONNECTED");
          return;
        }

        setStatus("RECONNECTING");
        reconnectAttempts.current += 1;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current - 1), 16000);

        if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
        reconnectTimer.current = setTimeout(() => {
          connect();
        }, delay);
      };

      wsRef.current = ws;
    } catch {
      setStatus("RECONNECTING");
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.close(1000);
      }
    };
  }, [connect]);

  const sendEvent = useCallback((type: string, payload: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, payload }));
    }
  }, []);

  return { status, sendEvent, isConnected: status === "CONNECTED" };
}
