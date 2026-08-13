# DECISIONS.md — Signal Clone

## Architecture Decisions Log

### D-001: Monorepo Structure
**Decision:** Single repository with `frontend/` and `backend/` directories.
**Rationale:** Simplifies development, deployment, and review. No need for a package manager-level monorepo tool given two distinct stacks (Node.js + Python).
**Alternatives:** Separate repos — rejected for complexity.

---

### D-002: Unified Conversation Model
**Decision:** Single `conversations` table with `type` field (`DIRECT` / `GROUP`) instead of separate tables.
**Rationale:** Avoids duplicating message routing, participant management, and receipt logic. The messaging experience is fundamentally the same; only group admin features differ.
**Alternatives:** Separate `direct_chats` and `group_chats` tables — rejected for code duplication.

---

### D-003: Zustand for Client State
**Decision:** Use Zustand for UI/client state (selected conversation, modals, typing, connection status).
**Rationale:** Minimal boilerplate, no context provider nesting, works alongside fetch-based server state. The app's client state is modest enough for a single store.
**Alternatives:**
- Redux Toolkit — too heavyweight for this scope
- React Context — re-render performance issues with frequent state changes (typing, connection status)
- Jotai/Recoil — viable but Zustand has better adoption and simpler API

---

### D-004: No External State Management for Server State
**Decision:** Use custom hooks with `fetch` + local state for server data (conversations, messages) rather than React Query/SWR.
**Rationale:** The app updates server state primarily via WebSocket events. React Query's cache invalidation model doesn't align well with WebSocket-driven updates. Custom hooks give us precise control over how WS events update the local data.
**Alternatives:**
- React Query — viable but adds complexity for WebSocket integration
- SWR — same concern

*Re-evaluation note: If data fetching patterns become complex, consider introducing React Query for REST-only data (contacts, user search).*

---

### D-005: HTTP-Only Session Cookie for REST and WebSockets
**Decision:** Both REST API and WebSocket connections authenticate strictly via the HTTP-only `session_token` cookie.
**Rationale:** Eliminates credential leakage in query strings/URLs. Browser automatically includes HTTP-only cookies in WebSocket upgrade handshake. Frontend JavaScript never reads or stores raw session tokens.
**Alternatives:** Query parameter for WS — rejected in Phase 5 hardening for security concerns.

---

### D-006: Session Token Design
**Decision:** Generate 32-byte random token, store SHA-256 hash in database, return raw token to client via HTTP-only cookie.
**Rationale:** Even if the database is compromised, raw tokens are not exposed. Standard practice for session management.
**Alternatives:**
- JWT — stateless but harder to revoke, overkill for single-server SQLite
- UUID as token — less secure if database leaked

---

### D-007: SQLite with WAL Mode
**Decision:** Enable WAL (Write-Ahead Logging) mode for SQLite.
**Rationale:** Allows concurrent readers while writing. Critical for a web application with simultaneous API requests. Without WAL, SQLite serializes all access.
**Alternatives:** Default journal mode — rejected for concurrency limitations.

---

### D-008: Deterministic Cursor-Based Pagination for Messages
**Decision:** Use `before` (message ID) + `limit` with deterministic `(created_at, id)` tie-breaking.
**Rationale:** UUID string comparison does not guarantee chronological ordering. Combining `created_at` timestamp with `id` tie-breaker ensures 100% deterministic, zero-duplicate, zero-missing message pagination even when timestamps are identical.
**Alternatives:** Offset/limit — rejected for real-time message insertion issues. Plain UUID string comparison — rejected in Phase 5 hardening.

---

### D-009: Unread Count via Read Watermark
**Decision:** Track `last_read_message_id` on `conversation_participants` instead of computing unread count from individual receipts.
**Rationale:** O(1) lookup for unread watermark vs. O(n) receipt aggregation. Conversation list is a hot path. Receipts are still used for per-message status display.
**Alternatives:** Count unread from receipts table — rejected for performance on conversation list.

---

### D-010: Receipt Creation on Message Send
**Decision:** When a message is sent, create `message_receipts` entries for ALL other active participants with status `SENT`.
**Rationale:** Enables tracking per-user delivery/read state from the moment the message exists. Avoids needing to retroactively create receipts.
**Alternatives:** Create receipts lazily on delivery — would miss the SENT→DELIVERED transition.

---

