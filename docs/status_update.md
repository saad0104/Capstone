# ThreatGPT — Project Status

_Last updated: 2026-08-02_

ThreatGPT is an LLM-assisted Cyber Threat Intelligence system that turns a raw threat report into a structured, stored alert. Its implemented flow is:

```text
React dashboard → Flask API → regex IoC extraction → LangChain LLM analysis
                → alert-engine severity reconciliation → SQLite → dashboard/export
```

## Completed work

| Phase | Status | Deliverable |
| --- | --- | --- |
| Phase 0 — Setup | Complete | Flask/React scaffold, configuration, SQLite model |
| Phase 1 — Data | Complete | 50 source-attributed records across five publishers and a balanced 20-record accepted ground-truth set |
| Phase 2 — Backend | Complete | Analyze, alert-list/detail/delete APIs; structured LLM analysis; regex IoCs; SQLite persistence; 20 backend tests |
| Phase 3 — Frontend | Complete | Analyze, alert-list, and alert-detail routes; filters; CSV/JSON export; provider selector; CORS support |
| Phase 4 — Evaluation | Complete (initial run) | 20-document run, baselines, metrics report, and findings in `docs/evaluation_results.md` |
| Phase 5 — Final report/deployment | Pending | Final written report, presentation assets, human usefulness ratings, and optional deployment |

## Current implementation

- **Frontend:** React, Vite, Tailwind, `react-router-dom`, and Context + `useReducer`.
- **Backend:** Flask with Pydantic validation and CORS through `flask-cors`.
- **LLM layer:** LangChain structured-output chain with Gemini, Grok, Ollama, OpenRouter, and Claude provider adapters. The UI exposes Gemini, Grok, and Ollama; Gemini is the only provider live-verified end-to-end in the application UI.
- **Alert processing:** regex is the authoritative source for IP, CVE, hash, and domain extraction; the alert engine can only upgrade severity from the LLM result.
- **Storage:** SQLAlchemy with SQLite. A PostgreSQL migration remains a future scalability option.

## Initial evaluation outcome

The recorded 2026-07-30 run used OpenRouter with `google/gemma-4-26b-a4b-it:free` on all 20 held-out documents:

- Threat-type macro F1: **0.78** — target met.
- Severity macro F1: **0.58** — target not met.
- IoC F1: **1.00** — target met.
- p95 latency: **23.75 s** — target not met for this provider/model.
- Human summary ratings: **not yet collected**.

See `docs/evaluation_results.md` for the full tables, baseline comparison, and methodology notes. These results are specific to that provider/model and should not be presented as Gemini performance.

## Remaining work and known limitations

- Collect human usefulness ratings for the 20 generated summaries and regenerate the evaluation report with them.
- Perform a real-browser UI click-through before final sign-off.
- Prepare the final written report and presentation/poster assets.
- Deployment configuration is prepared for Render + Netlify, but no deployed URL is recorded.
- Production caching, retry/backoff, rate limiting, numeric confidence scoring, frontend automated tests, and persistent database storage are intentionally deferred MVP work.
