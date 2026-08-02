# Implementation Notes

This document tracks design decisions, trade-offs, and lessons learned throughout the ThreatGPT development.

---

## Decision Log

### Decision Template

```
Date: YYYY-MM-DD
Area: backend | frontend | data | devops
Title: <short title>
Context: Why this decision was needed
Option A: <description>
Option B: <description>
Decision: <chosen option + rationale>
Outcome: <what happened>
Impact: <consequences (positive/negative)>
```

---

## Decisions

### 1. Database Choice: SQLite vs PostgreSQL

**Date:** 2026-07-23  
**Area:** backend  
**Title:** SQLite for MVP, upgrade path to PostgreSQL  
**Context:** Need a lightweight database for the course project with option to scale later.

**Options:**

- **A: SQLite** — Zero setup, file-based, sufficient for MVP (50–100 alerts)
- **B: PostgreSQL** — Full-featured, requires external DB, better for production scale

**Decision:** SQLite for Phase 0–4 (course deadline). Migration path to PostgreSQL defined but deferred.  
**Rationale:** Faster development velocity, no infrastructure overhead, local testing simpler.  
**Outcome:** Backend tests pass, local deployment works immediately.  
**Impact:** Later migration requires schema migration script; doable but requires care.

---

### 2. LLM Prompt Strategy: Few-shot vs Chain-of-Thought

**Date:** 2026-07-23  
**Area:** backend  
**Title:** Structured JSON output with 2-shot examples  
**Context:** LLM hallucination risk if output is free-text; need deterministic, machine-parseable alerts.

**Options:**

- **A: Chain-of-Thought (CoT)** — Ask LLM to explain reasoning, then extract fields
- **B: Structured JSON with 2-shot examples** — Provide examples of desired JSON format, force compliance

**Decision:** Option B (2-shot examples + JSON schema in prompt).  
**Rationale:** Faster inference, lower cost, more reliable parsing, easier validation.  
**Outcome:** LLM returns valid JSON ~95% of the time; invalid responses fallback to error handling.  
**Impact:** Reduced hallucination but requires careful prompt engineering iteration (expect 5–6 revisions).

---

### 3. Preprocessing: Regex vs NER (spaCy/Transformers)

**Date:** 2026-07-23  
**Area:** backend  
**Title:** Hybrid: Regex IoC extraction + optional spaCy for entity recognition  
**Context:** Need to extract threat indicators (IPs, domains, CVEs) efficiently.

**Options:**

- **A: Pure regex** — Fast, deterministic, brittle
- **B: spaCy NER** — More accurate, slower, requires model download
- **C: Hybrid** — Regex for well-defined patterns (IP, CVE), spaCy optional for advanced NER

**Decision:** Option C (hybrid approach).  
**Rationale:** Regex handles the 80% of cases (IPs, CVEs, hashes are fixed patterns). spaCy optional for future organization/person entity extraction.  
**Outcome:** Preprocessing runs in <100ms, high precision on IoC extraction.  
**Impact:** Balanced accuracy vs speed; easily extensible.

---

### 4. Frontend State Management: React Context vs Redux

**Date:** 2026-07-23  
**Area:** frontend  
**Title:** React hooks + Context API (no Redux)  
**Context:** Need to manage alert list, filters, and pagination state.

**Options:**

- **A: React Context + useReducer** — Lightweight, built-in
- **B: Redux** — Powerful, but overkill for a simple CRUD app
- **C: Zustand / Jotai** — Minimal boilerplate

**Decision:** Option A (Context API + hooks).  
**Rationale:** MVP doesn't need Redux complexity; Context sufficient for alert + filter state.  
**Outcome:** Simpler codebase, fewer dependencies, faster iteration.  
**Impact:** May need refactor if app grows; Redux migration path exists.

---

### 5. API Rate Limiting: Token bucket vs Leaky bucket

**Date:** 2026-07-23  
**Area:** backend  
**Title:** Simple rate limit decorator (requests per minute)  
**Context:** Prevent abuse of `/api/analyze` endpoint due to LLM API costs.

**Options:**

- **A: Token bucket** — Flexible, industry standard
- **B: Leaky bucket** — FIFO queue, fair distribution
- **C: Simple request count per minute** — Easy to implement, sufficient for MVP

