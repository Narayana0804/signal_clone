"use client";

import React from "react";
import { MessageSquare, Shield, Lock, Send } from "lucide-react";
import { Conversation } from "@/hooks/useConversations";
import { getInitials } from "@/lib/utils";

interface ChatPanePlaceholderProps {
  conversation: Conversation | null;
}

export function ChatPanePlaceholder({ conversation }: ChatPanePlaceholderProps) {
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

        <div className="flex items-center gap-2 text-xs text-[var(--color-text-tertiary)]">
          <Shield className="w-4 h-4 text-[var(--color-signal-blue)]" />
          <span className="text-[11px]">End-to-End Encrypted (Simulated)</span>
        </div>
      </div>

      {/* Main Message View Placeholder */}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center justify-center">
        <div className="max-w-sm text-center bg-[var(--color-bg-secondary)] p-6 rounded-[var(--radius-lg)] border border-[var(--color-border-light)] shadow-xs">
          <div className="w-12 h-12 bg-white text-[var(--color-signal-blue)] rounded-full flex items-center justify-center mx-auto mb-3 shadow-xs border border-[var(--color-border-light)]">
            <Lock className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-sm text-[var(--color-text-primary)] mb-1">
            Conversation Created
          </h3>
          <p className="text-xs text-[var(--color-text-secondary)] mb-3 leading-relaxed">
            You are now connected with <strong className="text-[var(--color-text-primary)]">{displayName}</strong>.
          </p>
          <div className="p-2.5 bg-blue-50 text-blue-800 text-[11px] rounded-[var(--radius-md)] border border-blue-200/60 font-medium">
            Persistent real-time message exchange and WebSocket synchronization will be enabled in Phase 5.
          </div>
        </div>
      </div>

      {/* Message Composer Bar (Disabled for Phase 4) */}
      <div className="p-3 border-t border-[var(--color-border-primary)] bg-[var(--color-bg-sidebar)]">
        <div className="flex items-center gap-2 bg-[var(--color-bg-input)] rounded-[var(--radius-md)] p-1.5 border border-[var(--color-border-primary)]">
          <input
            type="text"
            disabled
            placeholder="Send a message (Phase 5 Messaging Activation Pending)..."
            className="flex-1 bg-transparent px-2 text-xs text-[var(--color-text-tertiary)] cursor-not-allowed outline-none"
          />
          <button
            disabled
            className="p-1.5 bg-[var(--color-signal-blue)] text-white rounded-[var(--radius-sm)] opacity-40 cursor-not-allowed"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </main>
  );
}
