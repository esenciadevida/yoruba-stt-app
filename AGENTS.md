# AGENTS.md

## Overview
Bámi-Sọ̀rọ̀ — Yoruba Speech-to-Text app. FastAPI backend, Next.js 14 frontend. Backend deployed on Render (Python runtime); frontend on Vercel and Render.

## Repository Structure
```
.
├── backend/              # FastAPI backend
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── requirements-host.txt   # Minimal deps for Render free tier (no torch/transformers)
│   ├── requirements.txt        # Full deps including local model fallbacks
│   └── Dockerfile
├── frontend/             # Next.js 14 frontend
│   ├── package.json
│   ├── eslint.config.mjs
│   └── tsconfig.json
├── render.yaml           # Render service definitions (bami-soro-backend, bami-soro-frontend)
├── vercel.json           # Vercel deployment config
└── skills-lock.json      # Neon agent-skill references
```

## Build & Run

### Backend (local)
```bash
cd backend
pip install -r requirements-host.txt   # or requirements.txt for local models
uvicorn main:app --reload
```

### Frontend (local)
```bash
cd frontend
npm install
npm run dev
```

## Lint & Type Check

### Frontend (Next.js)
```bash
cd frontend
npx eslint .                 # lint
npx tsc --noEmit             # typecheck
```

### Backend
No linter configured. Typecheck via Python syntax:
```bash
cd backend
python -m py_compile main.py  # basic syntax check
```

## Deploy
- Backend: `render.yaml` defines a Python service with gunicorn start command
- Frontend: Vercel auto-deploys on push to `master`; also mirrored on Render via `render.yaml`

## Important Notes
- asyncpg `DATABASE_URL` must NOT include `sslmode=require` (asyncpg uses SSL by default and doesn't accept this param)
- `psycopg2` (sync) connection string for Render should include `sslmode=require`
- Start command must use `sh -c 'exec ...'` wrapper to properly expand `$PORT` in Render
