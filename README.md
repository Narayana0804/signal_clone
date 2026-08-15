# Signal Clone — Real-Time Production Messaging Application

A full-stack, production-deployed Signal-inspired messaging platform supporting 1-to-1 direct messaging, multi-user group chats, group member management, 3-state delivery/read receipts, typing indicators, presence tracking, reconnect recovery, and dark/light desktop UI aesthetics.

---

## 🚀 Live Production Endpoints

- **Frontend (Vercel)**: [https://frontend-psi-snowy-58.vercel.app](https://frontend-psi-snowy-58.vercel.app)
- **Backend API (Railway)**: [https://signal-clone-backend-production.up.railway.app](https://signal-clone-backend-production.up.railway.app)
- **API Health Check**: `GET https://signal-clone-backend-production.up.railway.app/health`

---

## 🛠️ Technology Stack & Architecture

### Backend
- **Framework**: Python 3.12+ with **FastAPI**
- **ORM & Database**: **SQLAlchemy 2.x async** (`async_session`), **SQLite** in WAL mode with volume persistence (`/data/signal.db`)
- **Validation & Serialization**: **Pydantic v2**
- **Realtime**: Asynchronous WebSockets (`/api/v1/ws`) with connection state manager and automatic reconnect recovery
- **Linting & Code Quality**: `ruff` and `pytest`

### Frontend
- **Framework**: **Next.js 16 (App Router)** with **TypeScript** (`strict: true`)
- **Styling**: **Tailwind CSS v4** with Signal Desktop design system and glassmorphism styling
- **State Management**: **Zustand** store with local storage persistence
- **Icons**: `lucide-react`

---

## 💡 Key Features

### 1. Authentication & Multi-Device Sessions
- Phone number or username registration with mock OTP verification (`123456`).
- Multi-device session support with HTTP-only cookies for REST endpoints and token query parameters for WebSocket connections.
- Persistent user sessions across page reloads and browser restarts.

### 2. Direct 1-to-1 Messaging & Presence
- Real-time 1-to-1 messaging with instant optimistic UI rendering.
- 3-state message receipt transitions (`SENT` → `DELIVERED` → `READ`).
- Live presence detection (`Online` vs `Last seen at <timestamp>`) updated dynamically across co-participants.
- Throttled typing indicators with automatic inactivity timeouts.

### 3. Multi-User Group Messaging & Member Management
- Create group conversations with custom names and multiple initial contacts.
- Group member management: list active members with `ADMIN` and `MEMBER` role badges.
- Group Admin controls: add existing contacts to active groups or remove members (with sole admin protection).
- Independent per-user message receipts tracking delivery and read state for each group member.
- Sender names styled above group message bubbles with visual message grouping for consecutive messages within 5 minutes.

### 4. Offline Recovery & Reconnect Handling
- Automatic WebSocket reconnection with exponential backoff on network drop.
- Idempotent fetch of unread and missed messages upon reconnect to prevent duplicate message rendering.

---

## 📁 Repository Structure

```
signal_clone/
├── backend/
│   ├── app/
│   │   ├── models/            # SQLAlchemy ORM models (User, Conversation, Participant, Message, Receipt, Contact)
│   │   ├── repositories/      # Database query abstraction layer
│   │   ├── routers/           # FastAPI endpoints (auth, conversations, messages, contacts, health, ws)
│   │   ├── schemas/           # Pydantic v2 request/response validation
│   │   ├── services/          # Core business logic and mutation handlers
│   │   ├── database.py        # SQLite async engine configuration
│   │   ├── main.py            # FastAPI entry point & CORS configuration
│   │   ├── seed.py            # Idempotent demo database seed script
│   │   └── websocket_manager.py # Realtime connection and event broadcaster
│   └── tests/                 # Integration test suite (pytest)
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   ├── components/        # Reusable UI components (Toast, layout wrappers)
│   │   ├── features/          # Feature modules (conversations, groups, contacts)
│   │   ├── hooks/             # Custom React hooks (useAuth, useConversations, useMessages, useWebSocket)
│   │   ├── lib/               # API client and utility helpers
│   │   └── stores/            # Zustand app store
└── DEPLOYMENT.md              # Railway volume persistence & CORS production setup
```

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)
```env
DATABASE_URL=sqlite+aiosqlite:////data/signal.db
CORS_ORIGINS=https://frontend-psi-snowy-58.vercel.app
SESSION_SECRET_KEY=production-secure-secret-key
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=https://signal-clone-backend-production.up.railway.app
```

---

## 🧪 Local Setup & Development

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
pip install -r requirements.txt

# Run Database Seed
python -m app.seed

# Run Development Server
uvicorn app.main:app --reload --port 8000
```

### 2. Running Backend Tests
```bash
cd backend
pytest -v
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🔒 Security & Transport Note

All production communication takes place over HTTPS/WSS transport encryption. Full end-to-end Signal Protocol cryptography is omitted by design for demonstration and assessment purposes.
