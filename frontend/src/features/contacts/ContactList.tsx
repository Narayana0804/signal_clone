"use client";

import React, { useState } from "react";
import { Search, UserPlus, UserMinus, Users, AlertCircle, Loader2, Check } from "lucide-react";
import { useContacts } from "@/hooks/useContacts";
import { getInitials } from "@/lib/utils";

export function ContactList() {
  const {
    contacts,
    searchResults,
    loading,
    searching,
    error,
    searchUsers,
    addContact,
    removeContact,
  } = useContacts();

  const [query, setQuery] = useState("");
  const [addingId, setAddingId] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"contacts" | "search">("contacts");

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    if (val.trim().length >= 2) {
      setActiveTab("search");
      searchUsers(val);
    } else if (val.trim().length === 0) {
      setActiveTab("contacts");
    }
  };

  const handleAdd = async (userId: string) => {
    try {
      setAddingId(userId);
      await addContact(userId);
    } catch {
      // Error handled in hook
    } finally {
      setAddingId(null);
    }
  };

  const handleRemove = async (contactId: string) => {
    try {
      setRemovingId(contactId);
      await removeContact(contactId);
    } catch {
      // Error handled in hook
    } finally {
      setRemovingId(null);
    }
  };

  const contactUserIds = new Set(contacts.map((c) => c.user.id));

  return (
    <div className="w-full max-w-lg bg-[var(--color-bg-primary)] rounded-[var(--radius-lg)] shadow-[var(--shadow-medium)] border border-[var(--color-border-primary)] overflow-hidden flex flex-col h-[550px]">
      {/* Header */}
      <div className="p-4 border-b border-[var(--color-border-primary)] bg-[var(--color-bg-secondary)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[var(--color-signal-blue)] text-white flex items-center justify-center font-semibold text-xs">
            <Users className="w-4 h-4" />
          </div>
          <h2 className="font-bold text-sm text-[var(--color-text-primary)]">Contacts</h2>
        </div>

        {/* Tab selector */}
        <div className="flex bg-[var(--color-bg-tertiary)] p-0.5 rounded-[var(--radius-md)] text-xs font-medium">
          <button
            onClick={() => setActiveTab("contacts")}
            className={`px-3 py-1 rounded-[var(--radius-sm)] transition-colors ${
              activeTab === "contacts"
                ? "bg-white text-[var(--color-text-primary)] shadow-xs font-semibold"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            }`}
          >
            My Contacts ({contacts.length})
          </button>
          <button
            onClick={() => setActiveTab("search")}
            className={`px-3 py-1 rounded-[var(--radius-sm)] transition-colors ${
              activeTab === "search"
                ? "bg-white text-[var(--color-text-primary)] shadow-xs font-semibold"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            }`}
          >
            Find Users
          </button>
        </div>
      </div>

      {/* Search Input */}
      <div className="p-3 border-b border-[var(--color-border-light)] bg-white">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-[var(--color-text-tertiary)]" />
          <input
            type="text"
            value={query}
            onChange={handleSearchChange}
            placeholder="Search by name or phone number..."
            className="w-full pl-9 pr-3 py-1.5 bg-[var(--color-bg-input)] text-xs rounded-[var(--radius-md)] border border-[var(--color-border-primary)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-signal-blue)]"
          />
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="p-2.5 mx-3 mt-3 rounded-[var(--radius-md)] bg-red-50 text-[var(--color-error)] text-xs flex items-center gap-2 border border-red-200">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-2 divide-y divide-[var(--color-border-light)]">
        {activeTab === "contacts" ? (
          loading ? (
            <div className="flex flex-col items-center justify-center h-full text-xs text-[var(--color-text-secondary)] gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-[var(--color-signal-blue)]" />
              <span>Loading contacts...</span>
            </div>
          ) : contacts.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full p-6 text-center text-xs text-[var(--color-text-secondary)]">
              <Users className="w-8 h-8 text-[var(--color-text-tertiary)] mb-2 stroke-1" />
              <p className="font-semibold text-[var(--color-text-primary)] mb-1">No contacts yet</p>
              <p>Use the search bar above to find users and add them to your contacts list.</p>
            </div>
          ) : (
            contacts.map((contact) => (
              <div
                key={contact.id}
                className="flex items-center justify-between p-2.5 hover:bg-[var(--color-bg-hover)] rounded-[var(--radius-md)] transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-[var(--color-signal-blue)] text-white flex items-center justify-center font-bold text-xs shadow-xs">
                    {getInitials(contact.user.display_name)}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-[var(--color-text-primary)]">
                      {contact.user.display_name}
                    </h3>
                    <p className="text-[11px] font-mono text-[var(--color-text-secondary)]">
                      {contact.user.phone_number}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => handleRemove(contact.id)}
                  disabled={removingId === contact.id}
                  title="Remove contact"
                  className="p-1.5 rounded-[var(--radius-sm)] text-[var(--color-text-tertiary)] hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
                >
                  {removingId === contact.id ? (
                    <Loader2 className="w-4 h-4 animate-spin text-red-600" />
                  ) : (
                    <UserMinus className="w-4 h-4" />
                  )}
                </button>
              </div>
            ))
          )
        ) : searching ? (
          <div className="flex flex-col items-center justify-center h-full text-xs text-[var(--color-text-secondary)] gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-[var(--color-signal-blue)]" />
            <span>Searching users...</span>
          </div>
        ) : searchResults.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full p-6 text-center text-xs text-[var(--color-text-secondary)]">
            <Search className="w-8 h-8 text-[var(--color-text-tertiary)] mb-2 stroke-1" />
            <p className="font-semibold text-[var(--color-text-primary)] mb-1">
              {query.trim().length < 2 ? "Type to search" : "No users found"}
            </p>
            <p>
              {query.trim().length < 2
                ? "Enter at least 2 characters to search for users by name or phone."
                : `No registered users matched "${query}".`}
            </p>
          </div>
        ) : (
          searchResults.map((user) => {
            const isAlreadyContact = contactUserIds.has(user.id);
            return (
              <div
                key={user.id}
                className="flex items-center justify-between p-2.5 hover:bg-[var(--color-bg-hover)] rounded-[var(--radius-md)] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-blue-100 text-[var(--color-signal-blue)] flex items-center justify-center font-bold text-xs">
                    {getInitials(user.display_name)}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-[var(--color-text-primary)]">
                      {user.display_name}
                    </h3>
                    <p className="text-[11px] font-mono text-[var(--color-text-secondary)]">
                      {user.phone_number}
                    </p>
                  </div>
                </div>

                {isAlreadyContact ? (
                  <span className="text-[10px] font-semibold text-green-700 bg-green-50 px-2 py-1 rounded border border-green-200 flex items-center gap-1">
                    <Check className="w-3 h-3" />
                    Contact
                  </span>
                ) : (
                  <button
                    onClick={() => handleAdd(user.id)}
                    disabled={addingId === user.id}
                    className="px-2.5 py-1 bg-[var(--color-signal-blue)] hover:bg-[var(--color-signal-blue-dark)] text-white text-xs font-medium rounded-[var(--radius-md)] transition-colors flex items-center gap-1 disabled:opacity-50"
                  >
                    {addingId === user.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <>
                        <UserPlus className="w-3.5 h-3.5" />
                        Add
                      </>
                    )}
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
