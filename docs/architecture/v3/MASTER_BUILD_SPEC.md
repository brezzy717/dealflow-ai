# DealFlow AI — Master Build Spec (v3, Single Source of Truth)

> Status: living document. Consolidates `docs/product/project-scope/*`,
> `docs/ux/dashboard-design/*`, and `docs/architecture/v1|v2/*` into one authoritative
> reference. Where the source docs conflict, this document **resolves** the conflict and
> notes the decision. Supersedes the fragmented v1/v2 specs for build purposes.

---

## 1. Product Overview & Glossary

DealFlow AI (dealflowtech.io) is an off-market deal-sourcing platform for business brokers.
It ingests multi-source business + owner data, scores each business for likelihood-to-sell
with a 3-model ML ensemble, assigns scored prospects to brokers on a slow-drip cadence, and
runs an automated email + AI-call outreach loop whose outcomes feed back into model retraining.

**Lifecycle (authoritative):**
`raw lead` (ingested+enriched) → `scored lead` (ensemble prediction + tier) →
`prospect` (assigned to a broker, shown under Prospects) → `client` (broker manually toggles
after a booked discovery call closes) → `deal` (client enters PipeDeal Kanban) →
`past client` (deal completed, archived under Clients).

**Tiers (RESOLVED CONFLICT).** The source docs disagree: some describe 3 tiers
(Green/Yellow/Red) with point bands 75–100 / 50–74 / 25–49 / <25, others list 4 tiers
including "Black <40" and a "Monitor <25". **Decision for build:** ship **4 tiers** on a
0–100 scale, but assignment and the dashboard surface the **top 3** (Green/Yellow/Red); the
4th tier is a low/"Monitor" bucket that is scored, stored, and re-scored but **not** dropped to
brokers until it crosses into Red. Canonical bands:

| Tier | Band | Dropped to brokers? |
|---|---|---|
| 🟢 Green | 75–100 | Yes (10/week) |
| 🟡 Yellow | 50–74 | Yes (10/week) |
| 🔴 Red | 25–49 | Yes (10/week) |
| ⚪ Monitor | 0–24 | No — re-scored, promoted when signals rise |

(If you want the literal "Black" label instead of "Monitor" for the bottom bucket, it's a
rename only — bands and behavior are unchanged.)

---

## 2. Data Model (Neon/Supabase Postgres)

Sixteen core tables. All tables carry `id` (uuid pk), `created_at`, `updated_at` (UTC), and —
where tenant-scoped — a `tenant_id` fk with Row-Level Security. Prediction/outcome rows are
immutable + timestamped for audit.

1. `tenants` — subscriber/broker accounts (billing, status, licensing_state, settings).
2. `raw_leads` — complete business + owner record from all sources (business identity, address,
   APN, owner identity/contact, NAICS/industry, employees, revenue, years_in_business, raw
   source payloads, dedup key).
3. `data_source_enrichment` — per-lead provenance: which source/dataset supplied which field,
   pulled_at, confidence.
4. `ensemble_predictions` — per-lead, per-run: ensemble score, tier, confidence, prediction
   variance, individual model scores, top-5 positive / top-5 negative feature attributions,
   plain-English explanation, model_version_ids, scored_at (immutable, append-only).
5. `model_versions` — registry: model_name (xgboost_v1/random_forest_v1/neural_net_v1), artifact
   uri, training_run, metrics, active flag.
6. `ensemble_weights` — adaptive per-model weights with effective_from timestamp + rationale.
7. `lead_assignments` — territory-protected ownership: lead_id, tenant_id, assigned_at, tier,
   status (prospect/client/past_client), clawback fields. **Permanent** once assigned.
8. `broker_calendars` — Cal.com / OAuth calendar linkage + sync metadata.
9. `lead_email_outreach` — per-prospect email sends, opens, replies, booking-link clicks.
10. `ai_call_queue` — scheduled calls (prospect_id, scheduled_window, attempt_no, status).
11. `ai_call_outcomes` — per-attempt: outcome (booked/dnc/interested_future/no_contact),
    reason, callback_at, recording_uri, transcript_uri, actor (concierge/broker).
12. `appointments` — bookings (source: AI/manual/self-serve link), Cal.com event ref.
13. `deal_outcomes` — closed/lost: predicted_score, actual_outcome, actual_quality_score,
    prediction_error, free-text loss reason, timestamps (feeds the feedback loop).
14. `document_vault` — broker docs + templates + outreach PDFs (storage uri, type, signed-status).
15. `admin_notifications` — system alerts / error feed for the admin dashboard.
16. `whatsapp_conversations` — support chat history.

Plus supporting tables introduced during build: `broker_parameters` (assignment gating:
years_in_business, employees, revenue_millions, omitted_industries, omitted_cities_zips),
`tasks`, `notes`/`voice_notes`, `deal_rooms` + `deal_room_messages`, `audit_log`.

---

## 3. ML Scoring Engine

