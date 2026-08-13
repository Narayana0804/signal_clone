# ARCHITECTURE.md — Signal Clone

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │              Next.js Frontend (React/TS)              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐  │   │
│  │  │   Auth   │ │  Convos  │ │ Messaging │ │ Groups │  │   │
│  │  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └───┬────┘  │   │
│  │       │             │             │           │        │   │
│  │  ┌────┴─────────────┴─────────────┴───────────┴────┐  │   │
│  │  │           API Client + WebSocket Hook            │  │   │
│  │  └─────────────────────┬───────────────────────────┘  │   │
│  └────────────────────────┼──────────────────────────────┘   │
└───────────────────────────┼──────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │  REST (HTTP) │  WebSocket  │
              └──────┬───────┴──────┬──────┘
                     │              │
┌────────────────────┼──────────────┼──────────────────────────┐
│                 FastAPI Backend                                │
│  ┌─────────────────┼──────────────┼───────────────────────┐  │
│  │           ┌─────┴─────┐  ┌─────┴──────┐               │  │
│  │           │  Routers   │  │  WebSocket │               │  │
│  │           │  (REST)    │  │  Manager   │               │  │
│  │           └─────┬─────┘  └─────┬──────┘               │  │
│  │                 │              │                        │  │
│  │           ┌─────┴──────────────┴──────┐               │  │
│  │           │       Services            │               │  │
│  │           │  (Business Logic Layer)   │               │  │
│  │           └─────────────┬─────────────┘               │  │
│  │                         │                              │  │
│  │           ┌─────────────┴─────────────┐               │  │
│  │           │     Repositories          │               │  │
│  │           │  (Data Access Layer)      │               │  │
│  │           └─────────────┬─────────────┘               │  │
│  │                         │                              │  │
│  │           ┌─────────────┴─────────────┐               │  │
│  │           │   SQLAlchemy ORM Models   │               │  │
│  │           └─────────────┬─────────────┘               │  │
│  └─────────────────────────┼─────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │     SQLite      │
                    │  (signal.db)    │
                    └─────────────────┘
