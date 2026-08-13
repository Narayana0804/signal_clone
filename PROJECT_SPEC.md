# PROJECT_SPEC.md — Signal Clone

## Overview

A production-quality desktop-first Signal-like secure messaging application built as a full-stack assignment. The application reproduces Signal's information architecture, interaction patterns, visual hierarchy, and messaging experience using an independently designed codebase.

## Scope

### In Scope
- Authentication/onboarding (mocked phone verification)
- Contacts management
- Conversation list with search
- One-to-one messaging
- Real-time messaging via WebSockets
- Timestamps and message grouping
- Delivery/read receipts with per-user state
- Message state machine (SENDING → SENT → DELIVERED → READ)
- Typing indicators
- Persistent messages (SQLite)
- Group conversations with member management
- Group administration (roles, add/remove members)
- Signal-like desktop UI/UX
- Seeded demo data
- Documented API, architecture, and database schema
- Deployed working application

### Explicitly Out of Scope (Mocked/Placeholder)
- Real phone number verification (use fixed OTP: `123456`)
- Cryptographic key exchange
- Actual end-to-end encryption
- Voice/video calls
- Stories
- Linked devices

### Bonus Features (P2 — only after P0 stable)
- Reply-to messages
- Reactions (emoji)
- Dark mode toggle
- Responsive design (tablet/mobile)
- Keyboard shortcuts
- Disappearing messages
- File attachments

---

## Requirements Traceability Matrix

