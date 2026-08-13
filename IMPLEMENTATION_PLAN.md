# IMPLEMENTATION_PLAN.md — Signal Clone

## Implementation Phases

### Phase 0: Specification ✅ (Current)
- [x] Workspace reconnaissance
- [x] PROJECT_SPEC.md
- [x] ARCHITECTURE.md
- [x] DATABASE.md
- [x] API_SPEC.md
- [x] WEBSOCKET_SPEC.md
- [x] DECISIONS.md
- [x] TEST_PLAN.md
- [x] DEPLOYMENT.md
- [x] IMPLEMENTATION_PLAN.md
- [ ] Internal architecture review
- [ ] Human approval

**Time estimate:** 1-2 hours

---

### Phase 1: Foundation (~2 hours)

**Objective:** Working monorepo with frontend ↔ backend ↔ database connectivity.

**Tasks:**
1. Initialize Git repository
2. Create `.gitignore`, `.env.example`
3. Initialize Next.js frontend (`npx create-next-app`)
4. Initialize Python backend with FastAPI
5. Set up SQLAlchemy 2.x with async SQLite
6. Set up Alembic
7. Create all SQLAlchemy models (all 7 tables)
8. Generate initial Alembic migration
9. Configure CORS
10. Implement health endpoint
11. Set up logging
12. Verify: frontend runs, backend runs, database created, health endpoint responds

**Output:** Both apps running locally, database schema applied.

---

### Phase 2: Authentication (~2 hours)

**Objective:** Complete auth flow with session persistence.

**Tasks:**
1. Implement `POST /auth/register`
2. Implement `POST /auth/verify` (mock OTP)
3. Implement `POST /auth/login` (session creation, cookie)
4. Implement `POST /auth/logout`
5. Implement `GET /auth/me`
6. Implement `PATCH /auth/me` (profile update)
7. Implement `get_current_user` dependency
8. Frontend: Registration page
9. Frontend: Login page
10. Frontend: OTP verification
11. Frontend: Auth state management
12. Frontend: Protected route redirect
13. Tests: `test_auth.py`

**Output:** User can register, verify, login, persist session across refresh, logout.

---

### Phase 3: Users & Contacts (~1.5 hours)

**Objective:** User search and contact management.

**Tasks:**
1. Implement `GET /users/search`
2. Implement `GET /contacts`
3. Implement `POST /contacts`
4. Implement `DELETE /contacts/{id}`
5. Frontend: User search UI
6. Frontend: Contact list
7. Frontend: Add/remove contact
8. Tests: `test_contacts.py`

**Output:** Users can search for others and manage contacts.

---

### Phase 4: Conversations (~2 hours)

**Objective:** Direct conversations with participant management and conversation list.

**Tasks:**
1. Implement `POST /conversations` (direct + group)
2. Implement `GET /conversations` (with last message, unread count)
3. Implement `GET /conversations/{id}`
4. Frontend: Conversation list sidebar
5. Frontend: Conversation item (avatar, name, last message, unread badge, time)
6. Frontend: Start new conversation modal
7. Frontend: Search conversations
8. Frontend: Conversation selection state
9. Tests: `test_conversations.py`

**Output:** Users see conversation list, can create conversations, select them.

---

### Phase 5: Persistent Messaging (~2 hours)

**Objective:** Send, persist, retrieve, and render messages (REST only, no WebSocket yet).

**Tasks:**
1. Implement `POST /conversations/{id}/messages`
2. Implement `GET /conversations/{id}/messages` (cursor pagination)
3. Frontend: Message list component
4. Frontend: Message bubble (own vs other)
5. Frontend: Message composer (input + send)
6. Frontend: Timestamp display and message grouping
7. Frontend: Scroll behavior (scroll to bottom, load more on scroll up)
8. Tests: `test_messages.py`

**Output:** Users can send messages via REST, see message history, timestamps.

---

### Phase 6: WebSocket Real-Time (~3 hours)

**Objective:** Real-time message delivery via WebSocket.

**Tasks:**
1. Implement WebSocket endpoint `/ws`
2. Implement ConnectionManager (user → connections map)
3. Implement WebSocket authentication
4. Implement event handler (routing incoming events)
5. Implement `message.created` broadcast (on REST message creation)
6. Implement `connection.ready` event
7. Frontend: WebSocket hook with auto-reconnect
8. Frontend: Integrate WebSocket events into message list
9. Frontend: Integrate WebSocket events into conversation list
10. Frontend: Connection status indicator
11. Tests: `test_websocket.py`

**Output:** Messages appear in real-time for online recipients.

---

### Phase 7: Message States & Receipts (~2 hours)

**Objective:** Full message lifecycle (SENT → DELIVERED → READ).

**Tasks:**
1. Create receipts on message send (status: SENT)
2. Implement delivery acknowledgment (client → server on receive)
3. Implement `POST /messages/{id}/read` (mark read, update watermark)
4. Implement `message.delivered` event broadcast
5. Implement `message.read` event broadcast
6. Frontend: Receipt indicators (✓ sent, ✓✓ delivered, ✓✓ blue for read)
7. Frontend: Auto-mark-read when conversation is open and visible
8. Tests: receipt state transitions

