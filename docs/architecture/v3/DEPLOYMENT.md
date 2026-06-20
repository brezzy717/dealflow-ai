# DealFlow AI — Deployment Guide

Maps the modernized stack (MASTER_BUILD_SPEC §11) to concrete services.

## Topology

| Component | Service | Notes |
|---|---|---|
| Frontend | **Vercel** (Next.js) | `apps/frontend`; set `NEXT_PUBLIC_API_BASE_URL` to the API URL. Vercel Cron (`infrastructure/cron/vercel.json`) triggers jobs. |
| API + ML | **Google Cloud Run** (container) | `infrastructure/docker/backend.Dockerfile`; scales to zero; runs the FastAPI app + scoring/ingestion packages. Start on Render/Railway if simpler. |
| Worker / jobs | Cloud Run Job or the worker container | Long-running ingest/score/retrain; triggered by the scheduler. |
| Database | **Supabase** (Postgres 15) | Apply `apps/backend/migrations` via `alembic upgrade head`. RLS is enabled by the initial migration. Alternative: Neon. |
| Object storage | Supabase Storage (or GCS/S3) | Documents, PDFs, call recordings, voice notes, model artifacts. |
| Auth | **Clerk** | Set `CLERK_JWKS_URL`, `CLERK_ISSUER` (and `CLERK_AUDIENCE`). Required in production. |
| Scheduling | Vercel Cron / Cloud Scheduler → admin job endpoints | See `infrastructure/cron/README.md`. |

## Required environment (backend)

| Var | Purpose |
|---|---|
| `ENVIRONMENT=production` | enables fail-fast guards |
| `DATABASE_URL` | Supabase/Neon Postgres (asyncpg DSN) — required in prod |
| `CLERK_JWKS_URL`, `CLERK_ISSUER` | auth — required in prod |
| `CORS_ALLOW_ORIGINS` | the Vercel frontend origin |
| `MODEL_ARTIFACTS_DIR` | model artifact location (object storage mount) |
| `BILLING_WEBHOOK_SECRET` | billing webhook verification |

## Cross-tenant jobs + RLS

Tenant tables enforce FORCE Row-Level Security. Per-request reads set
`app.current_tenant` from the JWT. System/admin jobs (retrain, assignment,
clawback, purge) run cross-tenant and must use a **BYPASSRLS** database role.

## Privacy

Account close purges a tenant's PII via cascade while retaining anonymized
training samples (`retained_training_samples`). Encryption in transit/at rest is
provided by the managed platforms (Supabase/Cloud Run/Vercel TLS).

## Deploy steps (first cut)

1. Provision Supabase; run `alembic upgrade head` against it.
2. Deploy the backend container to Cloud Run with the env above.
3. Deploy the frontend to Vercel; point `NEXT_PUBLIC_API_BASE_URL` at Cloud Run.
4. Configure Clerk and set the JWKS/issuer envs.
5. Wire Vercel Cron (or Cloud Scheduler) to the `/api/admin/jobs/*` endpoints
   with an admin service token.
6. Add Stripe + the live email/voice/booking adapters as keys become available.
