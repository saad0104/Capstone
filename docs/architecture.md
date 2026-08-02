# ThreatGPT System Architecture

## Overview

ThreatGPT is an end-to-end LLM-assisted pipeline for cyber threat intelligence (CTI) summarization and alert generation. The system ingests raw threat reports, processes them through a preprocessing pipeline, uses an LLM to extract and structure threat information, applies rule-based severity refinement, and stores results in a searchable database. A web dashboard allows analysts to review, filter, and export alerts.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              User Interface (React + Tailwind, dark theme)       │
│              react-router-dom routes, Context+useReducer state   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  "/" Analyze │  │ "/alerts"    │  │"/alerts/:id" │          │
│  │  + provider  │  │ Log & Filter │  │ Detail       │          │
│  │  selector    │  │ + CSV export │  │ + JSON export│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬──────────────────────────────────┘
                             │ HTTP / REST API (CORS via flask-cors,
                             │ CORS_ORIGINS env var)
┌────────────────────────────▼──────────────────────────────────┐
│                    Backend (Flask API Server)                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Endpoint: POST /api/analyze (raw_text)                 │  │
│  │  ┌─────────────────────────────────────────────────────┐│  │
│  │  │ 1. Input Validation (Pydantic)                      ││  │
│  │  │    - Check text length, format                      ││  │
│  │  └─────────────────────────────────────────────────────┘│  │
│  │                         ▼                                │  │
│  │  ┌─────────────────────────────────────────────────────┐│  │
│  │  │ 2. Text Preprocessing (Regex)                      ││  │
│  │  │    - Normalize whitespace (clean_text)               ││  │
│  │  │    - Extract IoCs: IPs, CVEs, domains, hashes       ││  │
│  │  │    - nltk installed, staged for future use, not     ││  │
│  │  │      yet wired into any pipeline step               ││  │
│  │  └─────────────────────────────────────────────────────┘│  │
│  │                         ▼                                │  │
│  │  ┌─────────────────────────────────────────────────────┐│  │
│  │  │ 3. LLM Service (LangChain provider registry)        ││  │
│  │  │    - prompt | chat_model | PydanticOutputParser      ││  │
│  │  │    - 2-shot structured-JSON prompt                   ││  │
│  │  │    - Default via LLM_PROVIDER; API can override:   ││  │
│  │  │      Gemini / Grok / Ollama / OpenRouter / Claude   ││  │
│  │  │    - Return: {summary, threat_type, severity,       ││  │
│  │  │      recommended_action}                             ││  │
│  │  │    - No retry/backoff or response caching yet        ││  │
│  │  └─────────────────────────────────────────────────────┘│  │
│  │                         ▼                                │  │
│  │  ┌─────────────────────────────────────────────────────┐│  │
│  │  │ 4. Alert Engine (backend/alert_engine.py)           ││  │
│  │  │    - Dedupe/validate regex-extracted IoCs            ││  │
│  │  │    - Cross-check severity with keyword signals       ││  │
│  │  │      (upgrade-only, never downgrades the LLM call)   ││  │
│  │  │    - Add metadata: UUID, timestamp, processing_ms    ││  │
│  │  │    - No numeric confidence score yet                 ││  │
│  │  └─────────────────────────────────────────────────────┘│  │
│  │                         ▼                                │  │
│  │  ┌─────────────────────────────────────────────────────┐│  │
│  │  │ 5. Database Storage (SQLAlchemy + SQLite)           ││  │
│  │  │    - Persist alert to Alerts table                  ││  │
│  │  │    - Log raw input for audit trail                  ││  │
│  │  └─────────────────────────────────────────────────────┘│  │
│  │                         ▼                                │  │
│  │  ┌─────────────────────────────────────────────────────┐│  │
│  │  │ 6. Response to Client                               ││  │
│  │  │    - Return structured alert (JSON)                 ││  │
│  │  │    - HTTP 200 on success, 4xx/5xx on error         ││  │
│  │  └─────────────────────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Other Endpoints:                                        │  │
│  │  - GET /api/alerts — list all alerts                    │  │
│  │  - GET /api/alerts/<id> — fetch alert details           │  │
│  │  - DELETE /api/alerts/<id> — remove alert               │  │
│  │  - GET /health — service health check                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SQL/ORM
┌──────────────────────────▼──────────────────────────────────────┐
│                      SQLite Database                             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Alerts Table                                            │  │
│  │  ├── id (UUID, PK)                                       │  │
│  │  ├── raw_input (TEXT)                                    │  │
│  │  ├── summary (TEXT)                                      │  │
│  │  ├── threat_type (VARCHAR 64)                            │  │
│  │  ├── severity (VARCHAR 16: Low/Medium/High/Critical)    │  │
│  │  ├── ioc_list (JSON: [ips, cves, hashes, domains])     │  │
│  │  ├── recommended_action (TEXT)                           │  │
│  │  ├── created_at (DATETIME)                               │  │
│  │  └── processing_ms (INT)                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

The provider names shown in the diagram are the original UI-facing set. The
implemented backend registry also includes OpenRouter and Claude; the complete
provider list is maintained in the component table and design decisions below.

1. **User inputs raw threat text** → Analyze page textarea, with an optional per-request provider selection (Gemini/Grok/Ollama)
2. **API receives request** → `/api/analyze` endpoint validates and processes
3. **Preprocessing stage** → normalizes text, extracts IoCs with regex
4. **LLM call** → sends structured prompt via LangChain to the selected or default provider
5. **Alert enrichment** → validates output, applies severity rules, adds metadata
6. **Persistence** → stores complete alert in SQLite database
7. **Response** → returns structured JSON to frontend, added to the Alerts Context so the list updates without a refetch
8. **Display** → dashboard renders alert with severity badge, monospace IoC chips; list view supports threat_type/severity filtering and CSV export; detail view supports JSON export and delete

