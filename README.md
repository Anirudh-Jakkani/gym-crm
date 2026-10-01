# Gym CRM

Multi-gym SaaS CRM: members, customizable plans, weekly check-ups, AI workout/diet plans with
member preview links, expiry reminders, leads, finance, analytics and data import.

| Part | Stack |
|---|---|
| `frontend/` | Next.js 15 (App Router, TypeScript), shadcn/ui (Base UI + Tailwind v4), TanStack Query, React Hook Form + Zod, typed client via openapi-fetch |
| `backend/` | FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2, JWT auth (httpOnly cookies) |
| Data | PostgreSQL 16 in Docker/production; SQLite for local dev without Docker. Redis for background jobs (upcoming). |

## Status

**Phase 1: foundation (done)**
- Gym signup creates the gym (tenant), a main branch and an owner account.
- Login, refresh, logout and gym switching.
- Roles: owner, manager, trainer and front desk.
- Gym settings, including membership expiry reminder timing.
- Branches.
- Staff invites by shareable link, with role and branch management.
- Tenant isolation: every tenant query goes through `TenantRepository`, and tests prove one gym can't read or change another's data.

**Phase 2: plans & members (done)**
- **Custom plan builder:**
  - Any duration in days, weeks, months or years, with price, joining fee, tax %, included services and allowed freeze days.
  - Archive or restore a plan. Only plans that were never sold can be deleted.
- **Member onboarding:**
  - Profile, emergency contact, fitness profile (goal, diet, experience, height, medical notes), trainer, branch and tags.
  - Optionally sell the first membership in the same step, with a live price and end-date preview.
- **Membership lifecycle:**
  - Renew: the next membership starts the day after the current one ends, and the joining fee only applies to the first.
  - Freeze and unfreeze: the end date moves by the frozen days, and later renewals move with it.
  - Cancel.
  - Overlapping memberships are rejected. Plan terms are copied into each membership, so editing a plan never rewrites history.
- **Statuses** (active, expiring soon, frozen, upcoming, expired, no plan) are computed from "today" in the gym's own time zone.
- **Members list:** status tabs with counts, search by name, phone or email, trainer, branch and tag filters, sorting and pagination.
- **Dashboard:** member stats and a "renewals due" list.
- **Member preview links:** each member already gets a private link token (copy, share on WhatsApp, regenerate). The page it opens comes in phase 5.

**Phase 3: membership expiry reminders (done)**
- **Settings:** the owner picks the reminder days (e.g. 7, 3 and 1 days before, on the day, 3 days after) and a send hour in the gym's time zone. They can also edit the message templates, with `{placeholders}` and a live preview.
- **Automatic email:**
  - Members with an email address get reminders automatically.
  - Members who already renewed are skipped.
  - Every send is recorded in `reminder_logs`, which has a unique key per membership, reminder day and channel. A send is claimed before it is sent, so the job can run hourly, or on several machines, without double-sending.
  - Failed sends are logged, and **Send emails now** retries them.
- **WhatsApp:** the **Reminders → Due** list has a one-click WhatsApp button with the message prefilled. Staff send it from their own WhatsApp, and the app logs it. The WhatsApp Business API comes later.
- **Staff alerts:**
  - A daily digest notification goes to owners, managers and the front desk via the header bell.
  - The sidebar badge counts reminders nobody has sent yet.
  - The History tab shows every send.

