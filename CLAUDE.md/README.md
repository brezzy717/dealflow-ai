## DealFlow AI Build Scaffolding

### Repository Overview
- `apps/backend` — FastAPI service skeleton with health endpoint, configuration, and tests.
- `apps/frontend` — Next.js dashboard starter wired for React Query and API integration.
- `apps/worker` — Redis/RQ worker entry point for async automation.
- `configs`, `infrastructure`, `scripts`, `docs`, `tests` — shared settings, local stack, helpers, reference material, and integration test placeholders.

### Backend Setup
- From the repo root: `cd apps/backend && python3 -m venv .venv && source .venv/bin/activate`.
- Install dependencies: `pip install -e .[dev]`.
- Copy environment template: `cp ../../configs/env/backend.env.example ../../configs/env/backend.env`.
- Run the API locally: `uvicorn dealflow_backend.main:app --reload --host 0.0.0.0 --port 8000`.
- Health check lives at `GET http://localhost:8000/health`.

### Frontend Setup
- From the repo root: `cd apps/frontend`.
- Install tooling: `npm install`.
- Copy env template if needed: `cp ../../configs/env/frontend.env.example ../../configs/env/frontend.env`.
- Start the dashboard: `npm run dev` (defaults to `http://localhost:3000`).
- Update `NEXT_PUBLIC_API_BASE_URL` in `.env.local` or `frontend.env` to point at the backend (e.g., `http://localhost:8000`).

### Worker Setup
- From the repo root: `cd apps/worker && python3 -m venv .venv && source .venv/bin/activate`.
- Install dependencies: `pip install -e .[dev]`.
- Copy env template: `cp ../../configs/env/worker.env.example ../../configs/env/worker.env`.
- Start Redis locally (via Docker or `redis-server`) and launch the worker: `python -m dealflow_worker.main`.

### Local Stack via Docker
- Navigate to `infrastructure/docker`.
- Ensure Docker Desktop is running.
- Bring up the stack: `docker compose up --build`.
- Services exposed: backend `:8000`, frontend `:3000`, Postgres `:5432`, Redis `:6379`.
- Tear down when finished: `docker compose down --volumes` (removes containers and database volume).

### Next Implementation Targets
- Flesh out backend domain modules (`core/`, `models/`) with actual services and schema.
- Build frontend data hooks and UI components to consume live API endpoints.
- Add worker task definitions and schedule orchestration for ingestion/scoring.
- Expand integration tests under `tests/integration` once service contracts stabilize.
