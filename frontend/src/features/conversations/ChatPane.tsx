"use client";

import React, { useEffect, useRef, useState } from "react";
import { MessageSquare, Shield, Send, Check, CheckCheck, Loader2, AlertCircle } from "lucide-react";
import { Conversation } from "@/hooks/useConversations";
import { useMessages } from "@/hooks/useMessages";
import { formatTimestamp, getInitials } from "@/lib/utils";
import { User } from "@/types";

interface ChatPaneProps {
  conversation: Conversation | null;
  currentUser: User | null;
  onIncomingMessage?: (msg: any) => void;
}

export function ChatPane({ conversation, currentUser }: ChatPaneProps) {
  const [inputText, setInputText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    loading,
    sending,
    error,
    sendMessage,
    markAsRead,
  } = useMessages(conversation ? conversation.id : null);

  // Auto-scroll to bottom on new messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Mark latest message as read when viewing conversation
  useEffect(() => {
    if (messages.length > 0 && currentUser) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.sender_id !== currentUser.id) {
        markAsRead(lastMsg.id);
      }
    }
  }, [messages, currentUser, markAsRead]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !currentUser || !conversation) return;

    const text = inputText;
    setInputText("");
    try {
      await sendMessage(text, currentUser);
    } catch {
      setInputText(text); // Restore text on failure
    }
  };

  if (!conversation) {
    return (
      <main className="flex-1 h-full bg-[var(--color-bg-chat)] flex flex-col items-center justify-center p-8 text-center">
        <div className="w-16 h-16 bg-blue-50 text-[var(--color-signal-blue)] rounded-full flex items-center justify-center mb-4 border border-blue-100 shadow-xs">
          <MessageSquare className="w-8 h-8" />
        </div>
        <h2 className="text-lg font-bold text-[var(--color-text-primary)] mb-1">Signal Desktop</h2>
        <p className="text-xs text-[var(--color-text-secondary)] max-w-sm">
          Select a conversation from the sidebar or start a new direct chat to begin messaging.
        </p>
      </main>
    );
  }

  const displayName =
    conversation.type === "DIRECT" && conversation.other_user
      ? conversation.other_user.display_name
      : conversation.name || "Conversation";

  const subText =
    conversation.type === "DIRECT" && conversation.other_user
      ? conversation.other_user.phone_number
      : `${conversation.participants.length} participants`;

  return (
    <main className="flex-1 h-full bg-[var(--color-bg-chat)] flex flex-col overflow-hidden">
      {/* Chat Top Header */}
      <div className="p-3 border-b border-[var(--color-border-primary)] bg-[var(--color-bg-sidebar)] flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-[var(--color-signal-blue)] text-white flex items-center justify-center font-bold text-xs shadow-xs">
            {getInitials(displayName)}
          </div>
          <div>
            <h2 className="font-bold text-xs text-[var(--color-text-primary)]">{displayName}</h2>
            <p className="text-[10px] text-[var(--color-text-secondary)] font-mono">{subText}</p>
          </div>
        </div>

        {/* Security Disclaimer (Explicit & Honest per prompt rule #2) */}
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
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
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
          messages.map((msg) => {
            const isMe = currentUser ? msg.sender_id === currentUser.id : false;
            const isRead = msg.receipts?.some((r) => r.status === "READ");

            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[70%] px-3.5 py-2.5 rounded-[var(--radius-md)] shadow-2xs text-xs ${
                    isMe
                      ? "bg-[var(--color-signal-blue)] text-white rounded-br-xs"
                      : "bg-white text-[var(--color-text-primary)] border border-[var(--color-border-light)] rounded-bl-xs"
                  }`}
                >
                  {!isMe && conversation.type === "GROUP" && (
                    <span className="block font-bold text-[11px] text-[var(--color-signal-blue)] mb-0.5">
                      {msg.sender.display_name}
                    </span>
                  )}
                  <p className="whitespace-pre-wrap break-words leading-relaxed">{msg.content}</p>

                  {/* Timestamp & Receipt status */}
                  <div
                    className={`flex items-center justify-end gap-1 mt-1 text-[10px] ${
                      isMe ? "text-blue-100" : "text-[var(--color-text-tertiary)]"
                    }`}
                  >
                    <span>{formatTimestamp(msg.created_at)}</span>
                    {isMe && (
                      <span title={isRead ? "Read" : "Sent"}>
                        {isRead ? (
                          <CheckCheck className="w-3.5 h-3.5 text-blue-200" />
                        ) : (
                          <Check className="w-3.5 h-3.5 text-blue-200/80" />
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

      {/* Message Composer Bar */}
      <form onSubmit={handleSend} className="p-3 border-t border-[var(--color-border-primary)] bg-[var(--color-bg-sidebar)]">
        <div className="flex items-center gap-2 bg-[var(--color-bg-input)] rounded-[var(--radius-md)] p-1.5 border border-[var(--color-border-primary)] focus-within:border-[var(--color-signal-blue)] focus-within:bg-white transition-all">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
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
