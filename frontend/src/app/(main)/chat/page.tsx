"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { LogOut, User, Shield, Phone, Calendar } from "lucide-react";
import { formatTimestamp, getInitials } from "@/lib/utils";
import { ContactList } from "@/features/contacts/ContactList";

export default function ChatPage() {
  const router = useRouter();
  const { currentUser, loading, logout } = useAuth();

  useEffect(() => {
    if (!loading && !currentUser) {
      router.push("/login");
    }
  }, [loading, currentUser, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] text-sm">
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

  return (
    <div className="min-h-screen bg-[var(--color-bg-secondary)] p-6 flex flex-col items-center justify-start">
      <div className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        {/* User Profile Card */}
        <div className="bg-[var(--color-bg-primary)] rounded-[var(--radius-lg)] shadow-[var(--shadow-medium)] border border-[var(--color-border-primary)] overflow-hidden">
          {/* Header Banner */}
          <div className="bg-[var(--color-signal-blue)] text-white p-6 text-center relative">
            <div className="w-16 h-16 bg-white text-[var(--color-signal-blue)] rounded-full flex items-center justify-center mx-auto mb-3 font-bold text-xl shadow-md border-2 border-white">
              {getInitials(currentUser.display_name)}
            </div>
            <h1 className="text-xl font-bold">{currentUser.display_name}</h1>
            <p className="text-xs text-blue-100 mt-1">{currentUser.phone_number}</p>
          </div>

          {/* Details Card */}
          <div className="p-6 space-y-4">
            <div className="flex items-center justify-between text-xs text-[var(--color-text-secondary)] border-b border-[var(--color-border-light)] pb-3">
              <span className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-[var(--color-signal-blue)]" />
                Verification Status
              </span>
              <span className="font-semibold px-2 py-0.5 rounded bg-green-100 text-green-800 border border-green-200">
                Verified
              </span>
            </div>

            <div className="flex items-center justify-between text-xs text-[var(--color-text-secondary)] border-b border-[var(--color-border-light)] pb-3">
              <span className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-[var(--color-signal-blue)]" />
                Phone Number
              </span>
              <span className="font-mono font-medium text-[var(--color-text-primary)]">
                {currentUser.phone_number}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs text-[var(--color-text-secondary)] border-b border-[var(--color-border-light)] pb-3">
              <span className="flex items-center gap-2">
                <User className="w-4 h-4 text-[var(--color-signal-blue)]" />
                About Status
              </span>
              <span className="text-[var(--color-text-primary)] italic">
                {currentUser.about || "Available"}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs text-[var(--color-text-secondary)] pb-2">
              <span className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-[var(--color-signal-blue)]" />
                Account Created
              </span>
              <span>{formatTimestamp(currentUser.created_at)}</span>
            </div>

            <div className="pt-4">
              <button
                onClick={async () => {
                  await logout();
                  router.push("/login");
                }}
                className="w-full py-2.5 px-4 bg-red-50 hover:bg-red-100 text-[var(--color-error)] border border-red-200 text-sm font-medium rounded-[var(--radius-md)] transition-colors flex items-center justify-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Sign Out (Invalidate Session)
              </button>
            </div>
          </div>
        </div>

        {/* Contacts & User Search Component */}
        <ContactList />
      </div>
    </div>
  );
}
