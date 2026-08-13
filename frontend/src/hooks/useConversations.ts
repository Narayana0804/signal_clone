"use client";

import { useCallback, useEffect, useState } from "react";
import { apiRequest, ApiError } from "@/lib/api";
import { useAppStore } from "@/stores/appStore";
import { User } from "@/types";

export interface Participant {
  id: string;
  user_id: string;
  role: string;
  joined_at: string;
  user: User;
}

export interface LastMessagePreview {
  id: string;
  content: string;
  sender_id: string;
  sender_name: string;
  created_at: string;
  message_type: string;
}

export interface Conversation {
  id: string;
  type: "DIRECT" | "GROUP";
  name?: string | null;
  avatar_url?: string | null;
  created_at: string;
  updated_at: string;
  participants: Participant[];
  other_user?: User | null;
  last_message?: LastMessagePreview | null;
  unread_count: number;
}

export function useConversations() {
  const selectedConversationId = useAppStore((state) => state.selectedConversationId);
  const setSelectedConversationId = useAppStore((state) => state.setSelectedConversationId);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiRequest<{ conversations: Conversation[] }>("/conversations");
      setConversations(data.conversations || []);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load conversations");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  useEffect(() => {
    if (!selectedConversationId) {
      setSelectedConversation(null);
      return;
    }
    const found = conversations.find((c) => c.id === selectedConversationId);
    if (found) {
      setSelectedConversation(found);
    } else {
      // Fetch directly if not in list
      apiRequest<Conversation>(`/conversations/${selectedConversationId}`)
        .then((conv) => setSelectedConversation(conv))
        .catch(() => setSelectedConversation(null));
    }
  }, [selectedConversationId, conversations]);

  const createDirectConversation = async (targetUserId: string) => {
    try {
      setError(null);
      const conv = await apiRequest<Conversation>("/conversations", {
        method: "POST",
        body: JSON.stringify({
          type: "DIRECT",
          participant_ids: [targetUserId],
        }),
      });

      // Update list (add or replace existing)
      setConversations((prev) => {
        const exists = prev.some((c) => c.id === conv.id);
        if (exists) {
          return prev.map((c) => (c.id === conv.id ? conv : c));
        }
        return [conv, ...prev];
      });

      setSelectedConversationId(conv.id);
      return conv;
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to start conversation");
      }
      throw err;
    }
  };

  const selectConversation = (id: string | null) => {
    setSelectedConversationId(id);
  };

  return {
    conversations,
    selectedConversation,
    selectedConversationId,
    loading,
    error,
    fetchConversations,
    createDirectConversation,
    selectConversation,
  };
}
