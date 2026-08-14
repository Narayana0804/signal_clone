"use client";

import { useCallback, useEffect, useState } from "react";
import { apiRequest, ApiError } from "@/lib/api";

export interface Receipt {
  user_id: string;
  status: "SENT" | "DELIVERED" | "READ";
  delivered_at?: string | null;
  read_at?: string | null;
}

export interface MessageSender {
  id: string;
  display_name: string;
  avatar_url?: string | null;
}

export interface MessageItem {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender: MessageSender;
  content: string;
  message_type: string;
  client_id?: string | null;
  reply_to_id?: string | null;
  created_at: string;
  updated_at?: string | null;
  deleted_at?: string | null;
  receipts: Receipt[];
  isOptimistic?: boolean;
}

export function useMessages(conversationId: string | null) {
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  const fetchMessages = useCallback(async (convId: string, before?: string) => {
    try {
      setLoading(true);
      setError(null);
      const url = `/conversations/${convId}/messages${before ? `?before=${before}` : ""}`;
      const data = await apiRequest<{ messages: MessageItem[]; has_more: boolean }>(url);
      
      setMessages((prev) => {
        if (!before) {
          return data.messages || [];
        }
        // Merge and deduplicate
        const map = new Map<string, MessageItem>();
        (data.messages || []).forEach((m) => map.set(m.id, m));
        prev.forEach((m) => map.set(m.id, m));
        return Array.from(map.values()).sort(
          (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
      });
      setHasMore(data.has_more || false);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load messages");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (conversationId) {
      fetchMessages(conversationId);
    } else {
      setMessages([]);
    }
  }, [conversationId, fetchMessages]);

  const sendMessage = async (content: string, currentUser: { id: string; display_name: string }) => {
    if (!conversationId || !content.trim()) return;

    const clientId = `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const cleanContent = content.trim();

    // Optimistic message object
    const optimisticMsg: MessageItem = {
      id: clientId,
      conversation_id: conversationId,
      sender_id: currentUser.id,
      sender: {
        id: currentUser.id,
        display_name: currentUser.display_name,
        avatar_url: null,
      },
      content: cleanContent,
      message_type: "TEXT",
      client_id: clientId,
      created_at: new Date().toISOString(),
      receipts: [],
      isOptimistic: true,
    };

    setMessages((prev) => [...prev, optimisticMsg]);

    try {
      setSending(true);
      setError(null);
      const serverMsg = await apiRequest<MessageItem>(
        `/conversations/${conversationId}/messages`,
        {
          method: "POST",
          body: JSON.stringify({
            content: cleanContent,
            message_type: "TEXT",
            client_id: clientId,
          }),
        }
      );

      // Reconcile optimistic message with server message
      setMessages((prev) =>
        prev.map((m) => (m.client_id === clientId || m.id === clientId ? serverMsg : m))
      );
      return serverMsg;
    } catch (err) {
      // Remove optimistic message on failure
      setMessages((prev) => prev.filter((m) => m.client_id !== clientId && m.id !== clientId));
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to send message");
      }
      throw err;
    } finally {
      setSending(false);
    }
  };

  const addIncomingMessage = useCallback((incomingMsg: MessageItem) => {
    setMessages((prev) => {
      // Prevent duplicates
      if (prev.some((m) => m.id === incomingMsg.id || (incomingMsg.client_id && m.client_id === incomingMsg.client_id))) {
        return prev;
      }
      return [...prev, incomingMsg];
    });
  }, []);

  const markAsDelivered = async (messageId: string) => {
    if (!messageId) return;
    try {
      await apiRequest(`/messages/${messageId}/delivered`, { method: "POST" });
    } catch {
      // Ignore delivery ack error
    }
  };

  const markAsRead = async (messageId: string) => {
    if (!messageId) return;
    try {
      await apiRequest(`/messages/${messageId}/read`, { method: "POST" });
    } catch {
      // Ignore read receipt error silently
    }
  };

  const handleMessageDelivered = useCallback((msgId: string, recipientId: string) => {
    setMessages((prev) =>
      prev.map((m) => {
        if (m.id !== msgId) return m;
        const updatedReceipts = m.receipts.map((r) =>
          r.user_id === recipientId ? { ...r, status: "DELIVERED" as const, delivered_at: new Date().toISOString() } : r
        );
        if (!updatedReceipts.some((r) => r.user_id === recipientId)) {
          updatedReceipts.push({
            user_id: recipientId,
            status: "DELIVERED",
            delivered_at: new Date().toISOString(),
          });
        }
        return { ...m, receipts: updatedReceipts };
      })
    );
  }, []);

  const handleMessageRead = useCallback((convId: string, readerUserId: string, lastReadMessageId: string) => {
    setMessages((prev) => {
      const targetMsgIndex = prev.findIndex((m) => m.id === lastReadMessageId);
      if (targetMsgIndex === -1) return prev;

      const targetTimestamp = new Date(prev[targetMsgIndex].created_at).getTime();

      return prev.map((m) => {
        const msgTimestamp = new Date(m.created_at).getTime();
        if (msgTimestamp <= targetTimestamp) {
          const updatedReceipts = m.receipts.map((r) =>
            r.user_id === readerUserId ? { ...r, status: "READ" as const, read_at: new Date().toISOString() } : r
          );
          if (!updatedReceipts.some((r) => r.user_id === readerUserId)) {
            updatedReceipts.push({
              user_id: readerUserId,
              status: "READ",
              read_at: new Date().toISOString(),
            });
          }
          return { ...m, receipts: updatedReceipts };
        }
        return m;
      });
    });
  }, []);

  return {
    messages,
    loading,
    sending,
    error,
    hasMore,
    sendMessage,
    addIncomingMessage,
    markAsDelivered,
    markAsRead,
    handleMessageDelivered,
    handleMessageRead,
    fetchMessages,
  };
}
