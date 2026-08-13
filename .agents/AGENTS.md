# Signal Clone — Agent Rules

## Architecture
- Follow the layered architecture: Router → Schema → Service → Repository → ORM → Database
- Do NOT put business logic in route handlers
- Do NOT put SQL queries in service layer
- WebSocket Manager handles connections; Services handle persistence
- All state mutations must go through the service layer

## Coding Standards

### Backend (Python)
- Python 3.12+
- SQLAlchemy 2.x async syntax (use `select()`, `async_session`)
- Pydantic v2 for all request/response schemas
- Type hints on all function signatures
- Use `ruff` for linting and formatting
- Imports: stdlib → third-party → local (enforced by ruff)

### Frontend (TypeScript/React)
- Next.js App Router
- Strict TypeScript (`strict: true`)
- React functional components only
- Custom hooks for shared logic
- Tailwind CSS for styling — no inline styles, no CSS modules
- Use `lucide-react` for icons
- ESLint + Prettier

## Security
- All endpoints (except /health, /auth/register, /auth/verify, /auth/login) require authentication
- Authorization (conversation membership, admin role) must be enforced server-side
- Never trust client-provided user identity or roles
- Session tokens: HTTP-only cookies for REST, query param for WebSocket
- Validate all inputs with Pydantic
- No secrets in source code

## Database
- SQLite with WAL mode
- UUID primary keys (TEXT in SQLite)
- ISO 8601 timestamps (TEXT in SQLite, UTC)
- Alembic for migrations
- All foreign keys with explicit CASCADE behavior

## Scope Control
- P0 requirements before P1
- P1 before P2 (bonus)
- Do not add dependencies without documenting in DECISIONS.md
- Do not change architecture without human approval

## Testing
- pytest for backend
- Playwright for E2E
- Test authorization and error paths, not just happy paths

## Documentation
- Update spec documents when architecture changes
- Keep README current
- Commit messages: conventional commits format
