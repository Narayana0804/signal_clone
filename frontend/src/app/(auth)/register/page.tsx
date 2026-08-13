import { Suspense } from "react";
import { RegisterForm } from "@/features/auth/RegisterForm";

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg-secondary)] p-4">
      <Suspense fallback={<div className="text-sm text-[var(--color-text-secondary)]">Loading...</div>}>
        <RegisterForm />
      </Suspense>
    </div>
  );
}
