import Link from "next/link";
import { MessageSquare, ShieldCheck, Zap } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[var(--color-bg-secondary)] text-[var(--color-text-primary)] p-6">
      <div className="max-w-md w-full bg-[var(--color-bg-primary)] rounded-[var(--radius-lg)] shadow-[var(--shadow-medium)] p-8 border border-[var(--color-border-primary)] text-center">
        <div className="w-16 h-16 bg-[var(--color-signal-blue)] text-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
          <MessageSquare className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight mb-2">Signal Clone</h1>
        <p className="text-[var(--color-text-secondary)] text-sm mb-6">
          Desktop-first secure real-time messaging platform.
        </p>

        <div className="space-y-3 mb-8 text-left border-t border-b border-[var(--color-border-light)] py-4">
          <div className="flex items-center text-xs text-[var(--color-text-secondary)] space-x-2">
            <ShieldCheck className="w-4 h-4 text-[var(--color-signal-blue)] flex-shrink-0" />
            <span>Layered Architecture & SQLite WAL Mode</span>
          </div>
          <div className="flex items-center text-xs text-[var(--color-text-secondary)] space-x-2">
            <Zap className="w-4 h-4 text-[var(--color-signal-blue)] flex-shrink-0" />
            <span>FastAPI WebSockets & Next.js App Router</span>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <Link
            href="/chat"
            className="w-full py-2.5 px-4 bg-[var(--color-signal-blue)] hover:bg-[var(--color-signal-blue-dark)] text-white text-sm font-medium rounded-[var(--radius-md)] transition-colors flex items-center justify-center"
          >
            Open Signal Web
          </Link>
        </div>
      </div>
    </div>
  );
}
