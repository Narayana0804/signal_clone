"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { MessageSquare, ArrowRight, AlertCircle, Phone, User } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

export function RegisterForm() {
  const router = useRouter();
  const { register } = useAuth();

  const [phoneNumber, setPhoneNumber] = useState("+15551234567");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneNumber.trim() || !displayName.trim()) {
      setError("Please fill out all fields.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await register(phoneNumber.trim(), displayName.trim());
      // Navigate to verify page with phone number in query
      router.push(`/verify?phone=${encodeURIComponent(phoneNumber.trim())}`);
    } catch (err: unknown) {
      if (err && typeof err === "object" && "message" in err) {
        setError(String(err.message));
      } else {
        setError("Failed to create account. Please check inputs.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md bg-[var(--color-bg-primary)] p-8 rounded-[var(--radius-lg)] shadow-[var(--shadow-medium)] border border-[var(--color-border-primary)]">
      <div className="text-center mb-8">
        <div className="w-14 h-14 bg-[var(--color-signal-blue)] text-white rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm">
          <MessageSquare className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold tracking-tight">Create Account</h2>
        <p className="text-xs text-[var(--color-text-secondary)] mt-1">
          Set up your Signal profile with a phone number
        </p>
      </div>

      {error && (
        <div className="mb-5 p-3 rounded-[var(--radius-md)] bg-red-50 text-[var(--color-error)] text-xs flex items-center gap-2 border border-red-200">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-[var(--color-text-secondary)] mb-1.5 uppercase tracking-wider">
            Phone Number
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[var(--color-text-tertiary)]">
              <Phone className="w-4 h-4" />
            </div>
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="+15551234567"
              className="w-full pl-9 pr-3 py-2.5 bg-[var(--color-bg-input)] text-sm rounded-[var(--radius-md)] border border-[var(--color-border-primary)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-signal-blue)] transition-all"
              required
            />
          </div>
          <span className="text-[10px] text-[var(--color-text-tertiary)] mt-1 block">
            E.164 format (e.g. +15551234567)
          </span>
        </div>

        <div>
          <label className="block text-xs font-semibold text-[var(--color-text-secondary)] mb-1.5 uppercase tracking-wider">
            Profile Name
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[var(--color-text-tertiary)]">
              <User className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Alice Smith"
              className="w-full pl-9 pr-3 py-2.5 bg-[var(--color-bg-input)] text-sm rounded-[var(--radius-md)] border border-[var(--color-border-primary)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-signal-blue)] transition-all"
              required
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 py-2.5 px-4 bg-[var(--color-signal-blue)] hover:bg-[var(--color-signal-blue-dark)] text-white text-sm font-medium rounded-[var(--radius-md)] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? "Registering..." : "Continue to Verification"}
          {!loading && <ArrowRight className="w-4 h-4" />}
        </button>
      </form>

      <div className="mt-6 text-center text-xs text-[var(--color-text-secondary)] border-t border-[var(--color-border-light)] pt-4">
        Already have an account?{" "}
        <Link
          href="/login"
          className="text-[var(--color-signal-blue)] font-medium hover:underline"
        >
          Sign In
        </Link>
      </div>
    </div>
  );
}