### D-011: Tailwind CSS for Styling
**Decision:** Use Tailwind CSS as specified in the assignment requirements.
**Rationale:** Assignment specifies it. Provides utility-first styling with consistent design tokens. Fast iteration for Signal-like UI.
**Alternatives:** Vanilla CSS, CSS Modules — not specified by assignment.

---

### D-012: No Message Queue / Pub-Sub
**Decision:** In-memory WebSocket connection manager with direct broadcasting. No Redis, RabbitMQ, or external pub-sub.
**Rationale:** Single-server deployment with SQLite. Adding a message queue would be unnecessary complexity for a single-process application. The database is the durable event store.
**Alternatives:** Redis Pub/Sub — needed for multi-process but not for single-server.

---

### D-013: Alembic for Migrations
**Decision:** Use Alembic with auto-generated migrations from SQLAlchemy models.
**Rationale:** Assignment specifies Alembic. Standard migration tool for SQLAlchemy. Provides version control for schema changes.
**Alternatives:** Raw SQL migrations — less maintainable, not specified.

---

### D-014: Next.js App Router
**Decision:** Use Next.js App Router (not Pages Router).
**Rationale:** Modern Next.js convention. Better layout nesting. Route groups for auth vs. main views. Server components where useful (though most UI is client-side for real-time).
**Alternatives:** Pages Router — legacy, still supported but not the direction Next.js is going.

---

### D-015: `lucide-react` for Icons
**Decision:** Use `lucide-react` icon library.
**Rationale:** MIT licensed, consistent design, large icon set, tree-shakeable, popular in the React ecosystem. Signal uses simple line icons; Lucide matches this aesthetic.
**Alternatives:**
- Heroicons — good but fewer icons
- FontAwesome — heavier, licensing concerns
- Custom SVGs — too time-consuming

---

## Dependencies

### Backend
| Dependency | Purpose | Why Needed |
|-----------|---------|------------|
| `fastapi` | Web framework | Assignment requirement |
| `uvicorn` | ASGI server | Standard FastAPI server |
| `pydantic` | Schema validation | Comes with FastAPI |
| `pydantic-settings` | Config management | Environment variable loading |
| `sqlalchemy[asyncio]` | ORM | Assignment requirement (2.x) |
| `aiosqlite` | Async SQLite driver | Required for async SQLAlchemy + SQLite |
| `alembic` | Migrations | Assignment requirement |
| `python-multipart` | Form data parsing | Required for FastAPI file uploads/forms |
| `pytest` | Testing | Assignment requirement |
| `httpx` | HTTP test client | Standard for testing FastAPI |
| `pytest-asyncio` | Async test support | Required for async endpoint tests |
| `ruff` | Linting/formatting | Assignment suggests it |

### Frontend
| Dependency | Purpose | Why Needed |
|-----------|---------|------------|
| `next` | Framework | Assignment requirement |
| `react` / `react-dom` | UI library | Assignment requirement |
| `typescript` | Type safety | Assignment requirement |
| `tailwindcss` | CSS framework | Assignment requirement |
| `zustand` | Client state | Lightweight state management (D-003) |
| `lucide-react` | Icons | Signal-like icon system (D-015) |
| `eslint` | Linting | Assignment suggests it |
| `prettier` | Formatting | Assignment suggests it |

---

## Architecture Challenge Log (Pre-Phase 1)

### D-016: Add `is_verified` to Users
**Issue found:** Login endpoint accepted any registered phone number without verification. No way to distinguish verified from unverified users.
**Fix:** Added `is_verified` INTEGER field (0/1) to `users` table. Login requires `is_verified = 1`. Verify endpoint sets it.
**Impact:** DATABASE.md updated, API_SPEC.md login endpoint updated to require OTP.

### D-017: Login Requires OTP
**Issue found:** `POST /auth/login` only took `phone_number` — effectively passwordless access.
**Fix:** Login now requires `phone_number` + `otp` (always `123456`). Provides a consistent authentication factor.
**Impact:** API_SPEC.md updated.

### D-018: last_read_message_id ON DELETE SET NULL
**Issue found:** If a message referenced by `last_read_message_id` was soft-deleted or hard-deleted, the FK would break.
**Fix:** Added `ON DELETE SET NULL` to the FK constraint. If the referenced message is removed, the watermark resets gracefully.
**Impact:** DATABASE.md updated.