**Models:** XGBoost (`xgboost_v1`), Random Forest (`random_forest_v1`), PyTorch MLP
(`neural_net_v1`, with StandardScaler). Output = adaptive **weighted average** + **confidence**
(model agreement) + **prediction variance** + **drift score** (divergence between models).

**Feature catalog (RESOLVED CONFLICT).** The spec lists "52 features" but the two enumerations
differ (e.g. one includes `balloon_critical`, the other `permit_recency` in its place; one omits
a feature to reach 52). **Decision:** maintain the canonical 52-feature list in code as
`FEATURE_KEYS` in `services/scoring_engine/feature_store/`, treated as the single source; the
build reconciles the two doc lists there and documents each feature's source + transform. Groups:
Financial/Business (14), Owner Life Events (6), Personal Financial Distress (6), Online Sentiment
(10), Market Dynamics (6), Social Media (5), Composite Scores (4), Search Intent (1).

**Two scoring layers:** (a) the deterministic 100-point rules grid in the spec (pre-foreclosure,
tax distress, etc.) is retained as an **explainability + cold-start baseline**; (b) the ensemble
is the production scorer that **learns** which signal combinations predict conversion. Both are
stored; the ensemble governs tiering.

**Feedback loop (two-stage):** (1) prospect → booked appointment; (2) booked → signed deal /
lost-with-reason. Each action is captured immediately and used for periodic retraining; weights
adapt on recent performance; drift detection guards rollback. All predictions are date/time
stamped and never mutated (new run = new row).

---

## 4. Data Ingestion

**Sources:** Dewey Data (primary; ATTOM pre-foreclosure/tax/assessor/recorder, Builty permits,
People Data Labs, SafeGraph/Advan foot traffic, BrightQuery, WageScape, etc.), Yelp, NASDAQ,
SEC/EDGAR, Data.gov. (D&B PAYDEX referenced in the rules grid — "when added".)

**Workflow:** pull business list (initial focus: AZ, then UT, TX) → enrich per source →
dedup (business name + address) → validate/normalize types, default missing → upsert `raw_leads`
+ `data_source_enrichment` → trigger scoring. **Cadence:** ingestion Mon/Wed/Fri 10:00; rescoring
on new signals (cold leads can go hot). Only the **initial** ingestion is manual; everything else
is automated.

---

## 5. Assignment Engine

- Match scored leads against each broker's `broker_parameters` (years_in_business, employees,
  revenue_millions, omitted_industries, omitted_cities/zips in licensing state).
- **Slow-drip round-robin:** 30 leads/week/broker = 10 Green + 10 Yellow + 10 Red (120/month).
- **Color-block fallback:** short on a color → pull from the next block down (Green→Yellow→Red).
- Non-matching leads return to the pool for the next broker; leftovers roll to next week.
- **Permanent ownership:** once assigned, a lead is that broker's for life. The **only** clawback
  is broker departure **before** first contact → lead re-enters the pool. Admin can override/claw
  back misassignments from the Admin dashboard.
- Assignment runs **Tuesday 06:00**, no exceptions. A broker with unactioned prospects past the
  grace window does **not** receive the next drop.

---

## 6. Outreach Automation & AI Calling Concierge

Opt-in per broker at onboarding (toggle later in Settings). If opted out, the broker must log
outcomes themselves. Cadence (RESOLVED CONFLICT — the source doc gives two different call-day
sequences):

- **Day 0 — Tue 06:00:** prospects land under Prospects; automated email goes out with 2 value
  PDFs + self-serve Cal.com booking link.
- **Day 7 — Tue 11:00–13:00:** first call. AI scans inbox for replies + calendar for bookings,
  omits anyone already engaged, then calls the rest. Goal: book a 30-min discovery call on the
  broker's calendar.
- **Day 10 — Fri 11:00–13:00:** second call if still no contact. If still no contact → mark
  `no_contact`, schedule follow-up sequence in **60 days**.

**Decision:** canonical sequence is Day 0 email → Day 7 (Tue) call → Day 10 (Fri) call →
60-day re-sequence. (The "second call 3 days later on Friday" phrasing in the prose is the same
Day 7→Day 10 gap; we standardize on it.)

**Outcome codes (must be logged identically by AI concierge or broker):** `booked`,
`dnc` (deactivate + remove from calling list), `interested_future` (capture callback timeframe;
default +60 days if none), `no_contact` (callback +3 days first cycle). Every call recorded +
transcribed + attached to the prospect/client. Every action feeds the feedback loop. A prospect
is only deactivated on explicit DNC.

---

## 7. Dashboard (Broker)

Left vertical nav; floating **Aria** Deal-Assist widget (bottom-left, universal) + floating
mic/voice-record widget (universal). Tabs:

- **Home** — top row of metrics/charts (YTD commissions, closing rate, prospect→appt→close
  conversion); below: upcoming appointments, tasks due, this week's prospects, walkthrough launcher.
