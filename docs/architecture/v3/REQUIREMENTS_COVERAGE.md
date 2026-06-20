# DealFlow AI — Requirements Coverage Ledger

> The guard against "thin slices losing requirements." Every capability in
> `MASTER_BUILD_SPEC.md` is listed here with a status and the phase that owns it.
> A vertical slice may implement a *narrow* path through a row (e.g. one data
> source) — but the row stays open until the full requirement is met. Update this
> file in the same PR as the code it tracks.
>
> Status legend: ✅ done · 🟦 partial (slice) · ⬜ not started

## Legend of "partial"
A 🟦 row means a working path exists but the requirement is not fully met. The
"Gap / remaining" column states exactly what is still owed so it cannot be lost.

---

## 1. Data ingestion (spec §4)

| # | Requirement | Status | Phase | Gap / remaining |
|---|---|---|---|---|
| 1.1 | Pluggable pipeline base (fetch/transform/load) | ✅ | 0 | — |
| 1.2 | Synthetic/seed source for end-to-end dev | 🟦 | 2 | real connectors below replace it |
| 1.3 | Dewey Data connector (ATTOM, Builty, PDL, SafeGraph, BrightQuery, WageScape…) | 🟦 | 4 | signal mapper built/tested; live API key + endpoint/field verification owed |
| 1.4 | Yelp connector | 🟦 | 4 | mapper built/tested; live API wiring owed |
| 1.5 | NASDAQ connector | 🟦 | 4 | mapper built/tested; live API wiring owed |
| 1.6 | SEC/EDGAR connector | 🟦 | 4 | mapper built/tested; live API wiring owed |
| 1.7 | Data.gov connector | 🟦 | 4 | mapper built/tested; live API wiring owed |
| 1.8 | Dedup (business name + address) | ✅ | 4 | normalized name + address dedup_key |
| 1.9 | Missing-data defaults + type validation | 🟦 | 2 | extraction defaults; full validation owed |
| 1.10 | 2–3×/week scheduled ingest + event rescoring | 🟦 | 4 | cadence + refresh job + endpoint; external scheduler + event-driven rescore owed |

## 2. ML scoring engine (spec §3)

| # | Requirement | Status | Phase | Gap / remaining |
|---|---|---|---|---|
| 2.1 | Canonical 52-feature catalog (`FEATURE_KEYS`) | ✅ | 2 | — |
| 2.2 | Feature extraction from a lead | 🟦 | 2 | derivations for ~core features; rest defaulted |
| 2.3 | 3-model ensemble (XGBoost, RandomForest, MLP+scaler) | 🟦 | 2 | trained on synthetic data; real training set owed |
| 2.4 | Weighted average + confidence + variance | ✅ | 2 | — |
| 2.5 | Tier assignment (Green/Yellow/Red/Monitor) | ✅ | 2 | — |
| 2.6 | Feature attribution (top 5 ±) | 🟦 | 2 | importance×value heuristic; SHAP owed |
| 2.7 | Plain-English explanation | 🟦 | 2 | template-based; richer NL owed |
| 2.8 | Persist `ensemble_predictions` (timestamped, append-only) | 🟦 | 2 | written by orchestrator |
| 2.9 | Model versioning (`model_versions`) | 🟦 | 3 | rows + joblib artifacts; object-storage URIs owed |
| 2.10 | Adaptive ensemble weights (`ensemble_weights`) | ✅ | 3 | inverse-error weighting on retrain |
| 2.11 | Drift detection | 🟦 | 3 | perf-drift + model disagreement; population drift owed |
| 2.12 | Two-stage feedback retraining (booked → closed) | 🟦 | 3 | capture + retrain built; scheduling owed (Phase 4) |
| 2.13 | Deterministic 100-point rules grid (explainability baseline) | ⬜ | 3 | — |

## 3. Assignment engine (spec §5)

| # | Requirement | Status | Phase | Gap / remaining |
|---|---|---|---|---|
| 3.1 | Parameter gating (years, employees, revenue, omit industries/locations) | 🟦 | 2 | core filters; full parity owed |
| 3.2 | Round-robin slow-drip (30/wk, 10/10/10) | ✅ | 4 | `assign_weekly` over the scored pool |
| 3.3 | Color-block fallback (short tier → next down) | ✅ | 2 | — |
| 3.4 | Permanent single ownership (unique lead_id) | ✅ | 1 | — |
| 3.5 | Clawback on broker departure pre-contact | 🟦 | 2 | function built; admin trigger Phase 8 |
| 3.6 | Tue 06:00 scheduled assignment | 🟦 | 4 | cadence + assign job + endpoint; external cron trigger owed |
| 3.7 | Action-gating (no action → no next drop) | ✅ | 4 | enforced in `assign_weekly` |

## 4. Outreach automation (spec §6)

| # | Requirement | Status | Phase | Gap / remaining |
|---|---|---|---|---|
| 4.1 | Day-0 email + value PDFs + booking link | 🟦 | 5 | orchestration + EmailProvider; live email API (Resend/SendGrid) + real PDFs owed |
| 4.2 | Cal.com self-hosted booking | 🟦 | 5 | BookingProvider builds links; self-hosted Cal.com instance + sync owed |
| 4.3 | Hume AI calling concierge + Twilio (Re-tell fallback) | 🟦 | 5 | concierge loop + VoiceProvider; live Hume/Twilio adapters owed |
| 4.4 | Call recording + transcription | 🟦 | 5 | CallResult carries recording/transcript URIs; live capture owed |
| 4.5 | Outcome state machine (booked/dnc/interested/no_contact + callbacks) | ✅ | 5 | full cadence: Day7→Day10→60d, DNC deactivate, interested callbacks |
| 4.6 | Opt-in toggle (concierge vs manual) | ✅ | 5 | concierge skips opted-out brokers (manual logging) |

