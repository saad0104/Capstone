# ThreatGPT — Project Status Update

_Last updated: 2026-07-29_

## What it is

An LLM-assisted CTI (cyber threat intelligence) summarization and alert-generation system, built as a capstone project.

## Architecture (backend and frontend both built and verified end-to-end)

```
React/Tailwind dashboard (dark theme, react-router-dom)
  "/" Analyze + provider selector | "/alerts" List/Filter/CSV | "/alerts/:id" Detail/JSON export
        │  HTTP/REST (CORS via flask-cors, CORS_ORIGINS env var)
        ▼
Flask API (/health, /api/analyze, /api/alerts, /api/alerts/<id>)
        │
        ▼
Preprocessing (regex IoC extraction; nltk installed, staged, unused)
        │
        ▼
LLM service (LangChain: prompt | chat_model | PydanticOutputParser,
             2-shot structured-JSON prompt; provider registry --
             Gemini / Grok / local Ollama, one active by default or
             per-request via AnalyzeRequest.provider)
        │
        ▼
Alert engine (backend/alert_engine.py: IoC reconciliation,
              severity keyword cross-check, upgrade-only)
        │
        ▼
SQLite (Alert table, via backend/db.py)
        │
        ▼
Dashboard display -- alert appears in Alerts Context immediately, no refetch needed
```

- **Frontend:** React + Vite + Tailwind, react-router-dom, Context+useReducer state — fully built, all 3 pages working against the real API
- **Backend:** Flask + Werkzeug (kept over FastAPI for Phase 2, see `docs/implementation_notes.md` decision #7)
- **Validation:** Pydantic v2 (manual validation in Flask routes)
- **Preprocessing:** regex (IoC extraction) — sole authoritative source, matches the method the Phase 1 ground-truth CSVs were built with
- **LLM service:** LangChain provider registry — Gemini (live-verified), Grok/Ollama (implemented, untested, honestly labeled "unverified" in the UI)
- **Database:** SQLAlchemy + SQLite (MVP), Postgres upgrade path
- **Deployment target:** Render/Railway (backend) + Vercel/Netlify (frontend) — not yet deployed anywhere

## Plan (5 phases)

| Phase | Timeline | Activity |
|---|---|---|
| 1 | Days 8–16 | Data collection: 50–100 docs, 20 manually labeled |
| 2 | Days 17–27 | Backend implementation |
| 3 | Days 28–37 | Frontend, end-to-end integration |
| 4 | Days 38–40 | Formal evaluation |
| 5 | Days 41–45 | Report writing |

## Done

- **Phase 0 (Setup)** — complete. Repo scaffold, Flask skeleton, SQLAlchemy `Alert` model, React/Vite scaffold.
- **Phase 1 (Data collection)** — complete.
  - 50 raw, source-attributed documents (NVD, CISA, Google Threat Analysis Group, Microsoft Security, CERT/CC), full provenance in `data/metadata.csv`.
  - 20-record balanced, human-reviewed ground-truth set in `data/annotations/labels.csv`.
  - Broader 50-record draft label pool in `data/annotations/draft_labels.csv` (unreviewed scratch set, not required for Phase 1 exit).
- **Phase 2 (Backend)** — complete, 2026-07-28.
  - `POST /api/analyze`, `GET /api/alerts`, `GET /api/alerts/<id>`, `DELETE /api/alerts/<id>` alongside `/health`.
  - Full pipeline wired: regex preprocessing → LangChain LLM call → alert engine reconciliation → SQLite persistence → JSON response.
  - 18 passing tests (`backend/tests/`), LLM mocked so no live API key is needed to run the suite.
  - Live-verified against a real Gemini API call: correct threat classification, severity correctly upgraded by the keyword cross-check, correct CVE extraction.
  - Grok and Ollama providers are implemented on the same registry pattern but not yet tested against a real key/local instance.
- **Phase 3 (Frontend)** — complete, 2026-07-29.
  - Three routed pages (`/`, `/alerts`, `/alerts/:id`) via `react-router-dom`, alert state in a Context+`useReducer` store.
  - Analyze page: textarea, honest Gemini/Grok/Ollama provider selector (Grok/Ollama visibly badged "unverified"), inline result display, distinct error UI for invalid input (400) vs. provider failure (502) vs. unreachable backend.
  - Alerts list: threat_type/severity filters, CSV export of the filtered set.
  - Alert detail: full field display, JSON export, delete with confirm.
  - Dark SOC-dashboard theme via Tailwind design tokens (severity color scale, monospace IoC chips).
  - Backend touch-ups required to make this work: `AnalyzeRequest.provider` field threaded through to `LLMService`, and CORS (`flask-cors`, env-configurable) since the backend had none at all before.
  - Verified: production build succeeds, all modules transform cleanly through the dev server, full `/api/analyze` → list → detail → delete flow confirmed live against the real backend with real CORS headers. **Not verified: an actual browser click-through** — no browser tool available, so layout/interactivity/visual correctness still needs a human pass.
  - One real pre-existing bug caught and fixed: `postcss.config.cjs` never existed since Phase 0, so Tailwind was never actually processing anything — `@tailwind`/`@apply` were being shipped to the browser as literal text.

## Not yet built

- **Phase 4 (Evaluation)** — `evaluate.py` / `report_metrics.py` don't exist yet, but the backend they'd run against now exists — this could start any time. **This is the next milestone.**
- **Phase 5 (Report)** — not started.
- Rate limiting on `/api/analyze` — deliberately deferred as a stretch item (decision already logged in `docs/implementation_notes.md`, not implemented).
- Frontend automated tests (Vitest/React Testing Library) — deliberately deferred, same MVP-scope tradeoff as the backend rate limiter.
- A real browser click-through of the frontend — recommended before calling Phase 3 fully done, not something this session could perform.
- Deferred by explicit decision, not forgotten: FastAPI migration, LangGraph, git wiki, "modular git deployment" (this directory isn't a git repo yet).

## Bottom line

Both backend and frontend are real and working end-to-end, not just scaffolded — a user can submit a threat report, see it classified and enriched with real IoCs, browse/filter/export the alert history, and drill into and delete individual alerts. Formal evaluation (Phase 4) against the 20-doc `labels.csv` set is the natural next step now that the full pipeline exists to run it against.



1. MVP 
2. Fast API, nltk, langchain/langgraph and attention grab
3. Modular git deployment
4. git wiki
5. design frontend(cyber sec theme)
6. local llm
7. llm selection option for user(gemini, grok, local ollama powered)