# Scheduled jobs (cron cadence)

The platform's recurring work is triggered by an external scheduler (Vercel Cron
or Google Cloud Scheduler) issuing authenticated `POST` requests to the admin job
endpoint. The in-process job logic lives in
`apps/backend/src/dealflow_backend/services/scheduling.py` (`CADENCE`, `JOBS`).

| Job | Cron (UTC) | Endpoint | Purpose |
|-----|------------|----------|---------|
| `refresh` | `0 10 * * 1,3,5` | `POST /api/admin/jobs/refresh` | Mon/Wed/Fri 10:00 — ingest + rescore from sources |
| `assign` | `0 6 * * 2` | `POST /api/admin/jobs/assign` | Tue 06:00 — action-gated weekly lead drop (10/10/10) |
| `outreach` | `0 12 * * 2,5` | `POST /api/admin/jobs/outreach` | Tue/Fri 12:00 — Day-0 emails + AI concierge calls |
| `retrain` | `0 3 * * 1` | `POST /api/admin/jobs/retrain` | Mon 03:00 — feedback-driven retrain |

The endpoint requires the `admin` role claim. The scheduler must present an admin
service token. Only the initial ingestion is manual; everything else runs here.

## Vercel Cron (`vercel.json`)

`vercel.json` defines the schedules; each cron path is a Vercel route that proxies
to the backend job endpoint with the admin service token attached server-side.
Vercel Cron only triggers — the heavy work runs in the FastAPI/Cloud Run backend.