## 5. Dashboard — broker (spec §7)

| # | Requirement | Status | Phase | Gap / remaining |
|---|---|---|---|---|
| 5.1 | Auth + app shell / nav | 🟦 | 6 | sidebar nav shell built; Clerk frontend auth integration owed |
| 5.2 | Prospects list (name, employees, ARR, years, industry) | ✅ | 2 | list + expandable score detail |
| 5.3 | Prospects score rationale (expand) | ✅ | 2 | explanation + top ± drivers |
| 5.4 | Google Maps heat map w/ color pins + carousel | ⬜ | 6 | needs Google Maps API key |
| 5.5 | Brave Search embedded bar | ⬜ | 6 | needs Brave Search API key |
| 5.6 | Home metrics (YTD commissions, conversion) | 🟦 | 6 | metrics API + cards; commission capture owed |
| 5.7 | Appointments (week + 30-day + list) | 🟦 | 6 | list view + API; calendar grid views owed |
| 5.8 | My Clients (+ CSV/Excel/Sheets/CRM import-export) | 🟦 | 6 | list + CSV/JSON export; bulk import + Excel + CRM webhooks owed |
| 5.9 | Task Manager + to-dos | ✅ | 6 | list + create API/UI |
| 5.10 | Notebook + voice notes + attach | ⬜ | 6 | `notes` table exists; audio capture/UI owed |
| 5.11 | Aria assistant (read/write, search, email/SMS, calendar) | 🟦 | 6 | floating widget placeholder; assistant wiring owed |
| 5.12 | Reports (drill-down) | 🟦 | 6 | tier/industry/outcome summary API + UI; deeper drill-down owed |
| 5.13 | Settings (outreach toggle, params, export, videos, WhatsApp, theme) | 🟦 | 9 | outreach toggle + params + onboarding + account-close live; embedded videos + WhatsApp + theme owed |
| 5.14 | Vault (branded templates + PDFs + uploads) | ⬜ | 6 | placeholder; needs document service |

## 6. Deal Room + Pipeline (spec §7)

| # | Requirement | Status | Phase | Gap / remaining |
|---|---|---|---|---|
| 6.1 | Deal Room realtime multi-party chat | 🟦 | 7 | durable messages + API + UI (polled); Supabase Realtime push owed |
| 6.2 | Secure doc exchange + one-click attach | 🟦 | 7 | attach-to-client endpoint; secure storage + exchange owed |
| 6.3 | E-signature (DocuSign/Adobe) | ⬜ | 7 | needs DocuSign/Adobe Sign integration |
| 6.4 | Push notifications | ⬜ | 7 | needs realtime/push channel |
| 6.5 | PipeDeal Kanban (6 stages) | ✅ | 7 | board + stage-transition API/UI |
| 6.6 | Close → archive to Clients | ✅ | 7 | close archives to past-client |

## 7. Admin (spec §7)

| # | Requirement | Status | Phase | Gap / remaining |
|---|---|---|---|---|
| 7.1 | Real-time module monitoring | 🟦 | 8 | health/counts API + admin UI; live realtime feed owed |
| 7.2 | Error feed (`admin_notifications`) | ✅ | 8 | drift alerts written + admin feed API/UI |
| 7.3 | Lead clawback / override UI | ✅ | 8 | admin clawback endpoint re-pools lead + audit |
| 7.4 | Model + drift dashboards | 🟦 | 8 | model registry + metrics API/UI; richer charts owed |
| 7.5 | User management | 🟦 | 8 | admin user list; edit/deactivate actions owed |
| 7.6 | Audit trail (`audit_log`) | 🟦 | 8 | clawback writes + audit API; broaden write coverage owed |

## 8. Cross-cutting (spec §9, §10, §11)

| # | Requirement | Status | Phase | Gap / remaining |
|---|---|---|---|---|
| 8.1 | RLS tenant isolation | ✅ | 1 | policies live; per-request GUC wiring in Phase 2 API |
| 8.2 | Clerk auth (backend verify) | ✅ | 1 | frontend integration Phase 6 |
| 8.3 | Encryption in transit/at rest | 🟦 | 9 | documented (managed platforms provide TLS + at-rest); deploy config owed |
| 8.4 | Data purge-on-exit | ✅ | 9 | account close purges tenant PII, retains anonymized training samples |
| 8.5 | Stripe billing | 🟦 | 9 | subscription status + webhook + state on tenant; live Stripe adapter + checkout owed |
| 8.6 | REST API for all core objects | 🟦 | 2 | health, /me, prospects, feedback, admin/retrain; rest grow per phase |
| 8.7 | CSV/Excel/JSON export + CRM webhooks | 🟦 | 6 | CSV + JSON export endpoint; Excel + bulk import + CRM webhooks owed |
| 8.8 | CI: lint/type/test + migration on PG | ✅ | 1 | — |
| 8.9 | Deployment (Vercel/Supabase/Cloud Run/Inngest) | 🟦 | 9 | Dockerfiles + cron config + DEPLOYMENT.md guide; live provisioning + IaC owed |
