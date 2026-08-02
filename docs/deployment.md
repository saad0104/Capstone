# Deployment Runbook

Backend: **Render**. Frontend: **Netlify**. This doc separates what is already
prepared as files in this repo from what you must do by hand in each
platform's dashboard — no deployment CLI is installed in this environment,
so account creation, GitHub connection, and button-clicks cannot be
automated from here.

## Prerequisites (already done, nothing to click)

- `render.yaml` at the repo root — Render Blueprint definition for the backend.
- `netlify.toml` at the repo root — build config (base directory `frontend/`,
  build command `npm run build`, publish directory `frontend/dist`) plus an
  SPA redirect rule so client-side routes (`/alerts/:id`) don't 404 on
  refresh or direct link.
- `gunicorn` added to `requirements.txt` — Flask's own dev server isn't meant
  for production; `render.yaml`'s start command uses it via the app-factory
  invocation `gunicorn 'backend.app:create_app()'`.
- `/health` already exists in `backend/app.py`, used as Render's health check.

## Known limitation: SQLite on Render's free tier

Render's free-tier filesystem is **ephemeral**. Alert data written via
`/api/analyze` will be lost on every redeploy, restart, or 15-minute
inactivity spin-down. This is not fixed here — attaching a paid persistent
disk, or migrating to a managed database (e.g. Render Postgres), is a
separate future decision. Free-tier services also **cold-start** (~30-60s)
after 15 minutes idle — the first request after a quiet period will be slow,
not broken.

## Step 1 — Push the prepared config files

Commit and push `render.yaml`, `netlify.toml`, and the `requirements.txt`
diff (adds `gunicorn`). Keep this separate from any other in-progress,
unrelated work in the same working tree — don't bundle unrelated changes
into this commit.

## Step 2 — Deploy the backend on Render (dashboard)

1. Create a Render account (or log in), connect the `saad0104/Capstone`
   GitHub repo.
2. **New → Blueprint** → select this repo. Render detects `render.yaml`
   automatically.
3. When prompted for environment variables, enter real values for:
   - `LLM_PROVIDER` (e.g. `gemini`)
   - `GEMINI_API_KEY` (your real key — paste directly into Render's UI, never into a file or chat)
  - `OPENROUTER_API_KEY` (only needed for OpenRouter), `XAI_API_KEY` (only needed for Grok), or `ANTHROPIC_API_KEY` (only needed for Claude)
   - `CORS_ORIGINS` — temporarily set to `http://localhost:5173`; corrected in Step 4 once the real Netlify URL is known
   - `DATABASE_URL` — `sqlite:///data/threatgpt.db` is fine to start (not a secret, just a path)
4. Deploy. Note the resulting URL, e.g. `https://threatgpt-backend.onrender.com`.
5. Verify: `curl https://threatgpt-backend.onrender.com/health` → `{"status": "ok"}`. The deployment is not complete until this succeeds.

## Step 3 — Point Netlify at the Render backend (dashboard)

1. Netlify site → **Site configuration → Environment variables**.
2. Set `VITE_API_BASE_URL` to the Render URL from Step 2.
3. Trigger a redeploy — env var changes don't apply to already-built assets.

## Step 4 — Point Render's CORS at the real Netlify URL (dashboard)

1. Render service → **Environment**.
2. Set `CORS_ORIGINS` to the deployed Netlify URL (e.g.
   `https://threatgpt.netlify.app`; comma-separate if there's also a custom domain).
3. Save — this triggers a backend redeploy.

## Step 5 — Verify end-to-end

- `curl <render-url>/health` → `{"status": "ok"}`
- Load the Netlify URL, submit an analysis on `/`, confirm it appears on `/alerts`.
- Open `/alerts/<id>` **directly** (paste the URL, don't navigate via the app) and refresh — should render, not 404. This confirms the SPA redirect rule works.
- Check the browser devtools console — no CORS errors.
- If the backend had been idle for >15 minutes, expect the first request to take up to ~60 seconds (cold start) — not a bug.