**Decision:** Option C (simple per-minute limit, 10 requests/min per IP).  
**Rationale:** MVP doesn't need distributed rate limiting; simple decorator works.  
**Outcome:** Not yet implemented as of the Phase 2 backend build (2026-07-28) — deliberately deferred as a stretch item so it didn't block getting `/api/analyze` working end-to-end. Left as `# TODO(stretch)` in `backend/app.py`.  
**Impact:** Scales poorly if deployed to multiple servers; should upgrade to Redis-backed rate limiting for production.

---

### 6. Phase 1 Dataset: Provenance-first starter corpus

**Date:** 2026-07-27  
**Area:** data  
**Title:** Use public NVD records for the initial reproducible corpus
**Context:** The project needs raw CTI documents with traceable provenance before backend analysis and formal evaluation can begin.

**Options:**

- **A: Unattributed copied reports** — quick to collect but difficult to verify or reproduce
- **B: Public, authoritative source records with retained metadata** — slightly slower, but traceable and suitable for a report

**Decision:** Option B. Ten public NVD records were saved as plain text with a corresponding entry in `data/metadata.csv`.
**Rationale:** The NVD provides stable CVE identifiers, publication dates, severity data, and official source URLs. It is a safe starting point for the preprocessing pipeline.
**Outcome:** Ten raw documents and ten reviewable draft labels are available. A validation check confirmed that every metadata filename exists in `data/raw/`.
**Impact:** The current batch is heavily weighted toward vulnerabilities, so it cannot serve as the final 20-document evaluation set without adding diverse CISA and other public CTI reports. Draft labels remain separate from `labels.csv` until human review.

---

### 7. Phase 2 Backend Framework: Flask vs FastAPI

**Date:** 2026-07-28  
**Area:** backend  
**Title:** Keep Flask for Phase 2, defer FastAPI  
**Context:** Only `/health` existed on the Flask skeleton going into Phase 2; a request came in to consider switching to FastAPI (async, native Pydantic integration, auto-generated OpenAPI docs).

**Options:**

- **A: Migrate to FastAPI** — nothing real to migrate yet since only `/health` existed, so the switch would be cheap now and expensive later
- **B: Keep Flask** — build `/api/analyze` etc. on the existing skeleton, revisit the framework later if needed

**Decision:** Option B.  
**Rationale:** Avoid stacking a framework migration on top of the first real backend implementation in the same pass; keep the change surface minimal for MVP.  
**Outcome:** `backend/app.py` now has `/api/analyze`, `/api/alerts` (list/detail/delete) on Flask, with manual Pydantic validation (no native request/response integration like FastAPI would provide). 18 passing tests, live-verified against a real Gemini call.  
**Impact:** Pydantic validation in Flask is more boilerplate than FastAPI would need (manual `model_validate` + `ValidationError` handling per route). A FastAPI migration remains straightforward later since Pydantic schemas are already the validation layer.

---

### 8. LLM Orchestration: LangChain vs LangGraph, and multi-provider support

**Date:** 2026-07-28  
**Area:** backend  
**Title:** LangChain-only chain (not LangGraph), provider registry for Gemini/Grok/Ollama  
**Context:** The placeholder `LLMService.summarize()` just truncated text to 280 characters and never called a real LLM. Needed a real implementation, plus a request to support multiple LLM providers (Gemini, Grok, local Ollama) rather than hardcoding one.

**Options:**