**Phase 4: check-ups & progress (done)**
- **Check-ups:** weight, body fat %, muscle mass, height (keeps the profile's height up to date), automatic BMI, chest/waist/hips/arm/thigh measurements and trainer notes. One check-up per member per day. Whoever recorded a check-up can edit it; managers and owners can edit any.
- **Progress photos:** up to 4 per check-up, JPEG, PNG or WebP, max 8 MB.
  - The file type is checked from the file's contents, not the name it was uploaded with.
  - Stored privately: on local disk in dev, or in S3 or Cloudflare R2 in production.
  - Only served through a check-up photo endpoint that checks the viewer's gym, never from a public URL.
  - Deleting a photo, check-up or member also deletes the stored files.
- **Member Progress section:** stat tiles with the change since the first check-up, a chart per metric, history and a photo viewer.
- **Check-ups page:** members with a running membership who are due (owner-set interval, default 7 days), longest waiting first, with a "My members" filter for trainers.

Storage settings: `STORAGE_PROVIDER=local` (`STORAGE_DIR`, default `./uploads`) or `s3` (`S3_BUCKET`, `S3_REGION`, `S3_ENDPOINT_URL` for R2/MinIO, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`).

**Phase 5: AI plans & member page (done)**
- **AI plans:** trainers pick days per week, session length, equipment and extra instructions. Claude (`claude-opus-5-5`) writes a structured 4-week workout and diet plan.
  - **Inputs:** the member's age, sex, goal, diet preference, experience, medical notes (treated as hard constraints) and recent check-ups.
  - **Never sent:** name, phone or email.
  - **Request details:** structured output via a Pydantic schema, explicit effort, a cached system prompt, and a server-side refusal fallback. Refusals and API errors become clear messages for staff.
  - **Runs in the background:** the UI polls until the plan is ready. There's a monthly quota per gym (`AI_MONTHLY_PLAN_LIMIT`).
- **Review before members see it:**
  - Every plan is a draft until a trainer reviews it in the editor (workouts, exercises, meals, macros, notes) and publishes it.
  - Plans are versioned. Publishing a new version archives the old one, and published plans can be unpublished.
- **Member page `/p/{token}`:** a private, mobile-friendly page for the member.
  - Shows membership status and dates, their trainer, a "call the gym" button, progress (weight chart) and the published plan.
  - No login needed, rate-limited, not indexed by search engines, no referrer sent.
  - Never shows internal IDs, contact details or photos.
  - Staff can copy the link, send it on WhatsApp, replace it, or turn it off.

AI settings: `ANTHROPIC_API_KEY` (required to generate), `AI_MODEL` (default `claude-opus-5-5`), `AI_EFFORT` (default `medium`), `AI_MONTHLY_PLAN_LIMIT` (default 100). Roughly 3K input and 5K output tokens per plan, so about $0.10–0.15 each at Opus 5.5 prices.

Next up are leads, then finance, data import and analytics. The full plan is in [`docs/plan.md`](docs/plan.md).

## Background jobs & email

| Setting | Values |
|---|---|
| `SCHEDULER` | `inprocess` (default; runs inside the API, good for dev/single server), `celery` (production), `off` |
| `EMAIL_PROVIDER` | `console` (default; prints emails to the API log), `smtp` (`SMTP_HOST/PORT/USERNAME/PASSWORD`), `resend` (`RESEND_API_KEY`) |
| `EMAIL_FROM_ADDRESS` | Sender address. The gym's name is used as the sender name. |

In production, run a worker that has the beat scheduler built in:
```bash
celery -A app.worker worker --beat --loglevel=info
```
`docker compose up` already starts this as the `worker` service, with Redis.

## Run locally (no Docker)

You need [uv](https://docs.astral.sh/uv/) and Node 20 or newer.

```bash
# API: http://localhost:8000/api/docs
cd backend
uv sync
uv run alembic upgrade head
uv run python scripts/seed.py        # optional demo gym (logins listed at the top of the script)
uv run uvicorn app.main:app --reload --port 8000
```

```bash
# Web: http://localhost:3000
cd frontend
npm install
npm run dev
```

The web app proxies `/api/*` to the API (see `next.config.ts`), so auth cookies stay first-party.

## Run with Docker (Postgres)

```bash
docker compose up --build
```

## Common tasks

| Task | Command |
|---|---|
| Backend tests | `cd backend && uv run pytest` |
| Backend lint/format | `uv run ruff check . && uv run ruff format .` |
| New migration after model changes | `uv run alembic revision --autogenerate -m "..."` then `uv run alembic upgrade head` |
| Regenerate frontend API types after API changes | `cd frontend && npm run gen:api` |
| Add a shadcn component | `cd frontend && npx shadcn@latest add <name>` |
| Frontend checks | `npm run lint && npm run typecheck && npm run build` |

## Conventions

- **Tenant data:**
  - Add `TenantMixin` to the model (it gives the `gym_id` column).
  - Access it only through a `TenantRepository` subclass built with `ctx.gym_id`.
  - A record from another gym then behaves exactly like a missing one (404).
  - Add an isolation test for every new resource in `tests/test_tenant_isolation.py`.
- **Permissions:** use the `CurrentContext`, `ManagerContext` or `OwnerContext` dependencies in `app/core/deps.py`. Roles are read from the database on every request, so changes apply immediately.
- **Backend modules** live in `app/modules/<name>/`, each with `models.py`, `schemas.py`, `repository.py` and `router.py`. Register new models in `app/models.py`.
- **shadcn/ui on Base UI:**
  - Compose with the `render` prop instead of `asChild`, e.g. `<Button nativeButton={false} render={<Link href="/" />} />`.
  - Use `SimpleSelect` for plain option lists.