**Output:** Full receipt lifecycle visible in UI.

---

### Phase 8: Typing Indicators (~1 hour)

**Objective:** Real-time typing indicators.

**Tasks:**
1. Implement `typing.started` / `typing.stopped` WebSocket events (server relay)
2. Frontend: Send typing events on input (debounced, throttled)
3. Frontend: Display typing indicator in chat
4. Frontend: Auto-stop typing after timeout

**Output:** "Alice is typing..." appears for other participants.

---

### Phase 9: Group Features (~2 hours)

**Objective:** Full group conversation functionality.

**Tasks:**
1. Implement `POST /conversations/{id}/members` (admin add)
2. Implement `DELETE /conversations/{id}/members/{user_id}` (admin remove)
3. Implement `PATCH /conversations/{id}/members/{user_id}` (role change)
4. Implement `PATCH /conversations/{id}` (group name/avatar)
5. System messages for group events
6. Frontend: Create group modal
7. Frontend: Group info panel (member list, admin controls)
8. Frontend: Add/remove member UI
9. Frontend: System message rendering
10. WebSocket: participant events
11. Tests: `test_groups.py`

**Output:** Full group management with admin controls.

---

### Phase 10: UI Fidelity (~3 hours)

**Objective:** Signal Desktop look and feel.

**Tasks:**
1. Define design system (colors, typography, spacing, shadows)
2. Refine conversation sidebar (density, hover states, selection)
3. Refine message bubbles (Signal-style shapes, spacing, grouping)
4. Refine composer (Signal-style input area)
5. Refine chat header (contact info, group members)
6. Polish modals (create group, add contact, profile)
7. Empty states (no conversation selected, no messages)
8. Loading states (skeleton, spinners)
9. Error states and toasts
10. Avatar component (initials fallback, color generation)
11. Presence indicators (online dot)

**Output:** Application looks and feels like Signal Desktop.

---

### Phase 11: Quality Hardening (~2 hours)

**Objective:** Confidence in correctness.

**Tasks:**
1. Run all backend tests, fix failures
2. Run ESLint + Prettier, fix issues
3. Run Ruff, fix issues
4. TypeScript strict check
5. E2E Playwright test for critical flow
6. Adversarial review (auth, authorization, data consistency)
7. Fix CRITICAL/HIGH findings
8. Database constraint review

**Output:** Clean test suite, no critical bugs.

---

### Phase 12: Seed Data (~1 hour)

**Objective:** Application looks populated on first load.

**Tasks:**
1. Create seed script with deterministic data
2. Users: Alice, Bob, Charlie, David, Eve, Frank (6 users)
3. Contacts: Mutual contacts between several users
4. Direct conversations: 3+ with message history
5. Group conversations: 2+ with varied membership/roles
6. Messages: 50+ across conversations, varied timestamps
7. Receipts: Mix of SENT, DELIVERED, READ states
8. Unread messages for demo effect

**Output:** `python -m app.seed` populates a rich demo dataset.

---

### Phase 13: Deployment (~2 hours)

**Objective:** Live application accessible on the internet.

**Tasks:**
1. Deploy backend to Railway/Render
2. Configure persistent volume for SQLite
3. Run migrations + seed on deployed backend
4. Deploy frontend to Vercel
5. Configure environment variables
6. Configure CORS for production
7. Verify all features against deployed environment
8. Fix deployment-specific issues

**Output:** Working URLs for frontend and backend.

---

### Phase 14: Documentation (~1 hour)

**Objective:** Complete, reviewer-ready documentation.

**Tasks:**
1. Write comprehensive README.md
2. Finalize all spec documents
3. Create INTERVIEW_PREP.md
4. Update requirements traceability (status column)
5. Screenshots in README

**Output:** Repository ready for evaluation.

---

## Total Estimated Time: ~24-25 hours

| Phase | Hours |
|-------|-------|
| 0. Specification | 1-2 |
| 1. Foundation | 2 |
| 2. Authentication | 2 |
| 3. Users & Contacts | 1.5 |
| 4. Conversations | 2 |
| 5. Persistent Messaging | 2 |
| 6. WebSocket Real-Time | 3 |
| 7. Message States | 2 |
| 8. Typing Indicators | 1 |
| 9. Group Features | 2 |
| 10. UI Fidelity | 3 |
| 11. Quality Hardening | 2 |
| 12. Seed Data | 1 |
| 13. Deployment | 2 |
| 14. Documentation | 1 |
| **Total** | **~26.5** |

Buffer: ~2.5 hours for unexpected issues.

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| SQLite concurrency under WebSocket load | HIGH | WAL mode, async driver, single-writer discipline |
| WebSocket reconnection edge cases | MEDIUM | Robust client reconnect + REST data refresh on connect |
| Next.js + WebSocket integration complexity | MEDIUM | Keep WS logic in client-side hooks, not server components |
| Deployment platform SQLite persistence | HIGH | Validate persistence BEFORE building full app |
| Time overrun on UI polish | MEDIUM | Time-box Phase 10, prioritize core interactions |
| Cookie cross-origin issues in deployment | MEDIUM | Test early, consider token-in-body fallback |
