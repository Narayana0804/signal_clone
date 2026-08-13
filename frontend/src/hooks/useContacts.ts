"use client";

import { useCallback, useEffect, useState } from "react";
import { apiRequest, ApiError } from "@/lib/api";
import { User } from "@/types";

export interface ContactItem {
  id: string;
  user: User;
  created_at: string;
}

export function useContacts() {
  const [contacts, setContacts] = useState<ContactItem[]>([]);
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchContacts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiRequest<{ contacts: ContactItem[] }>("/contacts");
      setContacts(data.contacts || []);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load contacts");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  const searchUsers = async (query: string) => {
    if (!query.trim() || query.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      setSearching(true);
      setError(null);
      const data = await apiRequest<{ users: User[] }>(
        `/users/search?q=${encodeURIComponent(query.trim())}`
      );
      setSearchResults(data.users || []);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      }
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const addContact = async (contactUserId: string) => {
    try {
      setError(null);
      const newContact = await apiRequest<ContactItem>("/contacts", {
        method: "POST",
        body: JSON.stringify({ contact_user_id: contactUserId }),
      });
      setContacts((prev) => [newContact, ...prev]);
      // Remove from search results once added
      setSearchResults((prev) => prev.filter((u) => u.id !== contactUserId));
      return newContact;
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to add contact");
      }
      throw err;
    }
  };

  const removeContact = async (contactId: string) => {
    try {
      setError(null);
      await apiRequest(`/contacts/${contactId}`, { method: "DELETE" });
      setContacts((prev) => prev.filter((c) => c.id !== contactId));
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to remove contact");
      }
      throw err;
    }
  };

  return {
    contacts,
    searchResults,
    loading,
    searching,
    error,
    searchUsers,
    addContact,
    removeContact,
    fetchContacts,
  };
}
