import { create } from "zustand";
import { User } from "@/types";

interface AppState {
  currentUser: User | null;
  selectedConversationId: string | null;
  searchQuery: string;
  wsConnected: boolean;
  
  // Actions
  setCurrentUser: (user: User | null) => void;
  setSelectedConversationId: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  setWsConnected: (connected: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentUser: null,
  selectedConversationId: null,
  searchQuery: "",
  wsConnected: false,

  setCurrentUser: (user) => set({ currentUser: user }),
  setSelectedConversationId: (id) => set({ selectedConversationId: id }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
}));
