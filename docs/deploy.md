# Deploying Gym CRM

The app has five parts:

| Part | What it is | Notes |
|---|---|---|
| **web** | Next.js (`frontend/`) | Browsers only talk to this. It proxies `/api/*` to the API, so login cookies stay first-party. |
| **api** | FastAPI (`backend/`) | Runs database migrations on start. Health check: `/api/health/ready`. |
| **worker** | Celery with the beat scheduler (same image as the API) | Sends membership reminders every hour. **Run exactly one.** |
| **Postgres 16** | The database | |
| **Redis** | The job queue | |

Uploaded files (progress photos, expense bills, import files) go to **S3 or Cloudflare R2**. Container disks are wiped on every deploy.

## Option A: Render (one click, recommended to start)

[`render.yaml`](../render.yaml) creates all five parts.

1. Push this repo to GitHub, then in Render choose **New → Blueprint** and pick the repo.
2. Fill in the values Render asks for. See the [environment variables](#environment-variables) below.
   - Set `FRONTEND_URL` to the web service's address, for example `https://gym-crm-web.onrender.com`. You can update it after the first deploy if you don't know it yet.
   - `JWT_SECRET` is generated for you.
3. Deploy. The API applies the migrations itself. Open the web URL and sign up: the first account creates your gym.
4. *(Optional)* Add a custom domain to **gym-crm-web**, then update `FRONTEND_URL`.

> **Cost:** roughly the price of 3 starter services + a small Postgres + Redis on Render. Free instances sleep when idle, which breaks reminders, so the worker needs a paid plan.

## Option B: Vercel (web) + Render or Railway (API, worker, databases)

1. Deploy the backend pieces as in option A, but leave out the `gym-crm-web` service.
2. Import `frontend/` into Vercel and set these:
   - `BACKEND_URL`: the API's public URL, e.g. `https://gym-crm-api.onrender.com`. Rewrites are fixed at build time, so redeploy after changing it.
   - `NEXT_PUBLIC_SENTRY_DSN` and `SENTRY_DSN`: optional.
3. Set `FRONTEND_URL` on the API to the Vercel URL.
4. Set `TRUSTED_PROXY_HOPS=2` on the API, because Vercel's edge and the Next.js server both append to `X-Forwarded-For`.

## Option C: your own server (Docker)

```bash
docker compose up --build
```

[`docker-compose.yml`](../docker-compose.yml) runs everything locally.

For a server, copy it and then:
- Set `ENVIRONMENT=production`, a strong `JWT_SECRET` and `COOKIE_SECURE=true`.
- Configure S3 or R2.
- Put the web container behind a TLS proxy such as Caddy or nginx.
- Set `TRUSTED_PROXY_HOPS=2` when that proxy appends to `X-Forwarded-For`.
- Don't publish the database or Redis ports.

## Environment variables

These are set on the API and the worker. See [`backend/.env.example`](../backend/.env.example) for all of them.

| Variable | Production value |
|---|---|
| `ENVIRONMENT` | `production`. This turns on startup checks: the API refuses to start without a strong `JWT_SECRET`, `COOKIE_SECURE=true`, Postgres, and `SCHEDULER=celery` (or `off`). |
| `DATABASE_URL` | A Postgres URL. `postgres://…` from your host is fine; the right driver is filled in automatically. |
| `REDIS_URL` | The Redis URL. |
| `JWT_SECRET` | 32+ random characters. Changing it signs everyone out. |
| `COOKIE_SECURE` | `true` |
| `SCHEDULER` | `celery`, with exactly one worker running |
| `FRONTEND_URL` | Public web address. Used in invite and preview links, and in emails. |
| `TRUSTED_PROXY_HOPS` | `2` behind a load balancer + Next.js. Used for rate limiting. |
| `EMAIL_PROVIDER` | `resend` (needs `RESEND_API_KEY`) or `smtp` (needs `SMTP_*`) |
| `EMAIL_FROM_ADDRESS` | An address on a domain you've verified with your email provider |
| `STORAGE_PROVIDER` | `s3`, plus `S3_BUCKET`, `S3_REGION`, `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY`. For **R2**, also set `S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com` and `S3_REGION=auto`. Keep the bucket **private**: the API checks permissions, then hands out links that expire after 5 minutes. |
| `ANTHROPIC_API_KEY` | Optional. Turns on AI workout and diet plans. |
| `SENTRY_DSN` | Optional. Turns on error reporting. |
| `LOG_JSON` | `true` for log collectors |

## Error monitoring and logs

- **Sentry:** create a project and set `SENTRY_DSN`.
  - API and worker: set it on both.
  - Web app: set `NEXT_PUBLIC_SENTRY_DSN` (browser, needed at build time) and `SENTRY_DSN` (server).
- **What's sent to Sentry:** request bodies, cookies, query strings, user details and the secret tokens in preview and invite links are all removed before anything leaves the app.
- **Request IDs:** every API response carries an `X-Request-ID`, and every log line includes it. Quote it when tracing a problem.
- **Health checks:**
  - `/api/health` answers if the process is up.
  - `/api/health/ready` also checks the database.

## Backups

- **Database:** turn on your host's daily Postgres backups and test a restore once. Render keeps point-in-time backups on paid Postgres plans.
- **Uploaded files:** turn on versioning, or a lifecycle backup, for the S3/R2 bucket.
- **For gym owners:** each gym can download all its data as CSV from **Settings → Data**.

## Before going live

- [ ] Production deploy is green and `/api/health/ready` returns `ok`.
- [ ] Signing up creates a gym; inviting a staff member sends a working link (check `FRONTEND_URL`).
- [ ] A test reminder email arrives (**Reminders → Send emails now**) and isn't in spam (check SPF and DKIM for your domain).
- [ ] Uploading a progress photo still works after a redeploy (S3/R2 configured).
- [ ] An error shows up in Sentry. Try a wrong API route from the browser console and check the logs too.
- [ ] Database backups are on.
- [ ] Only one worker is running, otherwise reminders could be sent twice. The reminder log stops duplicates, but don't rely on that.
