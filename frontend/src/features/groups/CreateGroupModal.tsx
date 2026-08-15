"use client";

import React, { useState } from "react";
import { X, Users, Loader2, Check } from "lucide-react";
import { useContacts } from "@/hooks/useContacts";
import { getInitials } from "@/lib/utils";

interface CreateGroupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateGroup: (name: string, participantIds: string[]) => Promise<void>;
}

export function CreateGroupModal({
  isOpen,
  onClose,
  onCreateGroup,
}: CreateGroupModalProps) {
  const { contacts, loading: contactsLoading } = useContacts();
  const [name, setName] = useState("");
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const toggleUserSelection = (userId: string) => {
    setSelectedUserIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanName = name.trim();
    if (!cleanName) {
      setError("Please enter a group name");
      return;
    }
    if (selectedUserIds.length === 0) {
      setError("Please select at least one contact to add to the group");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      await onCreateGroup(cleanName, selectedUserIds);
      setName("");
      setSelectedUserIds([]);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to create group");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in-50">
      <div className="w-full max-w-md bg-[var(--color-bg-card)] rounded-[var(--radius-lg)] shadow-xl border border-[var(--color-border-primary)] overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-4 py-3 border-b border-[var(--color-border-primary)] flex items-center justify-between bg-[var(--color-bg-sidebar)]">
          <div className="flex items-center gap-2 text-[var(--color-text-primary)]">
            <Users className="w-4 h-4 text-[var(--color-signal-blue)]" />
            <h3 className="font-bold text-sm">New Group</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-[var(--radius-md)] text-[var(--color-text-tertiary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-hover)] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="p-4 space-y-4 flex-1 overflow-y-auto">
            {error && (
              <div className="p-2.5 rounded-[var(--radius-md)] bg-red-50 text-[var(--color-error)] text-xs border border-red-200">
                {error}
              </div>
            )}

            {/* Group Name Input */}
            <div>
              <label className="block text-[11px] font-bold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5">
                Group Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Project Team"
                maxLength={100}
                required
                className="w-full px-3 py-2 text-xs rounded-[var(--radius-md)] bg-[var(--color-bg-input)] border border-[var(--color-border-primary)] focus:bg-white focus:outline-none focus:border-[var(--color-signal-blue)] transition-all"
              />
            </div>

            {/* Contact Selector */}
            <div>
              <label className="block text-[11px] font-bold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5">
                Select Group Members ({selectedUserIds.length} selected)
              </label>

              {contactsLoading ? (
                <div className="flex items-center justify-center py-6 text-xs text-[var(--color-text-secondary)] gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-[var(--color-signal-blue)]" />
                  <span>Loading contacts...</span>
                </div>
              ) : contacts.length === 0 ? (
                <p className="text-xs text-[var(--color-text-tertiary)] py-4 text-center">
                  No contacts found. Add contacts first to invite them to groups.
                </p>
              ) : (
                <div className="space-y-1 max-h-56 overflow-y-auto border border-[var(--color-border-light)] rounded-[var(--radius-md)] p-1">
                  {contacts.map((c) => {
                    const isSelected = selectedUserIds.includes(c.user.id);
                    return (
                      <button
                        key={c.id}
                        type="button"
                        onClick={() => toggleUserSelection(c.user.id)}
                        className={`w-full flex items-center justify-between p-2 rounded-[var(--radius-md)] text-left transition-colors ${
                          isSelected
                            ? "bg-[var(--color-bg-selected)]"
                            : "hover:bg-[var(--color-bg-hover)]"
                        }`}
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="w-7 h-7 rounded-full bg-[var(--color-signal-blue)] text-white flex items-center justify-center font-bold text-[10px] flex-shrink-0">
                            {getInitials(c.user.display_name)}
                          </div>
                          <div className="min-w-0">
                            <p className="text-xs font-bold text-[var(--color-text-primary)] truncate">
                              {c.user.display_name}
                            </p>
                            <p className="text-[10px] text-[var(--color-text-tertiary)] font-mono truncate">
                              {c.user.phone_number}
                            </p>
                          </div>
                        </div>
                        <div
                          className={`w-4 h-4 rounded-xs border flex items-center justify-center transition-colors ${
                            isSelected
                              ? "bg-[var(--color-signal-blue)] border-[var(--color-signal-blue)] text-white"
                              : "border-[var(--color-border-primary)]"
                          }`}
                        >
                          {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-[var(--color-border-primary)] bg-[var(--color-bg-sidebar)] flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] rounded-[var(--radius-md)] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !name.trim() || selectedUserIds.length === 0}
              className="px-4 py-1.5 text-xs font-medium bg-[var(--color-signal-blue)] text-white rounded-[var(--radius-md)] hover:bg-[var(--color-signal-blue-dark)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
            >
              {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Create Group</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