| ID | Description | Priority | Implementation Location | Validation | Status |
|----|-------------|----------|------------------------|------------|--------|
| **AUTH** | | | | | |
| R-AUTH-01 | User registration with phone number | P0 | `backend/app/routers/auth.py`, `frontend/features/auth/` | API test + E2E | ⬜ |
| R-AUTH-02 | Mock OTP verification (fixed code `123456`) | P0 | `backend/app/services/auth_service.py` | API test | ⬜ |
| R-AUTH-03 | User login with session token | P0 | `backend/app/routers/auth.py` | API test + E2E | ⬜ |
| R-AUTH-04 | User logout | P0 | `backend/app/routers/auth.py` | API test | ⬜ |
| R-AUTH-05 | Session persistence across refresh | P0 | `backend/app/middleware/`, frontend cookie | E2E | ⬜ |
| R-AUTH-06 | GET /auth/me — current user info | P0 | `backend/app/routers/auth.py` | API test | ⬜ |
| R-AUTH-07 | Profile setup (display name, avatar) | P0 | `backend/app/routers/auth.py` | API test | ⬜ |
| **USERS** | | | | | |
| R-USR-01 | User search by name/phone | P0 | `backend/app/routers/users.py` | API test | ⬜ |
| R-USR-02 | User profile display | P0 | `frontend/features/profile/` | Manual | ⬜ |
| **CONTACTS** | | | | | |
| R-CON-01 | List contacts | P0 | `backend/app/routers/contacts.py` | API test | ⬜ |
| R-CON-02 | Add contact | P0 | `backend/app/routers/contacts.py` | API test | ⬜ |
| R-CON-03 | Remove contact | P0 | `backend/app/routers/contacts.py` | API test | ⬜ |
| **CONVERSATIONS** | | | | | |
| R-CVS-01 | Create direct conversation | P0 | `backend/app/routers/conversations.py` | API test | ⬜ |
| R-CVS-02 | Conversation list with last message preview | P0 | `backend/app/routers/conversations.py` | API test + E2E | ⬜ |
| R-CVS-03 | Conversation ordered by most recent activity | P0 | `backend/app/routers/conversations.py` | API test | ⬜ |
| R-CVS-04 | Unread message indicators | P0 | `backend/app/services/conversation_service.py` | API test + E2E | ⬜ |
| R-CVS-05 | Search conversations | P0 | `backend/app/routers/conversations.py` | API test | ⬜ |
| R-CVS-06 | Create group conversation | P0 | `backend/app/routers/conversations.py` | API test | ⬜ |
| **MESSAGING** | | | | | |
| R-MSG-01 | Send text message | P0 | `backend/app/routers/messages.py` | API test + E2E | ⬜ |
| R-MSG-02 | Persist messages in SQLite | P0 | `backend/app/repositories/message_repo.py` | API test | ⬜ |
| R-MSG-03 | Retrieve conversation messages (paginated) | P0 | `backend/app/routers/messages.py` | API test | ⬜ |
| R-MSG-04 | Message timestamps | P0 | `frontend/features/messaging/` | Manual | ⬜ |
| R-MSG-05 | Message grouping by time/sender | P0 | `frontend/features/messaging/` | Manual | ⬜ |
| **REALTIME** | | | | | |
| R-RT-01 | WebSocket connection with authentication | P0 | `backend/app/websocket/` | WS test | ⬜ |
| R-RT-02 | Real-time message delivery to online recipients | P0 | `backend/app/websocket/manager.py` | WS test + E2E | ⬜ |
| R-RT-03 | Offline message persistence (fetch on reconnect) | P0 | `backend/app/services/message_service.py` | WS test | ⬜ |
| R-RT-04 | WebSocket reconnect handling | P0 | `frontend/hooks/useWebSocket.ts` | E2E | ⬜ |
| **RECEIPTS** | | | | | |
| R-RCP-01 | Message state: SENDING (client-side optimistic) | P0 | `frontend/features/messaging/` | E2E | ⬜ |
| R-RCP-02 | Message state: SENT (server confirmed) | P0 | `backend/app/services/message_service.py` | API test | ⬜ |
| R-RCP-03 | Message state: DELIVERED (recipient acknowledged) | P0 | `backend/app/services/receipt_service.py` | API + WS test | ⬜ |
| R-RCP-04 | Message state: READ (recipient read) | P0 | `backend/app/services/receipt_service.py` | API + WS test | ⬜ |
| R-RCP-05 | Per-user receipt state in groups | P0 | `backend/app/models/message_receipt.py` | API test | ⬜ |
| R-RCP-06 | Visual receipt indicators (✓ ✓✓ colored) | P0 | `frontend/features/messaging/` | Manual | ⬜ |
| **TYPING** | | | | | |
| R-TYP-01 | Typing indicator sent via WebSocket | P0 | `backend/app/websocket/` | WS test | ⬜ |
| R-TYP-02 | Typing indicator displayed in UI | P0 | `frontend/features/messaging/` | E2E | ⬜ |
| R-TYP-03 | Typing auto-timeout (client debounce) | P0 | `frontend/hooks/` | Manual | ⬜ |
| **GROUPS** | | | | | |
| R-GRP-01 | Create group with name and members | P0 | `backend/app/routers/conversations.py` | API test | ⬜ |
| R-GRP-02 | Group member list display | P0 | `frontend/features/groups/` | E2E | ⬜ |
| R-GRP-03 | Add members to group (admin only) | P0 | `backend/app/routers/conversations.py` | API test | ⬜ |
| R-GRP-04 | Remove members from group (admin only) | P0 | `backend/app/routers/conversations.py` | API test | ⬜ |
| R-GRP-05 | Admin role enforcement (backend) | P0 | `backend/app/services/conversation_service.py` | API test | ⬜ |
| R-GRP-06 | Group messaging (send/receive) | P0 | `backend/app/services/message_service.py` | API + WS test | ⬜ |
| **UI/UX** | | | | | |
| R-UI-01 | Signal-like desktop layout (sidebar + chat pane) | P0 | `frontend/components/layout/` | Manual | ⬜ |
| R-UI-02 | Message bubbles with sender distinction | P0 | `frontend/features/messaging/` | Manual | ⬜ |
| R-UI-03 | Avatar display | P0 | `frontend/components/ui/Avatar.tsx` | Manual | ⬜ |
| R-UI-04 | Empty states | P0 | `frontend/components/feedback/` | Manual | ⬜ |
| R-UI-05 | Loading states | P0 | `frontend/components/feedback/` | Manual | ⬜ |
| R-UI-06 | Error states and toasts | P0 | `frontend/components/feedback/` | Manual | ⬜ |
| R-UI-07 | Settings panel | P1 | `frontend/features/settings/` | Manual | ⬜ |
| **DATA** | | | | | |
| R-DAT-01 | Deterministic seed data script | P0 | `backend/app/seed.py` | Manual | ⬜ |
| R-DAT-02 | Multiple users, conversations, groups, messages | P0 | `backend/app/seed.py` | Manual | ⬜ |
| **DEPLOY** | | | | | |
| R-DEP-01 | Backend deployed and accessible | P0 | `DEPLOYMENT.md` | Manual | ⬜ |
| R-DEP-02 | Frontend deployed and accessible | P0 | `DEPLOYMENT.md` | Manual | ⬜ |
| R-DEP-03 | SQLite persistence in deployment | P0 | Deployment config | Manual | ⬜ |
| R-DEP-04 | Health endpoint | P0 | `backend/app/routers/health.py` | API test | ⬜ |
| **DOCS** | | | | | |
| R-DOC-01 | README with setup instructions | P0 | `README.md` | Manual | ⬜ |
| R-DOC-02 | Architecture documentation | P0 | `ARCHITECTURE.md` | Manual | ⬜ |
| R-DOC-03 | API documentation (OpenAPI) | P0 | FastAPI auto-docs | Manual | ⬜ |
| R-DOC-04 | Database schema documentation | P0 | `DATABASE.md` | Manual | ⬜ |
| **QUALITY** | | | | | |
| R-QAL-01 | Backend unit/integration tests (pytest) | P1 | `backend/tests/` | CI | ⬜ |
| R-QAL-02 | E2E tests (Playwright) | P1 | `frontend/e2e/` | CI | ⬜ |
| R-QAL-03 | Linting (Ruff + ESLint) | P1 | Config files | CI | ⬜ |
| **BONUS** | | | | | |
| R-BON-01 | Reply-to messages | P2 | TBD | Manual | ⬜ |
| R-BON-02 | Emoji reactions | P2 | TBD | Manual | ⬜ |
| R-BON-03 | Dark mode | P2 | TBD | Manual | ⬜ |
| R-BON-04 | Responsive design | P2 | TBD | Manual | ⬜ |
| R-BON-05 | Keyboard shortcuts | P2 | TBD | Manual | ⬜ |
| R-BON-06 | Disappearing messages | P2 | TBD | Manual | ⬜ |