```

## Monorepo Structure

```
signal_clone/
├── frontend/                    # Next.js application
│   ├── app/                     # App Router pages
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Landing → redirect
│   │   ├── (auth)/              # Auth route group
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   └── (main)/              # Authenticated route group
│   │       └── chat/page.tsx    # Main messaging view
│   ├── components/
│   │   ├── ui/                  # Primitives (Button, Input, Avatar, Badge)
│   │   ├── layout/              # AppShell, Sidebar, ChatPane
│   │   ├── modals/              # CreateGroup, AddContact, UserProfile
│   │   └── feedback/            # Toast, Spinner, EmptyState, ErrorBoundary
│   ├── features/
│   │   ├── auth/                # Login, Register, OTP forms
│   │   ├── conversations/       # ConversationList, ConversationItem, Search
│   │   ├── messaging/           # MessageList, MessageBubble, Composer, TypingIndicator
│   │   ├── contacts/            # ContactList, AddContact
│   │   ├── groups/              # GroupInfo, MemberList, GroupSettings
│   │   └── profile/             # ProfileView, ProfileEdit
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   ├── useConversations.ts
│   │   ├── useMessages.ts
│   │   └── useTyping.ts
│   ├── lib/
│   │   ├── api.ts               # REST API client (fetch wrapper)
│   │   ├── ws.ts                # WebSocket client singleton
│   │   └── utils.ts             # Formatters, helpers
│   ├── stores/
│   │   └── appStore.ts          # Zustand store for client state
│   ├── types/
│   │   └── index.ts             # Shared TypeScript types
│   ├── public/
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry, CORS, lifespan
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── database.py          # SQLAlchemy engine, session factory
│   │   ├── dependencies.py      # Dependency injection (get_db, get_current_user)
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── session.py
│   │   │   ├── contact.py
│   │   │   ├── conversation.py
│   │   │   ├── participant.py
│   │   │   ├── message.py
│   │   │   └── message_receipt.py
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── contact.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   └── websocket.py
│   │   ├── routers/             # FastAPI route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── contacts.py
│   │   │   ├── conversations.py
│   │   │   ├── messages.py
│   │   │   └── health.py
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── contact_service.py
│   │   │   ├── conversation_service.py
│   │   │   ├── message_service.py
│   │   │   └── receipt_service.py
│   │   ├── repositories/        # Data access
│   │   │   ├── __init__.py
│   │   │   ├── user_repo.py
│   │   │   ├── session_repo.py
│   │   │   ├── contact_repo.py
│   │   │   ├── conversation_repo.py
│   │   │   ├── message_repo.py
│   │   │   └── receipt_repo.py
│   │   ├── websocket/           # WebSocket handling
│   │   │   ├── __init__.py
│   │   │   ├── manager.py       # ConnectionManager (in-memory user→connections map)
│   │   │   ├── handler.py       # Event routing/dispatch
│   │   │   └── events.py        # Event type definitions
│   │   └── seed.py              # Database seed script
│   ├── alembic/                 # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_contacts.py
│       ├── test_conversations.py
│       ├── test_messages.py
│       ├── test_receipts.py
│       └── test_websocket.py
│
├── .env.example
├── .gitignore
├── README.md
├── PROJECT_SPEC.md
├── ARCHITECTURE.md
├── DATABASE.md
├── API_SPEC.md
├── WEBSOCKET_SPEC.md
├── DECISIONS.md
├── IMPLEMENTATION_PLAN.md
├── TEST_PLAN.md
├── DEPLOYMENT.md
└── INTERVIEW_PREP.md
```

## Layer Responsibilities

### Routers (API Layer)
- Parse and validate HTTP requests via Pydantic schemas
- Extract authenticated user from dependency injection
- Delegate to service layer
- Return Pydantic response models
- Handle HTTP status codes and error responses
- **NO business logic**

### Services (Business Logic Layer)
- Enforce business rules and invariants
- Orchestrate repository calls
- Enforce authorization (e.g., "user must be a participant", "user must be admin")
- Coordinate cross-domain operations (e.g., create message + generate receipts + emit WS event)
- **NO direct SQL or ORM queries**

### Repositories (Data Access Layer)
- Execute database queries via SQLAlchemy
- Map between ORM models and domain needs
- Handle pagination, filtering
- **NO business rules or authorization logic**

### WebSocket Manager
- Maintain in-memory mapping: `user_id → Set[WebSocket]`
- Handle connect/disconnect lifecycle
- Broadcast events to specific users or conversation participants
- **NO message persistence** (delegates to services)

### WebSocket Handler
- Parse incoming WebSocket messages
- Route to appropriate service methods
- Format outgoing events per protocol spec
- **NO direct database access**

## Authentication Flow

```
Client                    Backend
  │                         │
  ├─ POST /auth/register ──►│  Create user (phone_number, display_name)
  │◄── 201 { user_id } ────┤
  │                         │
  ├─ POST /auth/verify ────►│  Verify OTP (always "123456")
  │◄── 200 { } ────────────┤
  │                         │
  ├─ POST /auth/login ─────►│  Create session, return token
  │◄── 200 Set-Cookie ─────┤  HTTP-only cookie: session_token
  │                         │
  ├─ GET /auth/me ──────────►│  Validate session, return user
  │◄── 200 { user } ────────┤
  │                         │
  ├─ WS /ws?token=... ─────►│  Authenticate WebSocket via query param
  │◄── connection.ready ────┤  (token is short-lived or session-derived)
```

### Session Design
- Sessions stored in `sessions` table with `token_hash` (SHA-256 of raw token)
- Raw token sent to client via HTTP-only cookie (`session_token`)
- For WebSocket: token sent as query parameter (acceptable for assignment; documented limitation)
- Session expiry: 7 days
- On logout: session row deleted

## State Management Strategy

### Server State (React Query / SWR pattern via custom hooks)
- User profile, contacts, conversations, messages, participants
- Fetched via REST API
- Invalidated/updated via WebSocket events

### Client State (Zustand — single lightweight store)
- Selected conversation ID
- Search query
- UI modal state
- Draft messages (per conversation)
- WebSocket connection status
- Typing indicators (ephemeral, per conversation)

### Why Zustand
- Minimal boilerplate vs Redux
- No context provider nesting issues
- Works well alongside direct fetch-based server state
- Single store sufficient for this app's client-state needs

## Cross-Cutting Concerns

### Error Handling
- Backend: FastAPI exception handlers → structured JSON error responses
- Frontend: Error boundaries + toast notifications
- WebSocket: Error events for invalid operations

### CORS
- Configured in FastAPI `main.py`
- Allows frontend origin only
- Credentials: true (for cookies)

### Environment Variables
- Backend: `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, `ENVIRONMENT`
- Frontend: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`

### Logging
- Backend: Python `logging` with structured format
- Startup, shutdown, WS connect/disconnect, errors
- No sensitive data in logs
