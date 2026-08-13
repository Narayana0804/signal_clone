# TEST_PLAN.md — Signal Clone

## Testing Strategy

### Principles
1. Test **business-critical logic** — not boilerplate
2. Backend tests are highest priority — they guard data integrity and authorization
3. E2E tests validate critical user flows — not every UI element
4. Do not over-test — time is constrained to ~29 hours total

### Test Pyramid

```
        ┌──────────┐
        │   E2E    │   ← Playwright (3-5 critical flows)
        ├──────────┤
        │  API     │   ← pytest + httpx (core endpoints)
        ├──────────┤
        │ Service  │   ← pytest (business logic, authorization)
        └──────────┘
```

---

## Backend Tests (`backend/tests/`)

### Framework
- `pytest` + `pytest-asyncio`
- `httpx.AsyncClient` for API testing
- In-memory SQLite for test isolation
- Fixtures: test database, test users, test conversations

### Test Modules

#### `test_auth.py`
| Test | Priority |
|------|----------|
| Register new user | P0 |
| Register duplicate phone → 409 | P0 |
| Verify with correct OTP | P0 |
| Verify with wrong OTP → 400 | P0 |
| Login creates session | P0 |
| Login with unknown phone → 404 | P0 |
| GET /me with valid session | P0 |
| GET /me without session → 401 | P0 |
| Logout invalidates session | P0 |

#### `test_contacts.py`
| Test | Priority |
|------|----------|
| List contacts (empty) | P0 |
| Add contact | P0 |
| Add duplicate contact → 409 | P0 |
| Add self as contact → 400 | P0 |
| Delete contact | P0 |
| List contacts after adding | P0 |

#### `test_conversations.py`
| Test | Priority |
|------|----------|
| Create direct conversation | P0 |
| Create duplicate direct → returns existing | P0 |
| Create group conversation | P0 |
| Create group without name → 400 | P0 |
| List conversations ordered by activity | P0 |
| Get conversation detail | P0 |
| Get conversation as non-participant → 403 | P0 |
| Unread count calculation | P0 |
| Last message preview | P0 |

#### `test_messages.py`
| Test | Priority |
|------|----------|
| Send message to conversation | P0 |
| Send message as non-participant → 403 | P0 |
| Retrieve messages paginated | P0 |
| Message creates receipts for other participants | P0 |
| Mark message as read | P0 |
| Read updates watermark and receipts | P0 |

#### `test_groups.py`
| Test | Priority |
|------|----------|
| Add member to group (admin) | P0 |
| Add member to group (non-admin) → 403 | P0 |
| Remove member from group (admin) | P0 |
| Remove last admin → 400 | P0 |
| Change member role (admin) | P0 |
| Change member role (non-admin) → 403 | P0 |
| List group members | P0 |

#### `test_websocket.py`
| Test | Priority |
|------|----------|
| Connect with valid token | P0 |
| Connect with invalid token → close 4001 | P0 |
| Receive message.created event | P0 |
| Send typing.started event | P1 |
| Receive typing indicator | P1 |

---

## Frontend / E2E Tests (`frontend/e2e/`)

### Framework
- Playwright

### Critical Flows

#### Flow 1: Authentication
```
Register → Verify OTP → Login → Verify /me → Refresh → Still logged in → Logout
```

#### Flow 2: Messaging
```
Login as Alice → Open conversation with Bob → Send message → Verify message appears
Login as Bob → Verify message received → Send reply → Alice sees reply
```

#### Flow 3: Group Operations
```
Login as Alice → Create group → Add Bob, Charlie → Send group message
Login as Bob → See group → See message → Reply
Login as Alice → Remove Charlie → Verify member list
```

#### Flow 4: Read Receipts
```
Login as Alice → Send message to Bob
Login as Bob → Open conversation → Message auto-marked read
Verify Alice sees read indicator
```

#### Flow 5: Offline Persistence
```
Login as Alice → Send message to Bob (Bob offline)
Login as Bob → Verify message visible from database
```

---

## Test Execution

### Local
```bash
# Backend
cd backend
pytest -v

# E2E
cd frontend
npx playwright test
```

### Coverage Target
- Not pursuing a specific coverage percentage
- Focus: all authorization checks, all state transitions, all error paths for core endpoints

---

## Test Data

### Fixtures (`conftest.py`)
- `test_db`: Fresh in-memory SQLite per test
- `test_client`: httpx.AsyncClient configured with test app
- `test_user_alice`: Pre-created user Alice
- `test_user_bob`: Pre-created user Bob
- `authenticated_client_alice`: Client with valid session cookie
- `test_conversation`: Direct conversation between Alice and Bob
- `test_group`: Group conversation with Alice (admin) + Bob + Charlie
