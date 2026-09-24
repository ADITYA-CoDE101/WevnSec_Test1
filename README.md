# WevnSec

Website security assessments and daily domain monitoring.

## Included
- React dashboard with overview, security-posture radar, score history, watched domains, scan history and drift inbox.
- FastAPI scanner, public/shareable reports and branded PDF downloads.
- Persistent daily scan schedules, pause/resume, grade-drop detection and an email outbox using managed Resend.
- Supabase Auth, PostgreSQL persistence in the `wevnsec` schema, row-level security and Alembic migrations.
- Account-wide login cooldown and explicit CORS/origin validation.

This source archive deliberately excludes real `.env` files, credentials, database records/backups, dependencies, internal QA scripts/reports and generated build files.

## Prerequisites
- Python 3.11 and Node.js 20+ with Yarn Classic.
- A configured Supabase project with a Postgres connection string and Auth keys.
- Your existing managed email integration configuration. No email credential is bundled.

## Setup

1. Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env`.
2. Fill all backend configuration values from your own environment. Keep service-role and email keys server-side. Choose strong admin/demo passwords; use a random JWT secret.
3. Set `APP_URL` to the frontend origin used in report email links. Set `CORS_ORIGINS` to exact trusted browser origins, comma-separated. Do not use `*`. If a trusted reverse proxy rewrites Origin, include its exact configured origin too.
4. Install backend dependencies and apply the migrations:

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
alembic upgrade head
uvicorn server:app --host 0.0.0.0 --port 8001
```

On Windows, activate using `.venv\Scripts\activate`.

5. Start the frontend in a second terminal:

```sh
cd frontend
yarn install --frozen-lockfile
yarn start
```

Open the frontend origin configured in your environment. The example configuration uses local frontend port 3000 and backend port 8001. `yarn build` creates the frontend production bundle.

## Configuration notes
- `DATABASE_URL` is the Supabase Postgres connection URL (`postgresql://...`), with URI-encoded password characters when necessary. SQLAlchemy and Alembic use it directly.
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` come from the same Supabase project.
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` and `DEMO_EMAIL` / `DEMO_PASSWORD` seed accounts only if absent. Existing account passwords are not replaced on startup.
- `EMERGENT_EMAIL_KEY` and `EMAIL_FROM_NAME=WevnSec` configure managed email. `EMAIL_REPLY_TO` is optional and should only be an inbox you control.
- Existing `MONGO_URL` / `DB_NAME` are legacy compatibility settings; current application persistence is Supabase/Postgres.
- The backend polls durable scheduled work every 30 seconds while the process is running. Schedules/leases survive restarts; completed scheduled scans set their next run approximately 24 hours later. This is not a guarantee of an exact wall-clock time.
- Email alerts are off by default. Enable them per domain to send grade-drop notices to the account email. A provider-accepted status does not guarantee inbox delivery. Known retryable rejections retry up to three attempts; ambiguous delivery outcomes are not retried automatically to reduce duplicates.
- PDFs are public to anyone with the same share ID as the corresponding public report. They describe automated checks, not a compliance certification or exhaustive pentest.

## Database safety
Migrations only introduce/change `wevnsec` application objects. Legacy `public` tables have NOT been dropped: auth triggers, RPCs and an active cleanup job still depend on them. See `docs/LEGACY_RETIREMENT.md` for the assessment and proposed staged retirement steps. This archive is source code, not a database backup.

## Verification status
The frontend production build passes. Agent verification covered the dashboard routes, responsive layouts, domain controls, scheduled scans, decline-only alerts, PDF downloads, managed email acceptance at the provider's test inbox, CORS rejection and login cooldown. Email failure/retry branches used isolated test fixtures, not mocked application APIs. A full clean-room installation from this archive has not been run.

Preview infrastructure may rewrite cookie attributes to `SameSite=None; Partitioned`; application code emits HttpOnly/Secure cookies with SameSite=Lax. Follow-up QA noted this proxy-level difference and a non-substantive exact-text PDF extraction mismatch on a wrapped long fragment.
