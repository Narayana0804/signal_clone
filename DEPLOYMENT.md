# DEPLOYMENT.md — Signal Clone

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Vercel         │         │  Railway/Render  │
│   (Frontend)     │────────►│  (Backend)       │
│   Next.js SSR    │  REST   │  FastAPI+Uvicorn │
│                  │◄────────│                  │
│                  │   WS    │  SQLite (disk)   │
└─────────────────┘         └─────────────────┘
```

## Deployment Targets

### Frontend: Vercel
- **Why:** Native Next.js support, zero-config deployment, free tier sufficient
- **Build:** `next build`
- **Environment Variables:**
  - `NEXT_PUBLIC_API_URL`: Backend REST API URL
  - `NEXT_PUBLIC_WS_URL`: Backend WebSocket URL

### Backend: Railway (Primary) or Render
- **Why:** Persistent filesystem for SQLite, supports long-running processes (WebSocket), affordable
- **Requirement:** Persistent disk/volume for SQLite database file
- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:**
  - `DATABASE_URL`: `sqlite+aiosqlite:///./data/signal.db`
  - `SECRET_KEY`: Random 32+ character string
  - `CORS_ORIGINS`: Frontend URL (comma-separated if multiple)
  - `ENVIRONMENT`: `production`

### SQLite Persistence Concern
- **Railway:** Supports persistent volumes. Mount at `/data/`. SQLite file at `/data/signal.db`.
- **Render:** Supports persistent disks on paid plans. Mount at `/data/`.
- **Fly.io:** Alternative. Supports persistent volumes.
- **CRITICAL:** Verify that the chosen platform does NOT use ephemeral filesystems for the backend. SQLite must survive restarts.

## Environment Variables

### `.env.example`
```env
# Backend
DATABASE_URL=sqlite+aiosqlite:///./data/signal.db
SECRET_KEY=change-me-to-a-random-secret-key
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
python -m app.seed          # Seed demo data
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                 # Starts on port 3000
```

## Production Build

### Backend
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m app.seed          # Optional: seed demo data
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Frontend
```bash
cd frontend
npm install
npm run build
npm start                   # or deploy to Vercel
```

## Health Check

```
GET /health
```

Returns `200` with `{"status": "healthy", "database": "connected"}` when operational.

Configure platform health checks to poll this endpoint.

## CORS & Cross-Site Cookie Configuration

### Production Architecture
- **Frontend**: Vercel (`https://<frontend-app>.vercel.app`)
- **Backend**: Railway (`https://<backend-app>.up.railway.app`)

Because the frontend and backend reside on different root domains (`vercel.app` vs `up.railway.app`), requests sent from the browser are classified as **cross-site**.

### Required Production Cookie Settings
To allow modern browsers (Chrome, Safari, Firefox) to accept and attach HTTP-only session cookies across different domains:

1. **`ENVIRONMENT=production`** environment variable must be set on Railway.
2. The session cookie is issued with:
   - `SameSite=None` (allows cross-site cookie transmission)
   - `Secure=True` (mandatory when `SameSite=None`; requires HTTPS)
   - `HttpOnly=True` (protects cookie from JavaScript access)
3. **CORS Configuration**:
   - `CORS_ORIGINS=https://<frontend-app>.vercel.app` (must match frontend origin exactly, no wildcards)
   - `allow_credentials=True` (required for browser to send/receive cookies)

### Development Cookie Settings
In local development (`http://localhost:3000` to `http://localhost:8000`):
- `ENVIRONMENT=development`
- `SameSite=Lax` and `Secure=False` are used because browsers block `SameSite=None` on unencrypted HTTP.

## Deployment Checklist

- [ ] Backend deployed with persistent volume
- [ ] SQLite database initialized (migrations run)
- [ ] Seed data applied
- [ ] Frontend deployed with correct API/WS URLs
- [ ] CORS configured for frontend domain
- [ ] Health endpoint responding
- [ ] WebSocket connections working
- [ ] Session cookies working cross-origin (SameSite, Secure flags)
- [ ] No secrets in source code
- [ ] `.env` not committed to git

## Known Deployment Limitations

1. **Single-server:** No horizontal scaling. WebSocket connections are in-memory on one process.
2. **SQLite:** No concurrent write scaling. Acceptable for assignment scope.
3. **WebSocket on Vercel:** Vercel does not support WebSocket on the frontend side. The frontend connects to the backend's WebSocket directly — this is fine.
4. **Cold starts:** Some platforms may have cold start delays. Not a concern for evaluation.
