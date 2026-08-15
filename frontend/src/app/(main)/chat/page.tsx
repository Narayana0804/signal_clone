"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useConversations } from "@/hooks/useConversations";
import { useContacts } from "@/hooks/useContacts";
import { useWebSocket, WSEventEnvelope } from "@/hooks/useWebSocket";
import { useAppStore } from "@/stores/appStore";
import { ConversationSidebar } from "@/features/conversations/ConversationSidebar";
import { ChatPane } from "@/features/conversations/ChatPane";
import { ContactList } from "@/features/contacts/ContactList";
import { CreateGroupModal } from "@/features/groups/CreateGroupModal";
import { GroupDetailsModal } from "@/features/groups/GroupDetailsModal";
import { SettingsModal } from "@/features/groups/SettingsModal";
import { Toast, ToastProps } from "@/components/Toast";
import { X, MessageSquarePlus } from "lucide-react";
import { getInitials } from "@/lib/utils";

export default function ChatPage() {
  const router = useRouter();
  const { currentUser, loading: authLoading, fetchMe } = useAuth();
  const updatePresence = useAppStore((state) => state.updatePresence);
  const {
    conversations,
    selectedConversation,
    selectedConversationId,
    selectConversation,
    createDirectConversation,
    createGroup,
    addGroupMember,
    removeGroupMember,
    fetchConversations,
  } = useConversations();
  const { contacts } = useContacts();

  const [showContactsModal, setShowContactsModal] = useState(false);
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [showGroupDetailsModal, setShowGroupDetailsModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [toast, setToast] = useState<Omit<ToastProps, "onClose"> | null>(null);

  // Page-level WebSocket event handler (presence + conversation list updates)
  const handleWSEvent = useCallback(
    (event: WSEventEnvelope) => {
      if (
        event.type === "message.created" ||
        event.type === "message.read" ||
        event.type === "conversation.created" ||
        event.type === "group.created" ||
        event.type === "group.member_added" ||
        event.type === "group.member_removed"
      ) {
        fetchConversations();
      }

      if (event.type === "presence.updated") {
        const { user_id, status, last_seen_at } = event.payload;
        updatePresence(user_id, status, last_seen_at ?? null);
      }
    },
    [fetchConversations, updatePresence]
  );

  useWebSocket(handleWSEvent);

  useEffect(() => {
    if (!authLoading && !currentUser) {
      router.push("/login");
    }
  }, [authLoading, currentUser, router]);

  if (authLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-[var(--color-signal-blue)] border-t-transparent rounded-full animate-spin"></div>
          <span>Validating session...</span>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return null;
  }

  const handleStartChatWithUser = async (targetUserId: string) => {
    try {
      await createDirectConversation(targetUserId);
      setShowContactsModal(false);
    } catch {
      // Error handled in hook
    }
  };

  const handleCreateGroup = async (name: string, participantIds: string[]) => {
    await createGroup(name, participantIds);
    setToast({ type: "success", message: `Group "${name}" created successfully!` });
  };

  const handleAddMember = async (conversationId: string, userId: string) => {
    await addGroupMember(conversationId, userId);
    setToast({ type: "success", message: "Member added to group" });
  };

  const handleRemoveMember = async (conversationId: string, userId: string) => {
    await removeGroupMember(conversationId, userId);
    setToast({ type: "success", message: "Member removed from group" });
  };

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-[var(--color-bg-primary)] text-[var(--color-text-primary)]">
      {/* Signal Desktop Sidebar */}
      <ConversationSidebar
        conversations={conversations}
        selectedConversationId={selectedConversationId}
        onSelectConversation={selectConversation}
        onOpenContactsModal={() => setShowContactsModal(true)}
        onOpenCreateGroupModal={() => setShowCreateGroupModal(true)}
        onOpenSettingsModal={() => setShowSettingsModal(true)}
        currentUser={currentUser}
      />

      {/* Main Chat View */}
      <ChatPane
        conversation={selectedConversation}
        currentUser={currentUser}
        onOpenGroupDetails={() => setShowGroupDetailsModal(true)}
      />

      {/* Toast Notifications */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

      {/* Create Group Modal */}
      <CreateGroupModal
        isOpen={showCreateGroupModal}
        onClose={() => setShowCreateGroupModal(false)}
        onCreateGroup={handleCreateGroup}
      />

      {/* Group Details Modal */}
      {selectedConversation && (
        <GroupDetailsModal
          isOpen={showGroupDetailsModal}
          onClose={() => setShowGroupDetailsModal(false)}
          conversation={selectedConversation}
          currentUser={currentUser}
          onAddMember={handleAddMember}
          onRemoveMember={handleRemoveMember}
        />
      )}

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        currentUser={currentUser}
        onProfileUpdated={fetchMe}
      />

      {/* Contacts / Start Chat Modal */}
      {showContactsModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="relative w-full max-w-lg bg-[var(--color-bg-primary)] rounded-[var(--radius-lg)] shadow-[var(--shadow-modal)] border border-[var(--color-border-primary)] overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-4 border-b border-[var(--color-border-primary)] bg-[var(--color-bg-secondary)] flex items-center justify-between">
              <h2 className="font-bold text-sm text-[var(--color-text-primary)] flex items-center gap-2">
                <MessageSquarePlus className="w-4 h-4 text-[var(--color-signal-blue)]" />
                Start a New Direct Chat
              </h2>
              <button
                onClick={() => setShowContactsModal(false)}
                className="p-1 rounded-[var(--radius-sm)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Quick Chat Triggers for Existing Contacts */}
            <div className="p-4 flex-1 overflow-y-auto space-y-4">
              <div>
                <h3 className="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-2">
                  Select from Contacts
                </h3>
                {contacts.length === 0 ? (
                  <p className="text-xs text-[var(--color-text-tertiary)] italic">
                    No contacts saved yet. Use the tab below to add contacts.
                  </p>
                ) : (
                  <div className="space-y-1">
                    {contacts.map((contact) => (
                      <button
                        key={contact.id}
                        onClick={() => handleStartChatWithUser(contact.user.id)}
                        className="w-full text-left p-2.5 rounded-[var(--radius-md)] border border-[var(--color-border-light)] hover:border-[var(--color-signal-blue)] hover:bg-blue-50/50 flex items-center justify-between transition-all group"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-[var(--color-signal-blue)] text-white flex items-center justify-center font-bold text-xs">
                            {getInitials(contact.user.display_name)}
                          </div>
                          <div>
                            <span className="font-bold text-xs text-[var(--color-text-primary)] block">
                              {contact.user.display_name}
                            </span>
                            <span className="text-[11px] font-mono text-[var(--color-text-secondary)]">
                              {contact.user.phone_number}
                            </span>
                          </div>
                        </div>
                        <span className="text-xs font-medium text-[var(--color-signal-blue)] group-hover:underline">
                          Chat →
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Contact Management Component */}
              <div className="border-t border-[var(--color-border-light)] pt-4">
                <h3 className="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-2">
                  Manage Contacts & Search Users
                </h3>
                <ContactList />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
