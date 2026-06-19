# CLAUDE.md

Guidance for working in this repository.

## What this is

DealFlow AI — an off-market deal-sourcing platform for business brokers. It ingests
multi-source business data, scores leads with a 3-model ML ensemble, assigns scored
prospects to brokers, and runs an automated outreach + feedback loop. See
`docs/architecture/v3/MASTER_BUILD_SPEC.md` for the authoritative spec and
`docs/DEVELOPMENT.md` for local setup.

## Monorepo layout

- `apps/backend` — FastAPI service (Python). Source under `src/dealflow_backend`.
- `apps/worker` — background worker entry point.
- `apps/frontend` — Next.js + React Query dashboard (Pages Router, Tailwind CSS).
- `services/` — domain libraries: `data_ingestion`, `scoring_engine`, `workflow_automation`.
- `configs/`, `infrastructure/`, `scripts/`, `docs/` — shared config, local stack, helpers, docs.

## Common commands

Backend (from `apps/backend`):
- Install: `pip install -e .[dev]`
- Test: `pytest`
- Lint/type: `ruff check src && mypy src`
- Run: `uvicorn dealflow_backend.main:app --reload`

Frontend (from `apps/frontend`):
- Install: `npm install`
- Build: `npm run build`
- Lint: `npm run lint`

Worker (from `apps/worker`): `pip install -e .[dev]` then `python -m dealflow_worker.main`.

Local stack: `docker compose -f infrastructure/docker/docker-compose.yml up --build`.

## Conventions

- Backend config comes from `Settings` in `dealflow_backend/config.py` (env-driven). Never hardcode
  secrets; `DATABASE_URL` is required in production.
- Keep the service boundary: API handlers depend on services in `dealflow_backend/services/`.
- Frontend styling uses Tailwind utility classes; global styles live in `src/styles/globals.css`.
- Do not commit secrets, `.env` files, build artifacts, or OS cruft (see `.gitignore`).
