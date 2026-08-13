"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ShieldCheck, AlertCircle, Info, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

export function VerifyForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const defaultPhone = searchParams.get("phone") || "";

  const { verifyOtp } = useAuth();

  const [phoneNumber, setPhoneNumber] = useState(defaultPhone);
  const [otp, setOtp] = useState("123456");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
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
      await verifyOtp(phoneNumber.trim(), otp.trim());
      setSuccess(true);
      setTimeout(() => {
        router.push(`/login?phone=${encodeURIComponent(phoneNumber.trim())}`);
      }, 1200);
    } catch (err: unknown) {
      if (err && typeof err === "object" && "message" in err) {
        setError(String(err.message));
      } else {
        setError("Verification failed. Make sure to use OTP '123456'.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md bg-[var(--color-bg-primary)] p-8 rounded-[var(--radius-lg)] shadow-[var(--shadow-medium)] border border-[var(--color-border-primary)]">
      <div className="text-center mb-6">
        <div className="w-14 h-14 bg-blue-50 text-[var(--color-signal-blue)] rounded-full flex items-center justify-center mx-auto mb-3 border border-blue-100">
          <ShieldCheck className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold tracking-tight">Verify Phone Number</h2>
        <p className="text-xs text-[var(--color-text-secondary)] mt-1">
          Enter the verification code sent to your phone
        </p>
      </div>

      <div className="mb-5 p-3 bg-blue-50/80 border border-blue-200/60 rounded-[var(--radius-md)] text-xs text-blue-900 flex items-start gap-2">
        <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">Mock Authentication Notice</span>
          Use fixed OTP code <code className="bg-blue-100 text-blue-800 px-1 py-0.5 rounded font-mono font-bold">123456</code> to verify.
        </div>
      </div>

      {error && (
        <div className="mb-5 p-3 rounded-[var(--radius-md)] bg-red-50 text-[var(--color-error)] text-xs flex items-center gap-2 border border-red-200">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-5 p-3 rounded-[var(--radius-md)] bg-green-50 text-green-700 text-xs flex items-center gap-2 border border-green-200">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>Phone verified successfully! Redirecting to login...</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-[var(--color-text-secondary)] mb-1.5 uppercase tracking-wider">
            Phone Number
          </label>
          <input
            type="tel"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            placeholder="+15551234567"
            className="w-full px-3 py-2.5 bg-[var(--color-bg-input)] text-sm rounded-[var(--radius-md)] border border-[var(--color-border-primary)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-signal-blue)] transition-all"
            required
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-[var(--color-text-secondary)] mb-1.5 uppercase tracking-wider">
            Verification Code (OTP)
          </label>
          <input
            type="text"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            placeholder="123456"
            maxLength={6}
            className="w-full px-3 py-2.5 text-center tracking-[0.5em] font-mono text-base bg-[var(--color-bg-input)] rounded-[var(--radius-md)] border border-[var(--color-border-primary)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-signal-blue)] transition-all font-bold"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading || success}
          className="w-full mt-2 py-2.5 px-4 bg-[var(--color-signal-blue)] hover:bg-[var(--color-signal-blue-dark)] text-white text-sm font-medium rounded-[var(--radius-md)] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? "Verifying..." : "Verify Code"}
        </button>
      </form>

      <div className="mt-6 text-center text-xs text-[var(--color-text-secondary)] border-t border-[var(--color-border-light)] pt-4">
        Need to register first?{" "}
        <Link
          href="/register"
          className="text-[var(--color-signal-blue)] font-medium hover:underline"
        >
          Register
        </Link>
      </div>
    </div>
  );
}
