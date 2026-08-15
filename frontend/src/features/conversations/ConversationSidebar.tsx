"use client";

import React, { useState } from "react";
import { Search, SquarePen, Users, MessageSquare, Circle } from "lucide-react";
import { Conversation } from "@/hooks/useConversations";
import { useAppStore } from "@/stores/appStore";
import { formatTimestamp, getInitials } from "@/lib/utils";
import { User } from "@/types";

interface ConversationSidebarProps {
  conversations: Conversation[];
  selectedConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onOpenContactsModal: () => void;
  onOpenCreateGroupModal: () => void;
  onOpenSettingsModal: () => void;
  currentUser: User | null;
}

export function ConversationSidebar({
  conversations,
  selectedConversationId,
  onSelectConversation,
  onOpenContactsModal,
  onOpenCreateGroupModal,
  onOpenSettingsModal,
  currentUser,
}: ConversationSidebarProps) {
  const [filterQuery, setFilterQuery] = useState("");
  const presence = useAppStore((state) => state.presence);

  const filteredConversations = conversations.filter((conv) => {
    if (!filterQuery.trim()) return true;
    const q = filterQuery.toLowerCase();
    const nameMatch = conv.name?.toLowerCase().includes(q);
    const otherUserMatch =
      conv.other_user?.display_name.toLowerCase().includes(q) ||
      conv.other_user?.phone_number.includes(q);
    return nameMatch || otherUserMatch;
  });

  return (
    <aside className="w-[320px] h-full bg-[var(--color-bg-sidebar)] border-r border-[var(--color-border-primary)] flex flex-col flex-shrink-0">
      {/* Sidebar Top Header */}
      <div className="p-3 border-b border-[var(--color-border-primary)] flex items-center justify-between bg-[var(--color-bg-sidebar)]">
        <div
          onClick={onOpenSettingsModal}
          className="flex items-center gap-2 cursor-pointer group"
          title="Open Settings"
        >
          <div className="w-8 h-8 rounded-full bg-[var(--color-signal-blue)] text-white flex items-center justify-center font-bold text-xs shadow-xs group-hover:opacity-90 transition-opacity">
            {currentUser ? getInitials(currentUser.display_name) : "S"}
          </div>
          <span className="font-bold text-sm text-[var(--color-text-primary)] tracking-tight group-hover:text-[var(--color-signal-blue)] transition-colors">
            Signal
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={onOpenCreateGroupModal}
            title="New Group Chat"
            className="p-1.5 rounded-[var(--radius-md)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] transition-colors"
          >
            <Users className="w-4 h-4 text-[var(--color-signal-blue)]" />
          </button>
          <button
            onClick={onOpenContactsModal}
            title="Contacts & New Chat"
            className="p-1.5 rounded-[var(--radius-md)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] transition-colors"
          >
            <SquarePen className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Search Filter Input */}
      <div className="p-2.5 border-b border-[var(--color-border-light)]">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[var(--color-text-tertiary)]" />
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Search conversations & groups..."
            className="w-full pl-8 pr-3 py-1.5 bg-[var(--color-bg-input)] text-xs rounded-[var(--radius-md)] border border-transparent focus:border-[var(--color-border-primary)] focus:bg-white focus:outline-none transition-all"
          />
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-1 space-y-0.5">
        {filteredConversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 p-4 text-center text-xs text-[var(--color-text-secondary)]">
            <MessageSquare className="w-8 h-8 text-[var(--color-text-tertiary)] mb-2 stroke-1" />
            <p className="font-semibold text-[var(--color-text-primary)] mb-1">No chats found</p>
            <p className="text-[11px] mb-3">
              {filterQuery ? "No conversation matches your search query." : "You don't have any conversations yet."}
            </p>
            {!filterQuery && (
              <div className="flex items-center gap-2">
                <button
                  onClick={onOpenContactsModal}
                  className="px-3 py-1.5 bg-[var(--color-signal-blue)] text-white font-medium rounded-[var(--radius-md)] text-xs hover:bg-[var(--color-signal-blue-dark)] transition-colors"
                >
                  Start Direct Chat
                </button>
                <button
                  onClick={onOpenCreateGroupModal}
                  className="px-3 py-1.5 bg-emerald-600 text-white font-medium rounded-[var(--radius-md)] text-xs hover:bg-emerald-700 transition-colors"
                >
                  New Group
                </button>
              </div>
            )}
          </div>
        ) : (
          filteredConversations.map((conv) => {
            const isSelected = conv.id === selectedConversationId;
            const isGroup = conv.type === "GROUP";
            const displayName =
              isGroup
                ? conv.name || "Group Conversation"
                : conv.other_user?.display_name || "Conversation";

            const otherUserId = conv.type === "DIRECT" ? conv.other_user?.id : undefined;
            const isOnline = otherUserId ? presence[otherUserId]?.status === "online" : false;
            const hasUnread = (conv.unread_count || 0) > 0;

            return (
              <button
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`w-full text-left p-2.5 rounded-[var(--radius-md)] flex items-center gap-3 transition-colors ${
                  isSelected
                    ? "bg-[var(--color-bg-selected)]"
                    : "hover:bg-[var(--color-bg-hover)]"
                }`}
              >
                {/* Avatar with presence dot / Group Badge */}
                <div className="relative flex-shrink-0">
                  <div
                    className={`w-10 h-10 rounded-full text-white flex items-center justify-center font-bold text-xs shadow-xs ${
                      isGroup ? "bg-indigo-600" : "bg-[var(--color-signal-blue)]"
                    }`}
                  >
                    {isGroup ? <Users className="w-5 h-5" /> : getInitials(displayName)}
                  </div>
                  {otherUserId && (
                    <Circle
                      className={`w-3 h-3 absolute -bottom-0.5 -right-0.5 rounded-full border-2 border-[var(--color-bg-sidebar)] transition-colors duration-300 ${
                        isOnline ? "fill-emerald-500 text-emerald-500" : "fill-gray-300 text-gray-300"
                      }`}
                    />
                  )}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <span
                      className={`text-xs truncate ${
                        hasUnread ? "font-extrabold text-[var(--color-text-primary)]" : "font-bold text-[var(--color-text-primary)]"
                      }`}
                    >
                      {displayName}
                    </span>
                    <span className="text-[10px] text-[var(--color-text-tertiary)] flex-shrink-0">
                      {formatTimestamp(conv.updated_at)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-1">
                    <p
                      className={`text-[11px] truncate italic ${
                        hasUnread ? "font-semibold text-[var(--color-text-primary)]" : "text-[var(--color-text-secondary)]"
                      }`}
                    >
                      {conv.last_message ? conv.last_message.content : "No messages yet"}
                    </p>

                    {/* Unread Count Badge */}
                    {hasUnread && (
                      <span className="px-1.5 py-0.5 bg-[var(--color-signal-blue)] text-white text-[10px] font-bold rounded-full flex-shrink-0">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}
