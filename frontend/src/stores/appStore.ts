import { create } from "zustand";
import { User } from "@/types";

interface PresenceEntry {
  status: "online" | "offline";
  last_seen_at: string | null;
}

interface AppState {
  currentUser: User | null;
  selectedConversationId: string | null;
  searchQuery: string;
  wsConnected: boolean;
  /** Ephemeral presence map: user_id → { status, last_seen_at } */
  presence: Record<string, PresenceEntry>;

  // Actions
  setCurrentUser: (user: User | null) => void;
  setSelectedConversationId: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  setWsConnected: (connected: boolean) => void;
  updatePresence: (userId: string, status: "online" | "offline", lastSeenAt: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentUser: null,
  selectedConversationId: null,
  searchQuery: "",
  wsConnected: false,
  presence: {},

  setCurrentUser: (user) => set({ currentUser: user }),
  setSelectedConversationId: (id) => set({ selectedConversationId: id }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  updatePresence: (userId, status, lastSeenAt) =>
    set((state) => ({
      presence: {
        ...state.presence,
        [userId]: { status, last_seen_at: lastSeenAt },
      },
    })),
}));
