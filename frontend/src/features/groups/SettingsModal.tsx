"use client";

import React, { useState } from "react";
import { X, User as UserIcon, Shield, Bell, Palette, Lock, Check } from "lucide-react";
import { User } from "@/types";
import { getInitials } from "@/lib/utils";
import { apiRequest } from "@/lib/api";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: User | null;
  onProfileUpdated?: () => void;
}

export function SettingsModal({
  isOpen,
  onClose,
  currentUser,
  onProfileUpdated,
}: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<"profile" | "privacy" | "notifications" | "appearance" | "security">("profile");
  const [displayName, setDisplayName] = useState(currentUser?.display_name || "");
  const [avatarUrl, setAvatarUrl] = useState(currentUser?.avatar_url || "");
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState(false);

  if (!isOpen) return null;

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await apiRequest("/users/me", {
        method: "PATCH",
        body: JSON.stringify({
          display_name: displayName.trim(),
          avatar_url: avatarUrl.trim() || null,
        }),
      });
      setSuccessMsg(true);
      setTimeout(() => setSuccessMsg(false), 2000);
      if (onProfileUpdated) onProfileUpdated();
    } catch {
      // Ignore profile update error
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in-50">
      <div className="w-full max-w-lg bg-[var(--color-bg-card)] rounded-[var(--radius-lg)] shadow-xl border border-[var(--color-border-primary)] overflow-hidden flex flex-col h-[520px]">
        {/* Header */}
        <div className="px-4 py-3 border-b border-[var(--color-border-primary)] flex items-center justify-between bg-[var(--color-bg-sidebar)]">
          <h3 className="font-bold text-sm text-[var(--color-text-primary)]">Settings</h3>
          <button
            onClick={onClose}
            className="p-1 rounded-[var(--radius-md)] text-[var(--color-text-tertiary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-hover)] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Tabs */}
          <div className="w-44 border-r border-[var(--color-border-primary)] bg-[var(--color-bg-sidebar)] p-2 space-y-1">
            <button
              onClick={() => setActiveTab("profile")}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] text-xs font-medium transition-colors ${
                activeTab === "profile"
                  ? "bg-[var(--color-bg-selected)] text-[var(--color-signal-blue)] font-bold"
                  : "text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)]"
              }`}
            >
              <UserIcon className="w-3.5 h-3.5" />
              <span>Profile</span>
            </button>

            <button
              onClick={() => setActiveTab("privacy")}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] text-xs font-medium transition-colors ${
                activeTab === "privacy"
                  ? "bg-[var(--color-bg-selected)] text-[var(--color-signal-blue)] font-bold"
                  : "text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)]"
              }`}
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Privacy</span>
            </button>

            <button
              onClick={() => setActiveTab("notifications")}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] text-xs font-medium transition-colors ${
                activeTab === "notifications"
                  ? "bg-[var(--color-bg-selected)] text-[var(--color-signal-blue)] font-bold"
                  : "text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)]"
              }`}
            >
              <Bell className="w-3.5 h-3.5" />
              <span>Notifications</span>
            </button>

            <button
              onClick={() => setActiveTab("appearance")}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] text-xs font-medium transition-colors ${
                activeTab === "appearance"
                  ? "bg-[var(--color-bg-selected)] text-[var(--color-signal-blue)] font-bold"
                  : "text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)]"
              }`}
            >
              <Palette className="w-3.5 h-3.5" />
              <span>Appearance</span>
            </button>

            <button
              onClick={() => setActiveTab("security")}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] text-xs font-medium transition-colors ${
                activeTab === "security"
                  ? "bg-[var(--color-bg-selected)] text-[var(--color-signal-blue)] font-bold"
                  : "text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)]"
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              <span>Security</span>
            </button>
          </div>

          {/* Right Detail Pane */}
          <div className="flex-1 p-5 overflow-y-auto">
            {activeTab === "profile" && (
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <h4 className="font-bold text-xs text-[var(--color-text-primary)] border-b pb-2">
                  Your Profile
                </h4>

                {/* Avatar Preview */}
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-[var(--color-signal-blue)] text-white flex items-center justify-center font-bold text-base shadow-xs overflow-hidden">
                    {avatarUrl ? (
                      <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                      getInitials(displayName || "S")
                    )}
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[var(--color-text-primary)]">{displayName}</p>
                    <p className="text-[11px] text-[var(--color-text-tertiary)] font-mono">
                      {currentUser?.phone_number}
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-[var(--color-text-secondary)] uppercase mb-1">
                    Display Name
                  </label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    required
                    className="w-full px-3 py-1.5 text-xs rounded-[var(--radius-md)] bg-[var(--color-bg-input)] border border-[var(--color-border-primary)] focus:bg-white focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-[var(--color-text-secondary)] uppercase mb-1">
                    Avatar Image URL (Optional)
                  </label>
                  <input
                    type="url"
                    value={avatarUrl}
                    onChange={(e) => setAvatarUrl(e.target.value)}
                    placeholder="https://example.com/avatar.jpg"
                    className="w-full px-3 py-1.5 text-xs rounded-[var(--radius-md)] bg-[var(--color-bg-input)] border border-[var(--color-border-primary)] focus:bg-white focus:outline-none"
                  />
                </div>

                <div className="pt-2 flex items-center gap-2">
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-1.5 bg-[var(--color-signal-blue)] text-white rounded-[var(--radius-md)] text-xs font-medium hover:bg-[var(--color-signal-blue-dark)] transition-colors"
                  >
                    {saving ? "Saving..." : "Save Profile"}
                  </button>

                  {successMsg && (
                    <span className="text-xs text-emerald-600 font-bold flex items-center gap-1">
                      <Check className="w-3.5 h-3.5" /> Saved!
                    </span>
                  )}
                </div>
              </form>
            )}

            {activeTab === "privacy" && (
              <div className="space-y-3">
                <h4 className="font-bold text-xs text-[var(--color-text-primary)] border-b pb-2">
                  Privacy Settings
                </h4>
                <div className="p-4 rounded-[var(--radius-md)] bg-gray-50 border border-gray-200 text-center text-xs text-gray-500">
                  <p className="font-semibold mb-1">Privacy Controls</p>
                  <p className="text-[11px]">Coming Soon in future update.</p>
                </div>
              </div>
            )}

            {activeTab === "notifications" && (
              <div className="space-y-3">
                <h4 className="font-bold text-xs text-[var(--color-text-primary)] border-b pb-2">
                  Notification Preferences
                </h4>
                <div className="p-4 rounded-[var(--radius-md)] bg-gray-50 border border-gray-200 text-center text-xs text-gray-500">
                  <p className="font-semibold mb-1">Push Notifications</p>
                  <p className="text-[11px]">Coming Soon in future update.</p>
                </div>
              </div>
            )}

            {activeTab === "appearance" && (
              <div className="space-y-3">
                <h4 className="font-bold text-xs text-[var(--color-text-primary)] border-b pb-2">
                  Appearance & Theme
                </h4>
                <div className="p-4 rounded-[var(--radius-md)] bg-gray-50 border border-gray-200 text-center text-xs text-gray-500">
                  <p className="font-semibold mb-1">Theme Selection</p>
                  <p className="text-[11px]">System Light Mode active (Dark Mode Coming Soon).</p>
                </div>
              </div>
            )}

            {activeTab === "security" && (
              <div className="space-y-3">
                <h4 className="font-bold text-xs text-[var(--color-text-primary)] border-b pb-2">
                  Security Disclaimer
                </h4>
                <div className="p-4 rounded-[var(--radius-md)] bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-2">
                  <div className="flex items-center gap-2 font-bold text-amber-800">
                    <Shield className="w-4 h-4 text-amber-600" />
                    <span>Transport Security Only</span>
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    This application is a Signal Clone demonstration built for assignment evaluation. All communications use TLS/HTTPS/WSS transport encryption. Full end-to-end Signal Protocol cryptography is omitted by design.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