---

## Component Responsibilities

| Component            | Technology              | Responsibility                                             |
| -------------------- | ----------------------- | ---------------------------------------------------------- |
| **Frontend**         | React + Vite + Tailwind, react-router-dom | 3 routed pages (Analyze/List/Detail), Context+useReducer state, dark SOC-dashboard theme |
| **API Server**       | Flask + Werkzeug        | HTTP endpoint routing, request/response handling           |
| **Input Validation** | Pydantic                | Schema validation, error handling                          |
| **Cross-origin access** | flask-cors            | Env-configurable allowed origins (`CORS_ORIGINS`), required since frontend/backend are separate origins in dev and prod |
| **Preprocessing**    | Regex (nltk staged, unused) | Text normalization, IoC extraction                     |
| **LLM Service**      | LangChain (Gemini / Grok / Ollama / OpenRouter / Claude) | Structured-output chain, provider registry |
| **Alert Engine**     | Custom Python (`backend/alert_engine.py`) | IoC reconciliation, severity cross-check   |
| **Database**         | SQLAlchemy + SQLite     | Alert persistence, schema management                       |

---

## Key Design Decisions

1. **Multi-provider LLM via LangChain** — the provider registry supports Gemini, Grok (xAI), local Ollama, OpenRouter, and Claude. `LLM_PROVIDER` supplies the default and the API accepts a per-request override. The current UI exposes Gemini, Grok, and Ollama; OpenRouter and Claude are available to the backend and evaluation harness.
2. **Hybrid severity scoring** — Combine LLM output with keyword-based signals in `alert_engine.py`; the cross-check can only upgrade severity, never downgrade the LLM's call.
3. **Structured JSON output** — LangChain `PydanticOutputParser` forces a deterministic schema (not free-text), with 2-shot examples in the prompt.
4. **Rule-based preprocessing** — Regex-based IoC extraction is the sole, authoritative source of IoCs (reduces hallucination); the LLM is never asked to produce IoCs itself.
5. **Flask retained over FastAPI** — deliberate choice to keep the existing skeleton rather than migrate for Phase 2; revisit later if needed.
6. **SQLite for MVP** — Lightweight, no external DB required; can upgrade to PostgreSQL later.
7. **Real client-side routing (react-router-dom)** — three real routes (`/`, `/alerts`, `/alerts/:id`), not a state-based view switch, so alerts are deep-linkable/shareable.
8. **Per-request provider selection, surfaced honestly** — the Analyze page lets a user pick Gemini/Grok/Ollama per request (threaded through `AnalyzeRequest.provider` → `LLMService(provider=...)`), but the UI visibly marks Grok/Ollama as "unverified" rather than presenting all three as equally reliable, since only Gemini has been live-verified end-to-end.
9. **CORS via flask-cors, not a dev-only proxy** — since production hosts the frontend and backend on separate origins (see Deployment Model), CORS is solved once, robustly, via an env-configurable allowlist rather than a Vite dev proxy that wouldn't carry over to prod.
10. **Both export formats implemented** — CSV for the (filtered) alerts list, JSON for a single alert detail — both generated client-side from data the API already returns, no new backend endpoints needed.

**Not yet implemented**: production response caching, production retry/backoff, numeric alert confidence scoring, rate limiting, frontend automated tests (Vitest/React Testing Library), and a PostgreSQL migration. The evaluation harness has its own pacing and limited retry logic; that is not production retry/backoff.

---

## Deployment Model

- **Backend** — Render (Flask app + gunicorn + SQLite DB), defined by the `render.yaml` Blueprint at the repo root. Deployed backend's `CORS_ORIGINS` env var must be set to the deployed frontend's actual origin (defaults to `http://localhost:5173` for local dev).
  - **Known limitation**: Render's free-tier filesystem is ephemeral — the SQLite file is wiped on every redeploy, restart, or 15-minute-idle spin-down (see `backend/db.py`'s default `DATABASE_URL` path). Alert data does not persist across these events unless a paid persistent disk is attached, or the app is later migrated to a managed database (e.g. Render Postgres). Not fixed as part of the current deployment setup — documented so it isn't mistaken for a bug.
  - Free-tier services also spin down after 15 minutes of inactivity and take roughly 30-60 seconds to wake on the next request — the first request after idle time will be slow, not broken.
- **Frontend** — Netlify (static build + React bundle), defined by the `netlify.toml` at the repo root (base directory `frontend/`, SPA redirect to `index.html` for `react-router-dom`'s client-side routes). Deployed frontend's `VITE_API_BASE_URL` must point at the deployed Render backend's actual URL (defaults to `http://localhost:5000` for local dev).
- **LLM API** — Gemini, Grok (xAI), OpenRouter, Claude, or a self-hosted local Ollama instance (no per-call cost)
- **Infrastructure** — Minimal, cost-effective (no serverless complexity)
- See `docs/deployment.md` for the exact step-by-step deployment runbook.

---

## Performance Targets

- **Latency**: aspirational mean response time < 10 seconds; the binding course criterion is p95 < 15 seconds.
- **Throughput**: Handle 10–20 concurrent requests (not load-tested yet).
- **Cost**: < $0.10 per analyze call (provider-dependent estimate).
- **Accuracy**: aspirational threat-type macro F1 > 0.80; the binding course criterion is > 0.75.

The initial OpenRouter evaluation met the binding threat-type criterion (0.78)
but missed the severity and p95-latency criteria. See `docs/evaluation_results.md`.