- **Prospects** — list of assigned scored leads (business name, employees, ARR, years, industry);
  expand for full scoring rationale; right-side **Google Maps heat map** with color-coded pins
  (carousel quick-view); embedded **Brave Search** bar. Mandatory fields vs optional defined in
  spec §Prospects.
- **Appointments** — week view + 30-day calendar + expandable list; import from broker calendars;
  Cal.com self-hosted.
- **My Clients** — current + past clients; CSV/Excel/Google-Sheet upload + API/webhook CRM import;
  full export; everything attaches as client assets.
- **Deal Room** — realtime multi-party chat (broker/buyer/seller + invited notary/underwriter/CPA),
  secure doc exchange + one-click attach to client, e-signature (DocuSign/Adobe), push
  notifications, SOC 2 / valid e-sign posture.
- **PipeDeal** — Kanban (Phase 1 Buyer Matching → 2 LOI/NDA → 3 Due Diligence → 4 Negotiation →
  5 Docs Signed/Underwriting → 6 Funded). On "closed/complete" the client moves to Clients tab
  with all assets archived.
- **AI Calling Concierge** — warm-outreach control + status.
- **Task Manager** — outstanding actions; to-do list; notebook + voice notes (attach to
  client/prospect/task/appointment); Aria's hub (read/write, web search, email/SMS draft+send,
  Deal Room, docs, calendar).
- **Vault** — branded templates (NDA, rep agreement, LOI) + uploads + outreach PDFs.
- **Reports** — granular drill-down (conversion, commissions, sector/region, channel) feeding
  Home metrics + the feedback loop.
- **Settings** — outreach toggle, assignment parameters, account close/export/import, how-to
  videos, WhatsApp help bot, light/dark mode.

**Admin dashboard (separate):** real-time module monitoring, error feed, lead clawback/override,
model + drift dashboards, user management, audit logs, platform health.

---

## 8. Integrations

Clerk (auth/onboarding), Stripe (billing), Cal.com (self-hosted booking), Hume AI voice agent +
Twilio (Re-tell fallback) for calls, DocuSign/Adobe Sign (e-signature), Brave Search API,
Google Maps API, WhatsApp (support bot). Email provider for outreach (TBD: Resend/SendGrid).

---

## 9. Security, Privacy & Compliance (first-class)

Handles sensitive PII (owner financials, bankruptcies, liens, life events, call recordings).
Requirements: encryption in transit + at rest; RLS tenant isolation; full audit trail (who
accessed which prospect/deal); broker data **purge-on-exit** (retain only anonymized ML-training
signals); Deal Room targets SOC 2 + valid electronic-signature compliance; secrets via env/secret
manager (never committed); least-privilege API keys per integration.

---

## 10. API Surface

REST/JSON for all core objects (leads/prospects, assignments, appointments, outcomes, documents,
reports) plus webhooks for CRM push/pull and bulk import/export (CSV, Excel, JSON). All
automation flows exposed as endpoints so cron/workflow triggers and the dashboard share one API.

---

## 11. Deployment Architecture (modernized; supersedes v1/v2 infra)

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router target) on **Vercel** |
| Data/storage/realtime | **Supabase** (Postgres 15 + pgvector + Storage + Realtime + RLS); **Neon** is the alternative if Clerk-only auth is preferred |
| Auth | **Clerk** (Supabase JWT integration) |
| API + ML | Containerized **FastAPI on Google Cloud Run** (Render/Railway to start) |
| Scheduling/workflows | **Inngest** durable workflows (or Cloud Scheduler + Cloud Run Jobs); Vercel Cron as lightweight trigger |
| Model artifacts | joblib in object storage + `model_versions`; MLflow later |

The AWS Terraform + Kubernetes + Redis/RQ scaffold from the original build was removed as
misaligned. Docker is retained for local development and Cloud Run images.

---

## 12. Build Roadmap (phased)

0. **Cleanup pass (done):** fix broken backend import, worker logging, frontend Tailwind/lint,
   secrets posture, `.gitignore`/hygiene, CI, infra realignment, author this spec.
1. **Foundations:** schema + migrations for all tables (RLS/tenancy), Clerk auth end-to-end, CI green.
2. **Vertical thin-slice:** one source → `raw_leads` → subset features → real-but-simple ensemble
   → `ensemble_predictions` (tier + explanation) → assignment → Prospects tab renders it.
3. **ML depth:** full 52 features, training pipeline, versioning/drift, two-stage feedback retrain.
4. **Ingestion breadth:** all sources, dedup/validation, cron/workflow cadence + rescoring.
5. **Outreach automation:** email + Cal.com + Hume/Twilio + recording/transcription + outcomes.
6. **Dashboard breadth:** Home, Appointments, Clients, Tasks/voice/Aria, Reports, Settings, Vault.
7. **Deal Room + Pipeline:** realtime chat + e-sign + Kanban + vault + push + compliance.
8. **Admin dashboard:** monitoring, error feed, clawback, model/drift, users, audit.
9. **Commercialize:** Stripe, onboarding, WhatsApp help, hardening, compliance, scale.