---

## Evaluation Criteria Mapping

| Criterion | Key Requirements | Primary Evidence |
|-----------|-----------------|------------------|
| Functionality | R-AUTH-*, R-CVS-*, R-MSG-*, R-RT-*, R-GRP-* | Working features, seed data |
| UI/UX | R-UI-* | Signal-like desktop layout |
| Database Design | R-DAT-*, DATABASE.md | Schema, migrations, invariants |
| Backend/API Design | API_SPEC.md, R-AUTH-*, R-CVS-*, R-MSG-* | FastAPI endpoints, OpenAPI |
| Code Quality | R-QAL-* | Tests, linting, typing |
| Code Modularity | ARCHITECTURE.md | Service/repo layers, components |
| Code Understanding | INTERVIEW_PREP.md | Defensible decisions |

---

## Assumptions

1. **Authentication**: Phone verification is mocked with fixed OTP `123456`. No real SMS.
2. **Encryption**: No actual E2E encryption. Messages stored in plaintext in SQLite. Clearly documented as a known limitation.
3. **Media**: Avatar URLs are placeholder/generated. No file upload in P0.
4. **Scale**: Single-server deployment. No horizontal scaling or message queues.
5. **Browser**: Desktop Chrome/Firefox/Safari. Mobile responsiveness is P2.
6. **Deployment**: Backend on a platform with persistent filesystem for SQLite (e.g., Railway, Render with disk, or a VPS). Frontend on Vercel or similar.