- **A: Full LangGraph agent workflow** — multi-node graph with conditional routing; more powerful, more moving parts to debug for a capstone deadline
- **B: LangChain only** — a single `prompt | chat_model | PydanticOutputParser` chain (LCEL), matching the already-decided 2-shot structured-JSON prompt strategy (decision #2 above)
- **Provider selection — A: per-request frontend selector now** vs **B: single configurable default via `LLM_PROVIDER` env var, registry pattern so a selector is a small future addition**

**Decision:** LangChain only (Option B), and a provider registry with a single active provider via `.env` (Option B on provider selection).  
**Rationale:** MVP-first — a full agent graph isn't needed for a single-call structured-extraction task, and per-request provider switching has no UI to expose it yet (frontend is Phase 3). The registry pattern (`PROVIDER_REGISTRY` dict of factory functions in `backend/services/llm_service.py`) means adding the frontend selector later is a small addition, not a rewrite.  
**Outcome:** `backend/services/llm_service.py` rewritten around `LLMAnalysis` (Pydantic schema: summary/threat_type/severity/recommended_action — deliberately *not* `ioc_list`, since IoCs stay exclusively regex-derived per decision #4). `_build_gemini`/`_build_grok`/`_build_ollama` factory functions; Grok reuses `langchain_openai.ChatOpenAI` with a custom `base_url` since its API is OpenAI-compatible, avoiding a separate SDK. `get_llm_service()` is a lazy singleton so a missing API key doesn't crash `flask run` or pytest collection at import time. Live-verified against a real Gemini key.  
**Impact:** Only the Gemini path has been tested against a live provider; Grok and Ollama are implemented on the same pattern but unverified. Default Gemini model name required a fix mid-session (`gemini-1.5-flash` had been retired; corrected to `gemini-2.5-flash` after checking `ListModels` against the actual key).

---

### 9. Preprocessing NLP Dependency: nltk replaces spaCy

**Date:** 2026-07-28  
**Area:** backend  
**Title:** Swap the unused `spacy` dependency for `nltk`  
**Context:** `requirements.txt` listed `spacy` since Phase 0, but nothing in `backend/` ever imported it — `preprocess.py` was always pure regex. A request came in to use `nltk` instead.

**Decision:** Removed `spacy` from `requirements.txt`, added `nltk`. Regex in `preprocess.py` remains the sole, authoritative IoC extractor (per decision #3's hybrid-preprocessing rationale) — nltk is staged for future tokenization/sentence-splitting needs, not wired into any pipeline step yet.  
**Rationale:** Neither library was actually in use, so this was a low-risk swap; keeping regex authoritative matters because it's the same extraction method the Phase 1 evaluation ground-truth CSVs were built with — changing it would silently invalidate that ground truth.  
**Outcome:** `nltk` installed, unused. No behavior change to `extract_iocs()`.  
**Impact:** None yet. Revisit when there's a concrete need (e.g., chunking long reports before the LLM call).

---

### 10. Phase 3 Frontend Routing: react-router-dom vs state-based view switch

**Date:** 2026-07-29  
**Area:** frontend  
**Title:** Real routes over a lightweight state switch  
**Context:** The frontend scaffold had no routing at all — `App.jsx` was a single placeholder view. Needed to decide how to navigate between Analyze/Alerts List/Alert Detail.

**Options:**

- **A: `react-router-dom`** — real URLs (`/`, `/alerts`, `/alerts/:id`), deep-linkable/shareable, adds one dependency
- **B: State-based view switch** — no new dependency, matches the minimal-dependency approach used for the backend, but no bookmarkable alert URLs

**Decision:** Option A.  
**Rationale:** A dashboard where individual alerts can't be linked to is a real UX gap for an analyst workflow; the dependency cost is low for a well-established, actively-maintained library already compatible with React 18.  
**Outcome:** `AlertDetailPage` reads `:id` via `useParams()`, falls back to a direct `getAlert(id)` fetch when the alert isn't already in the Alerts Context (covers deep-linking).  
**Impact:** None negative observed; one more dependency in `package.json`.

---

### 11. Frontend LLM Provider Selector

**Date:** 2026-07-29  
**Area:** frontend, backend  
**Title:** Expose Gemini/Grok/Ollama selection in the UI, labeled honestly  
**Context:** `LLMService.__init__` was built in decision #8 specifically so a per-request provider could be added later without a rewrite. A request came in to actually add it to the frontend now.

**Decision:** Added `AnalyzeRequest.provider: Optional[str] = None`; `app.py`'s `analyze()` constructs `LLMService(provider=...)` directly when supplied (catching unknown-provider `ValueError` as a 400, distinct from a 502 provider failure). Frontend `ProviderSelector` shows all three options but visibly badges Grok and Ollama as "unverified" (tooltip: implemented but never live-verified end-to-end) rather than hiding them or presenting them as equally reliable to Gemini.  
**Rationale:** Decision #8 already logged that only Gemini had been live-verified — surfacing Grok/Ollama without that caveat would mislead a user into thinking all three are equally trustworthy.  
**Outcome:** Live-verified: the default/Gemini path works end-to-end from the browser; an unknown provider name correctly returns 400, not 502.  
**Impact:** Grok/Ollama remain untested against real credentials/a local instance — this doc still doesn't claim otherwise.

---

### 12. CORS: flask-cors vs dev-only Vite proxy

**Date:** 2026-07-29  
**Area:** backend  
**Title:** flask-cors with an env-configurable allowlist  
**Context:** No CORS handling existed anywhere in the backend. `docs/architecture.md` already commits to separate production hosting origins (frontend on Vercel/Netlify, backend on Render/Railway), so this needed a fix that works in both dev and prod, not just locally.

**Options:**

- **A: Vite dev-server proxy** — simplest for local dev, but solves nothing for the documented separate-origin production deployment
- **B: `flask-cors`, allowed origins from a `CORS_ORIGINS` env var** — one mechanism for both dev and prod

**Decision:** Option B.  
**Rationale:** A dev-only fix that has to be redone differently at deploy time isn't actually solving the problem the architecture doc already committed to.  
**Outcome:** `CORS(app, origins=[...])` read from `CORS_ORIGINS` (default `http://localhost:5173`) inside `create_app()`. Live-verified: `Access-Control-Allow-Origin` header present on real responses when called with a `localhost:5173` `Origin` header.  
**Impact:** Deploying to prod requires setting `CORS_ORIGINS` to the real frontend URL — documented in `docs/architecture.md`'s Deployment Model section so it isn't missed later.

---

### 13. Phase 4 Evaluation: fixed held-out set and provider-specific reporting

**Date:** 2026-07-30  
**Area:** data | backend | evaluation  
**Title:** Evaluate against the accepted 20-record set without tuning on it
**Context:** The project required a formal, reproducible measurement of the implemented pipeline and baseline comparisons.

**Decision:** Use `data/annotations/labels.csv` as a held-out 20-record ground-truth set; run the system through an isolated temporary SQLite database; report the provider and model with every result. The initial run used OpenRouter with `google/gemma-4-26b-a4b-it:free`.
**Rationale:** Provider quality and latency vary materially, so an evaluation result is not a universal claim about all configured providers. Keeping the evaluation database isolated also prevents test alerts from polluting normal application data.
**Outcome:** The initial run completed 20/20 requests: threat-type macro F1 0.78, severity macro F1 0.58, IoC F1 1.00, and p95 latency 23.75 seconds. Human usefulness ratings remain outstanding.
**Impact:** Threat-type and IoC targets were met, while severity and latency were not. Severity rules and prompts must not be tuned on this held-out set; any later comparison should use a different provider or a separate development set.

---

## Lessons Learned

### Phase 0 (Setup)

- ✓ Scaffolding early saves time later (folders, .env, README templates)
- ✓ Virtual environment isolation prevents dependency conflicts
- ⚠ Forgot to create `/data` folder initially; created later

### Phase 1 (Data collection, complete 2026-07-27)

- ✓ Preserve source URL and collection metadata alongside every raw document.
- ✓ Keep draft labels separate from accepted ground truth to prevent accidental evaluation leakage.
- ✓ Ground truth `iocs` must only assert what's actually present in the corresponding raw `.txt` — an earlier pass had CVEs in `labels.csv` that didn't appear anywhere in the raw source text, which a system could never correctly reproduce from that input. Audit for this before accepting a labeled set.
- ✓ Extract IoCs with one deterministic, uniform method (regex, matching `backend/preprocess.py`) across every record rather than mixing manual/fetched enrichment for some rows and nothing for others — inconsistent methodology was the root cause of the CVE issue above.
- ⚠ A page-summarizing fetch tool is unreliable for verbatim data like file hashes; `curl` the raw HTML and verify matches by surrounding context instead.
- Exit criteria met: 50 raw documents across 5 publishers (target 50–100), 20 balanced, human-reviewed labeled records in `data/annotations/labels.csv` (target 20).

### Phase 2 (Backend, complete 2026-07-28)

- ✓ `AlertOut.model_validate()` on a raw ORM object fails if a stored field's shape doesn't match the response schema (e.g. `ioc_list` stored as a dict, exposed as `List[str]`) — validation runs before any post-processing code gets a chance to reshape it. Flatten/reshape into a plain dict first, then construct the Pydantic model from that.
- ✓ Pydantic v2's `ValidationError.errors()` can include non-JSON-serializable objects in `ctx` for custom validator errors — call it with `include_context=False` before passing to `jsonify`, or a clean 400 becomes an opaque 500.
- ⚠ Always check a provider's model catalog (e.g. `ListModels`) against the actual API key before hardcoding a default model name — `gemini-1.5-flash` was already retired by the time this was built.
- ⚠ A real secret briefly ended up in `.env.example` (git-tracked) instead of `.env` (gitignored) by human error. Caught before any commit via `git log --all -p`, but the lesson stands: always verify a secret's destination file is actually gitignored, don't assume from the filename.

### Phase 3 (Frontend, complete 2026-07-29)

- ⚠ **`postcss.config.cjs` never existed**, even though `tailwindcss`/`autoprefixer` were in `package.json` since Phase 0 — so `@tailwind`/`@apply` directives were being shipped to the browser as literal unprocessed text the entire time. Nothing caught this earlier because the original placeholder `App.jsx` only used a couple of utility classes that happened to not visibly break anything. Caught by inspecting the actual built CSS output size/content, not by trusting that `vite build` exiting successfully meant the output was correct.
- ✓ Separate frontend/backend origins (even just `:5173` vs `:5000` in local dev) need CORS solved deliberately — see decision #12. Don't discover this only when a deploy happens.
- ⚠ No real browser was used to verify the UI — verification was production build success, dev-server module-transform checks (catches syntax/import errors), and full backend API verification with real CORS headers. Actual rendered layout/interactivity/visual correctness still needs a human to click through it.

### Prompt Engineering (in progress)

- _Document all prompt iterations_ — version control prompt templates, measure accuracy per version
- _Use few-shot examples_ — Include 2–3 examples of desired input/output in prompt
- _Test with diverse inputs_ — Real threat reports vary widely; test on edge cases early

### Database

- _Schema matters early_ — Define Alert table fields carefully before building APIs
- _Index planning_ — Consider (threat_type, severity, created_at) composite index for filtering

### Frontend

- _Component reuse_ — Build Alert card once, reuse in list and detail view
- _Loading states_ — Always show spinner while API call in progress
- _Error handling_ — User-friendly error messages, not raw stack traces

---

## Known Issues & Workarounds

| Issue                                 | Workaround                                    | Priority  |
| ------------------------------------- | --------------------------------------------- | --------- |
| LLM API response time > 30s sometimes | Add timeout + fallback response               | High      |
| NLTK is installed but unused          | Keep regex authoritative until a concrete NLP need exists | Low |
| SQLite locks under concurrent load    | Switch to PostgreSQL if > 20 concurrent users | Low (MVP) |
| Free-tier LLM quotas can interrupt large runs | Use evaluator pacing/retry or run after quota reset | Medium |

---

## Performance Metrics

As you run the system, record:

- Average latency per analyze request
- LLM API cost per call
- Database query time (alerts list, filter)
- Frontend page load time
- Classification accuracy on test set

Initial formal run (2026-07-30, OpenRouter / `google/gemma-4-26b-a4b-it:free`, n=20):

- Threat-type macro F1: 0.78
- Severity macro F1: 0.58
- IoC F1: 1.00
- Mean latency: 11.44 seconds; p95: 23.75 seconds
- Human usefulness ratings: pending

See `docs/evaluation_results.md` for per-class metrics, baselines, findings,
and methodology. These figures are provider/model-specific.

---

## Refactoring Candidates

- [x] Extract LLMService into a separate module with pluggable backends (OpenAI, Gemini, local) — done 2026-07-28, see decision #8; `PROVIDER_REGISTRY` in `backend/services/llm_service.py` (Gemini/Grok/Ollama, not OpenAI directly)
- [ ] Add database session pooling for concurrent requests
- [x] Migrate tests to pytest with fixtures for mocking LLM API — done 2026-07-28, `backend/tests/` with a `mock_llm` fixture, 18 passing tests
- [ ] Add frontend unit tests with React Testing Library

---

## References

- [LangChain LCEL / structured output](https://python.langchain.com/docs/concepts/lcel/)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [nltk documentation](https://www.nltk.org/) (staged, not yet wired into preprocessing)
- [Flask best practices](https://flask.palletsprojects.com/en/latest/)
- [React Context API](https://react.dev/reference/react/createContext)
