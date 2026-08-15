"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  MessageSquare,
  Shield,
  Send,
  Check,
  CheckCheck,
  Loader2,
  AlertCircle,
  WifiOff,
  Circle,
  Users,
  Info,
} from "lucide-react";
import { Conversation } from "@/hooks/useConversations";
import { MessageItem, useMessages } from "@/hooks/useMessages";
import { useWebSocket, WSEventEnvelope } from "@/hooks/useWebSocket";
import { useAppStore } from "@/stores/appStore";
import { formatTimestamp, getInitials } from "@/lib/utils";
import { User } from "@/types";

/** Typing throttle: send at most once every 3s per spec */
const TYPING_THROTTLE_MS = 3000;
/** Auto-stop typing after 5s of inactivity */
const TYPING_STOP_DELAY_MS = 5000;
/** Remote typing indicator auto-clear after 6s with no refresh */
const TYPING_REMOTE_TIMEOUT_MS = 6000;

interface ChatPaneProps {
  conversation: Conversation | null;
  currentUser: User | null;
  onIncomingMessage?: (msg: unknown) => void;
  onOpenGroupDetails?: () => void;
}

export function ChatPane({ conversation, currentUser, onOpenGroupDetails }: ChatPaneProps) {
  const [inputText, setInputText] = useState("");
  const [typingUsers, setTypingUsers] = useState<Record<string, string>>({}); // user_id -> display_name
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingStopTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastTypingSentRef = useRef<number>(0);
  const typingRemoteTimers = useRef<Record<string, NodeJS.Timeout>>({});

  const presence = useAppStore((state) => state.presence);

  const {
    messages,
    loading,
    sending,
    error,
    sendMessage,
    addIncomingMessage,
    markAsDelivered,
    markAsRead,
    handleMessageDelivered,
    handleMessageRead,
    fetchMessages,
  } = useMessages(conversation ? conversation.id : null);

  // Clear remote typing timers on conversation change
  useEffect(() => {
    return () => {
      Object.values(typingRemoteTimers.current).forEach(clearTimeout);
      typingRemoteTimers.current = {};
    };
  }, [conversation?.id]);

  // WebSocket event handler for ChatPane
  const handleWSEvent = useCallback(
    (event: WSEventEnvelope) => {
      const { type, payload } = event;

      if (type === "message.created") {
        const msg = payload.message as MessageItem;
        if (msg.conversation_id === conversation?.id) {
          addIncomingMessage(msg);
          // Auto-mark as delivered if message from someone else
          if (msg.sender_id !== currentUser?.id) {
            markAsDelivered(msg.id);
            markAsRead(msg.id);
          }
          // Clear typing state for message sender (they just sent a message)
          if (msg.sender_id !== currentUser?.id) {
            setTypingUsers((prev) => {
              const next = { ...prev };
              delete next[msg.sender_id];
              return next;
            });
          }
        }
      } else if (type === "message.delivered") {
        const { message_id, recipient_id } = payload;
        handleMessageDelivered(message_id, recipient_id);
      } else if (type === "message.read") {
        const { conversation_id, user_id, last_read_message_id } = payload;
        if (conversation_id === conversation?.id) {
          handleMessageRead(conversation_id, user_id, last_read_message_id);
        }
      } else if (type === "typing.started") {
        const { conversation_id, user_id, display_name } = payload;
        if (conversation_id === conversation?.id && user_id !== currentUser?.id) {
          setTypingUsers((prev) => ({ ...prev, [user_id]: display_name || "Someone" }));

          // Auto-clear remote typing after timeout (safety net)
          if (typingRemoteTimers.current[user_id]) {
            clearTimeout(typingRemoteTimers.current[user_id]);
          }
          typingRemoteTimers.current[user_id] = setTimeout(() => {
            setTypingUsers((prev) => {
              const next = { ...prev };
              delete next[user_id];
              return next;
            });
            delete typingRemoteTimers.current[user_id];
          }, TYPING_REMOTE_TIMEOUT_MS);
        }
      } else if (type === "typing.stopped") {
        const { conversation_id, user_id } = payload;
        if (conversation_id === conversation?.id) {
          setTypingUsers((prev) => {
            const next = { ...prev };
            delete next[user_id];
            return next;
          });
          if (typingRemoteTimers.current[user_id]) {
            clearTimeout(typingRemoteTimers.current[user_id]);
            delete typingRemoteTimers.current[user_id];
          }
        }
      }
    },
    [
      conversation,
      currentUser,
      addIncomingMessage,
      markAsDelivered,
      markAsRead,
      handleMessageDelivered,
      handleMessageRead,
    ]
  );

  const { isConnected, sendEvent } = useWebSocket(handleWSEvent);

  // Auto-scroll to bottom on new messages
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Mark unread messages as read when opening conversation
  useEffect(() => {
    if (conversation && messages.length > 0 && currentUser) {
      const unreadIncoming = messages.filter(
        (m) =>
          m.sender_id !== currentUser.id &&
          !m.receipts?.some((r) => r.user_id === currentUser.id && r.status === "READ")
      );
      if (unreadIncoming.length > 0) {
        const lastMsg = unreadIncoming[unreadIncoming.length - 1];
        markAsRead(lastMsg.id);
      }
    }
  }, [conversation, messages, currentUser, markAsRead]);

  // Typing event sender logic
  const sendTypingStarted = useCallback(() => {
    if (!conversation || !isConnected) return;
    const now = Date.now();
    if (now - lastTypingSentRef.current >= TYPING_THROTTLE_MS) {
      lastTypingSentRef.current = now;
      sendEvent("typing.started", { conversation_id: conversation.id });
    }
  }, [conversation, isConnected, sendEvent]);

  const sendTypingStopped = useCallback(() => {
    if (!conversation || !isConnected) return;
    sendEvent("typing.stopped", { conversation_id: conversation.id });
    lastTypingSentRef.current = 0;
  }, [conversation, isConnected, sendEvent]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputText(e.target.value);
    if (!e.target.value.trim()) {
      if (typingStopTimerRef.current) clearTimeout(typingStopTimerRef.current);
      sendTypingStopped();
      return;
    }

    sendTypingStarted();

    if (typingStopTimerRef.current) clearTimeout(typingStopTimerRef.current);
    typingStopTimerRef.current = setTimeout(() => {
      sendTypingStopped();
    }, TYPING_STOP_DELAY_MS);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !currentUser || !conversation) return;
    const text = inputText;
    setInputText("");

    if (typingStopTimerRef.current) clearTimeout(typingStopTimerRef.current);
    sendTypingStopped();

    try {
      await sendMessage(text, currentUser);
    } catch {
      // Error state handled inside hook
    }
  };

  if (!conversation) {
    return (
      <main className="flex-1 h-full bg-[var(--color-bg-chat)] flex flex-col items-center justify-center text-[var(--color-text-secondary)] text-xs">
        <MessageSquare className="w-12 h-12 text-[var(--color-text-tertiary)] mb-3 stroke-1" />
        <p className="font-bold text-sm text-[var(--color-text-primary)] mb-1">Select a Conversation</p>
        <p className="text-xs">Choose a chat from the left sidebar to start messaging.</p>
      </main>
    );
  }

  const isGroup = conversation.type === "GROUP";
  const otherUser = isGroup ? null : conversation.other_user;
  const displayName = isGroup
    ? conversation.name || "Group Conversation"
    : otherUser?.display_name || "Direct Message";
  const subText = isGroup
    ? `${conversation.participants.length} members`
    : otherUser?.phone_number || "";

  const otherPresence = otherUser ? presence[otherUser.id] : null;
  const isOnline = otherPresence?.status === "online";
  const activeTypingNames = Object.values(typingUsers);

  return (
    <main className="flex-1 h-full bg-[var(--color-bg-chat)] flex flex-col min-w-0">
      {/* Reconnection / Offline Banner */}
      {!isConnected && (
        <div className="bg-amber-500 text-white text-[11px] font-bold px-3 py-1 flex items-center justify-center gap-1.5 shadow-2xs">
          <WifiOff className="w-3.5 h-3.5" />
          <span>Connection lost. Reconnecting to Signal realtime server...</span>
        </div>
      )}

      {/* Chat Pane Top Header */}
      <div className="px-4 py-2.5 border-b border-[var(--color-border-primary)] bg-[var(--color-bg-sidebar)] flex items-center justify-between shadow-2xs">
        <div
          onClick={isGroup ? onOpenGroupDetails : undefined}
          className={`flex items-center gap-3 ${isGroup ? "cursor-pointer group" : ""}`}
        >
          {/* Avatar */}
          <div className="relative">
            <div
              className={`w-9 h-9 rounded-full text-white flex items-center justify-center font-bold text-xs shadow-xs ${
                isGroup ? "bg-indigo-600" : "bg-[var(--color-signal-blue)]"
              }`}
            >
              {isGroup ? <Users className="w-5 h-5" /> : getInitials(displayName)}
            </div>
            {otherUser && (
              <Circle
                className={`w-3 h-3 absolute -bottom-0.5 -right-0.5 rounded-full border-2 border-[var(--color-bg-sidebar)] transition-colors duration-300 ${
                  isOnline ? "fill-emerald-500 text-emerald-500" : "fill-gray-300 text-gray-300"
                }`}
              />
            )}
          </div>
          <div>
            <h2 className={`font-bold text-xs text-[var(--color-text-primary)] ${isGroup ? "group-hover:text-[var(--color-signal-blue)] transition-colors" : ""}`}>
              {displayName}
            </h2>
            <p className="text-[10px] text-[var(--color-text-secondary)]">
              {isGroup ? (
                <span className="font-medium text-indigo-600 flex items-center gap-1">
                  <span>{subText}</span>
                  <Info className="w-3 h-3 text-indigo-400" />
                </span>
              ) : otherUser ? (
                isOnline ? (
                  <span className="text-emerald-600 font-medium">Online</span>
                ) : otherPresence?.last_seen_at ? (
                  <span>Last seen {formatTimestamp(otherPresence.last_seen_at)}</span>
                ) : (
                  <span className="font-mono">{subText}</span>
                )
              ) : (
                subText
              )}
            </p>
          </div>
        </div>

        {/* Security Disclaimer */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-[var(--radius-sm)] bg-amber-50 text-amber-800 border border-amber-200 text-[11px] font-medium">
          <Shield className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
          <span>Signal Clone Demo — Transport Security Only (No E2EE)</span>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-2 mx-4 mt-2 rounded-[var(--radius-md)] bg-red-50 text-[var(--color-error)] text-xs flex items-center gap-2 border border-red-200">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Messages List Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-0.5">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-full text-xs text-[var(--color-text-secondary)] gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-[var(--color-signal-blue)]" />
            <span>Loading messages...</span>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-xs text-[var(--color-text-secondary)]">
            <MessageSquare className="w-10 h-10 text-[var(--color-text-tertiary)] mb-2 stroke-1" />
            <p className="font-semibold text-[var(--color-text-primary)] mb-1">No messages yet</p>
            <p className="text-[11px]">Send a message below to start your conversation with {displayName}.</p>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isMe = currentUser ? msg.sender_id === currentUser.id : false;
            const isRead = msg.receipts?.some((r) => r.status === "READ");
            const isDelivered = msg.receipts?.some((r) => r.status === "DELIVERED" || r.status === "READ");

            // Visual message grouping: check if previous message was sent by same user within 5 minutes
            const prevMsg = index > 0 ? messages[index - 1] : null;
            const isSameSender = prevMsg ? prevMsg.sender_id === msg.sender_id : false;
            const isCloseInTime = prevMsg
              ? Math.abs(new Date(msg.created_at).getTime() - new Date(prevMsg.created_at).getTime()) < 5 * 60 * 1000
              : false;
            const isGrouped = isSameSender && isCloseInTime;

            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isMe ? "items-end" : "items-start"} ${isGrouped ? "mt-0.5" : "mt-3"}`}
              >
                <div
                  className={`max-w-[70%] px-3.5 py-2.5 rounded-[var(--radius-md)] shadow-2xs text-xs ${
                    isMe
                      ? "bg-[var(--color-signal-blue)] text-white rounded-br-xs"
                      : "bg-white text-[var(--color-text-primary)] border border-[var(--color-border-light)] rounded-bl-xs"
                  } ${msg.isOptimistic ? "opacity-70" : ""}`}
                >
                  {!isMe && isGroup && !isGrouped && (
                    <span className="block font-bold text-[11px] text-[var(--color-signal-blue)] mb-0.5">
                      {msg.sender.display_name}
                    </span>
                  )}
                  <p className="whitespace-pre-wrap break-words leading-relaxed">{msg.content}</p>

                  {/* Timestamp & 3-State Receipt Indicator */}
                  <div
                    className={`flex items-center justify-end gap-1 mt-1 text-[10px] ${
                      isMe ? "text-blue-100" : "text-[var(--color-text-tertiary)]"
                    }`}
                  >
                    <span>{formatTimestamp(msg.created_at)}</span>
                    {isMe && (
                      <span
                        title={isRead ? "Read" : isDelivered ? "Delivered" : msg.isOptimistic ? "Sending..." : "Sent"}
                        className="inline-flex transition-opacity"
                      >
                        {msg.isOptimistic ? (
                          <Loader2 className="w-3 h-3 animate-spin text-blue-200/50" />
                        ) : isRead ? (
                          <CheckCheck className="w-3.5 h-3.5 text-blue-200" />
                        ) : isDelivered ? (
                          <CheckCheck className="w-3.5 h-3.5 text-blue-200/70" />
                        ) : (
                          <Check className="w-3.5 h-3.5 text-blue-200/50" />
                        )}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Typing Indicator Bar */}
      {activeTypingNames.length > 0 && (
        <div className="px-4 py-1.5 text-[11px] italic text-[var(--color-signal-blue)] bg-[var(--color-bg-sidebar)] border-t border-[var(--color-border-light)] flex items-center gap-2">
          <div className="flex gap-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-signal-blue)] animate-bounce [animation-delay:0ms]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-signal-blue)] animate-bounce [animation-delay:150ms]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-signal-blue)] animate-bounce [animation-delay:300ms]" />
          </div>
          <span>{activeTypingNames.join(", ")} {activeTypingNames.length === 1 ? "is" : "are"} typing...</span>
        </div>
      )}

      {/* Message Composer Bar */}
      <form onSubmit={handleSend} className="p-3 border-t border-[var(--color-border-primary)] bg-[var(--color-bg-sidebar)]">
        <div className="flex items-center gap-2 bg-[var(--color-bg-input)] rounded-[var(--radius-md)] p-1.5 border border-[var(--color-border-primary)] focus-within:border-[var(--color-signal-blue)] focus-within:bg-white transition-all">
          <input
            type="text"
            value={inputText}
            onChange={handleInputChange}
            placeholder={`Message ${displayName}...`}
            className="flex-1 bg-transparent px-2 text-xs text-[var(--color-text-primary)] outline-none"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || sending}
            className="p-1.5 bg-[var(--color-signal-blue)] hover:bg-[var(--color-signal-blue-dark)] text-white rounded-[var(--radius-sm)] transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {sending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
          </button>
        </div>
      </form>
    </main>
  );
}
