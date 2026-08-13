"use client";

import { useEffect, useRef, useCallback } from "react";

export interface WSEventEnvelope {
  type: string;
  event_id: string;
  timestamp: string;
  payload: any;
}

export function useWebSocket(onEvent?: (event: WSEventEnvelope) => void) {
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (typeof window === "undefined") return;

    // Determine WebSocket URL
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = process.env.NEXT_PUBLIC_WS_URL || `${protocol}//${window.location.host}`;
    const wsUrl = `${host.replace(/\/$/, "")}/ws`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        // Connection established
      };

      ws.onmessage = (event) => {
        try {
          const envelope: WSEventEnvelope = JSON.parse(event.data);
          if (onEvent) {
            onEvent(envelope);
          }
        } catch {
          // Ignore invalid JSON frame
        }
      };

      ws.onerror = () => {
        // Handle error silently
      };

      ws.onclose = () => {
        // Clean up reference
        wsRef.current = null;
      };

      wsRef.current = ws;
    } catch {
      // Handle connection attempt error
    }
  }, [onEvent]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendEvent = (type: string, payload: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, payload }));
    }
  };

  return { sendEvent };
}
