import { Suspense } from "react";
import { VerifyForm } from "@/features/auth/VerifyForm";

export default function VerifyPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg-secondary)] p-4">
      <Suspense fallback={<div className="text-sm text-[var(--color-text-secondary)]">Loading...</div>}>
        <VerifyForm />
      </Suspense>
    </div>
  );
}
