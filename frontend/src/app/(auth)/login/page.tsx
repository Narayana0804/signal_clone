import { Suspense } from "react";
import { LoginForm } from "@/features/auth/LoginForm";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg-secondary)] p-4">
      <Suspense fallback={<div className="text-sm text-[var(--color-text-secondary)]">Loading...</div>}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
