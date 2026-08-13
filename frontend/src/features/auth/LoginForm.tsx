"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { LogIn, AlertCircle, Phone, Lock } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const defaultPhone = searchParams.get("phone") || "";

  const { login } = useAuth();

  const [phoneNumber, setPhoneNumber] = useState(defaultPhone);
  const [otp, setOtp] = useState("123456");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneNumber.trim() || !otp.trim()) {
      setError("Please fill out all fields.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await login(phoneNumber.trim(), otp.trim());
      // Redirect to main chat interface upon successful authentication
      router.push("/chat");
    } catch (err: unknown) {
      if (err && typeof err === "object" && "message" in err) {
        setError(String(err.message));
      } else {
        setError("Login failed. Verify phone number and OTP '123456'.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md bg-[var(--color-bg-primary)] p-8 rounded-[var(--radius-lg)] shadow-[var(--shadow-medium)] border border-[var(--color-border-primary)]">
      <div className="text-center mb-8">
        <div className="w-14 h-14 bg-[var(--color-signal-blue)] text-white rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm">
          <LogIn className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold tracking-tight">Sign In to Signal</h2>
        <p className="text-xs text-[var(--color-text-secondary)] mt-1">
          Enter your registered phone number & verification code
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
        </div>

        <div>
          <label className="block text-xs font-semibold text-[var(--color-text-secondary)] mb-1.5 uppercase tracking-wider">
            OTP Code (Mock: 123456)
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[var(--color-text-tertiary)]">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              placeholder="123456"
              maxLength={6}
              className="w-full pl-9 pr-3 py-2.5 font-mono tracking-widest text-sm bg-[var(--color-bg-input)] rounded-[var(--radius-md)] border border-[var(--color-border-primary)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-signal-blue)] transition-all"
              required
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 py-2.5 px-4 bg-[var(--color-signal-blue)] hover:bg-[var(--color-signal-blue-dark)] text-white text-sm font-medium rounded-[var(--radius-md)] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <div className="mt-6 text-center text-xs text-[var(--color-text-secondary)] border-t border-[var(--color-border-light)] pt-4 flex justify-between">
        <Link
          href="/register"
          className="text-[var(--color-signal-blue)] font-medium hover:underline"
        >
          Create account
        </Link>
        <Link
          href="/verify"
          className="text-[var(--color-text-secondary)] hover:underline"
        >
          Verify code
        </Link>
      </div>
    </div>
  );
}
