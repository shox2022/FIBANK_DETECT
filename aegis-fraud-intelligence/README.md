# AEGIS Fraud Intelligence

AEGIS means Adaptive Engine for Guarded Intelligence & Security.

This repository is being built in controlled phases. Phase 1 contains only the backend foundation: FastAPI app setup, stable SQLite configuration, SQLAlchemy models, automatic table creation, an idempotent seed command, and a health endpoint.

## Phase 1 Backend Setup

```powershell
cd aegis-fraud-intelligence\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

On Linux or macOS, activate the virtual environment with:

```bash
source venv/bin/activate
```

## Phase 1 Verification

The SQLite database is created at:

```text
backend/aegis.sqlite
```

The database path is resolved from the backend directory, so it does not depend on the terminal working directory.

Verify the backend:

- Health endpoint: http://localhost:8000/api/health
- Swagger docs: http://localhost:8000/docs

The seed command is safe to run multiple times:

```powershell
python -m app.seed
```

It upserts demo users and risk rules instead of duplicating them.

## Phase 1 Demo Users

All seeded demo users use the password:

```text
password123
```

| Email | Role |
| --- | --- |
| customer@aegis.test | CUSTOMER |
| analyst@aegis.test | ANALYST |
| admin@aegis.test | ADMIN |

## Phase 5 Frontend Setup

The React frontend expects the FastAPI backend at:

```text
http://localhost:8010
```

To override this, create `frontend/.env` from `frontend/.env.example` and set:

```text
VITE_API_BASE_URL=http://localhost:8010
```

Run the frontend:

```powershell
cd aegis-fraud-intelligence\frontend
npm install
npm run dev
```

Open:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8010
- Swagger docs: http://localhost:8010/docs

Build check:

```powershell
npm run build
```
