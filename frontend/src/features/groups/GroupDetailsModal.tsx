"use client";

import React, { useState } from "react";
import { X, Users, UserPlus, Trash2, ShieldCheck, Loader2 } from "lucide-react";
import { Conversation, Participant } from "@/hooks/useConversations";
import { useContacts } from "@/hooks/useContacts";
import { User } from "@/types";
import { getInitials } from "@/lib/utils";

interface GroupDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  conversation: Conversation;
  currentUser: User | null;
  onAddMember: (conversationId: string, userId: string) => Promise<void>;
  onRemoveMember: (conversationId: string, userId: string) => Promise<void>;
}

export function GroupDetailsModal({
  isOpen,
  onClose,
  conversation,
  currentUser,
  onAddMember,
  onRemoveMember,
}: GroupDetailsModalProps) {
  const { contacts } = useContacts();
  const [showAddPicker, setShowAddPicker] = useState(false);
  const [loadingUserId, setLoadingUserId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || conversation.type !== "GROUP") return null;

  const currentParticipant = conversation.participants.find(
    (p) => p.user_id === currentUser?.id
  );
  const isAdmin = currentParticipant?.role === "ADMIN";

  // Filter contacts who are not already active members in the group
  const availableContacts = contacts.filter(
    (c) => !conversation.participants.some((p) => p.user_id === c.user.id)
  );

  const handleAddUser = async (userId: string) => {
    try {
      setLoadingUserId(userId);
      setError(null);
      await onAddMember(conversation.id, userId);
      setShowAddPicker(false);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to add member");
      }
    } finally {
      setLoadingUserId(null);
    }
  };

  const handleRemoveUser = async (userId: string) => {
    try {
      setLoadingUserId(userId);
      setError(null);
      await onRemoveMember(conversation.id, userId);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to remove member");
      }
    } finally {
      setLoadingUserId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in-50">
      <div className="w-full max-w-md bg-[var(--color-bg-card)] rounded-[var(--radius-lg)] shadow-xl border border-[var(--color-border-primary)] overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-4 py-3 border-b border-[var(--color-border-primary)] flex items-center justify-between bg-[var(--color-bg-sidebar)]">
          <div className="flex items-center gap-2 text-[var(--color-text-primary)]">
            <Users className="w-4 h-4 text-[var(--color-signal-blue)]" />
            <h3 className="font-bold text-sm truncate">{conversation.name || "Group Details"}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-[var(--radius-md)] text-[var(--color-text-tertiary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-hover)] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 space-y-4 flex-1 overflow-y-auto">
          {error && (
            <div className="p-2.5 rounded-[var(--radius-md)] bg-red-50 text-[var(--color-error)] text-xs border border-red-200">
              {error}
            </div>
          )}

          {/* Group Header Info */}
          <div className="flex items-center gap-3 p-3 bg-[var(--color-bg-sidebar)] rounded-[var(--radius-md)] border border-[var(--color-border-light)]">
            <div className="w-12 h-12 rounded-full bg-[var(--color-signal-blue)] text-white flex items-center justify-center font-bold text-base shadow-xs">
              {getInitials(conversation.name || "Group")}
            </div>
            <div>
              <h4 className="font-bold text-sm text-[var(--color-text-primary)]">
                {conversation.name}
              </h4>
              <p className="text-xs text-[var(--color-text-secondary)]">
                {conversation.participants.length} members
              </p>
            </div>
          </div>

          {/* Admin Action: Add Member */}
          {isAdmin && (
            <div>
              <button
                onClick={() => setShowAddPicker(!showAddPicker)}
                className="w-full py-2 px-3 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-[var(--radius-md)] text-xs font-bold flex items-center justify-center gap-2 transition-colors border border-emerald-200"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Add Member to Group</span>
              </button>

              {showAddPicker && (
                <div className="mt-2 border border-[var(--color-border-primary)] rounded-[var(--radius-md)] p-2 space-y-1 bg-[var(--color-bg-sidebar)] max-h-40 overflow-y-auto">
                  <p className="text-[10px] font-bold text-[var(--color-text-tertiary)] uppercase px-1 mb-1">
                    Select Contact to Add:
                  </p>
                  {availableContacts.length === 0 ? (
                    <p className="text-xs text-[var(--color-text-tertiary)] p-2 text-center">
                      No contacts available to add.
                    </p>
                  ) : (
                    availableContacts.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => handleAddUser(c.user.id)}
                        disabled={loadingUserId === c.user.id}
                        className="w-full flex items-center justify-between p-1.5 hover:bg-[var(--color-bg-hover)] rounded-[var(--radius-md)] text-left transition-colors"
                      >
                        <span className="text-xs font-medium text-[var(--color-text-primary)] truncate">
                          {c.user.display_name} ({c.user.phone_number})
                        </span>
                        {loadingUserId === c.user.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--color-signal-blue)]" />
                        ) : (
                          <span className="text-[10px] font-bold text-emerald-600">Add</span>
                        )}
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          )}

          {/* Members List */}
          <div>
            <h5 className="text-[11px] font-bold text-[var(--color-text-secondary)] uppercase tracking-wider mb-2">
              Group Members ({conversation.participants.length})
            </h5>
            <div className="space-y-1 border border-[var(--color-border-light)] rounded-[var(--radius-md)] p-1 divide-y divide-[var(--color-border-light)]">
              {conversation.participants.map((p: Participant) => {
                const isMe = p.user_id === currentUser?.id;
                const pIsAdmin = p.role === "ADMIN";

                return (
                  <div
                    key={p.id}
                    className="flex items-center justify-between p-2 text-xs hover:bg-[var(--color-bg-sidebar)] transition-colors"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-8 h-8 rounded-full bg-[var(--color-signal-blue)] text-white flex items-center justify-center font-bold text-xs flex-shrink-0">
                        {getInitials(p.user.display_name)}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-[var(--color-text-primary)] truncate">
                            {p.user.display_name} {isMe && "(You)"}
                          </span>
                          {pIsAdmin && (
                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] font-bold bg-amber-100 text-amber-800 rounded-xs border border-amber-200">
                              <ShieldCheck className="w-2.5 h-2.5 text-amber-600" />
                              ADMIN
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-[var(--color-text-tertiary)] font-mono truncate">
                          {p.user.phone_number}
                        </p>
                      </div>
                    </div>

                    {/* Admin Delete Control */}
                    {isAdmin && !isMe && (
                      <button
                        onClick={() => handleRemoveUser(p.user_id)}
                        disabled={loadingUserId === p.user_id}
                        title="Remove member from group"
                        className="p-1.5 text-red-500 hover:bg-red-50 rounded-[var(--radius-md)] transition-colors disabled:opacity-50"
                      >
                        {loadingUserId === p.user_id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-[var(--color-border-primary)] bg-[var(--color-bg-sidebar)] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium bg-[var(--color-bg-hover)] text-[var(--color-text-primary)] rounded-[var(--radius-md)] hover:bg-[var(--color-border-primary)] transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
