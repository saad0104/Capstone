# Changelog

All notable changes to this project will be documented in this file.

Format

- Date: YYYY-MM-DD — Short description (Author)
- Follow semantic-style headings: Added, Changed, Fixed, Removed, Security

## Unreleased

### Added

- Phase 1 starter corpus of ten public NVD records in `data/raw/`
- Ten source-attributed CISA campaign-advisory extracts covering ransomware, malware, and APT activity
- Five additional CISA extracts covering phishing, active exploitation, DoS, and software supply-chain risk
- Ten additional CISA records focused on phishing, malware, DDoS/DoS, exploit activity, and supply-chain compromise
- Fifteen records from Google Threat Analysis Group, Microsoft Security, and CERT/CC, bringing the Phase 1 corpus to 50 documents
- A balanced 20-record evaluation selection in `data/annotations/labels.csv`
- Evaluation harnesses (`backend/evaluate.py`, `backend/report_metrics.py`) and the initial 20-document results report
- `data/metadata.csv` with a source URL, publication date, collection date, and category hint for every starter record
- `data/annotations/draft_labels.csv` with reviewable seed labels and summaries
- Draft labels for all 50 corpus documents

### Changed

- Documented the dataset provenance and the separation between draft labels and accepted evaluation ground truth
- Updated the project documentation to reflect the completed initial evaluation and the full five-provider backend registry

### Notes

- The 50-document starter corpus spans vulnerability, supply-chain, ransomware, malware, phishing, exploit, DDoS, and APT material across five publishers (NVD, CISA, Google TAG, Microsoft, CERT/CC).
- `data/annotations/draft_labels.csv` covers the wider 50-document corpus and remains separate from the accepted ground-truth set.
- The initial Phase 4 run is complete; see `docs/evaluation_results.md`. Phase 5 final-report work, human usefulness ratings, browser acceptance testing, and optional deployment remain.

## 2026-08-02 — Documentation synchronized with implemented project (Saad / Codex)

Changed:

- Reconciled the architecture, data guide, deployment runbook, evaluation plan, implementation notes, README, and status summary with the current code and the initial Phase 4 evaluation.
- Documented the full backend provider registry (Gemini, Grok, Ollama, OpenRouter, and Claude), while retaining the UI’s three-provider selector scope.
- Replaced stale future-tense Phase 4 and success-criteria statements with the measured provider-specific results and outstanding work.

## 2026-07-29 — Phase 3 frontend implemented (Saad / Claude)

Added:

- `frontend/src/api/client.js` — fetch wrapper with a typed `ApiError` (status/errorCode/details) distinct from plain network failures, and `analyze`/`listAlerts`/`getAlert`/`deleteAlert` functions.
- `frontend/src/context/AlertsContext.jsx` — Context + `useReducer` alert list/filter state (per the project's own decision #4 in `docs/implementation_notes.md`), with `ADD_ALERT`/`REMOVE_ALERT` actions so Analyze/Detail pages update the list without a refetch.
- Three routed pages via `react-router-dom`: `AnalyzePage` ("/"), `AlertsListPage` ("/alerts"), `AlertDetailPage` ("/alerts/:id").
- `ProviderSelector` — Gemini/Grok/Ollama radio selector on the Analyze page, with Grok/Ollama visibly badged "unverified" rather than presented as equally reliable to Gemini.
- `ErrorPanel` — one shared component rendering distinct messaging for 400 (invalid input), 502 (LLM/provider failure), 404 (not found), and plain network failure.
- CSV export of the filtered alerts list (`utils/csvExport.js`) and JSON export of a single alert (`utils/jsonExport.js`), both client-side, no new backend endpoints.
- Dark SOC-dashboard theme: `tailwind.config.cjs` extended with `severity-*` and `surface-*` color tokens and a monospace font stack for IoCs/technical values; `darkMode: "class"` with `class="dark"` on `<html>`.
- `frontend/.env.example` (`VITE_API_BASE_URL`).
- Backend: `AnalyzeRequest.provider: Optional[str]`, threaded through `app.py`'s `analyze()` into `LLMService(provider=...)` when supplied; unknown provider name now correctly returns 400, not 502.
- Backend: CORS via `flask-cors`, allowed origins from a new `CORS_ORIGINS` env var (default `http://localhost:5173`), read inside `create_app()` so tests/different deploys each get their own config.
- 2 new backend tests covering the explicit-provider path and unknown-provider 400 (20 total, all passing).

Fixed:

- `postcss.config.cjs` never existed in the repo, even though `tailwindcss`/`autoprefixer` were installed since Phase 0 — Tailwind was never actually running, and `@tailwind`/`@apply` directives were being shipped to the browser as literal unprocessed text. Caught by inspecting the built CSS output size/content directly rather than trusting a successful `vite build` exit code.

Notes:

- Verified: production build succeeds; every new module transforms cleanly through the Vite dev server (no syntax/import errors); full `/api/analyze` → `/api/alerts` list → detail → delete flow confirmed against the live backend with real `Origin` headers proving CORS actually works.
- **Not verified: an actual browser click-through.** No browser automation tool was available this session — layout, interactivity, and visual correctness of the theme still need a human pass before Phase 3 is fully signed off.
- Frontend automated tests (Vitest/React Testing Library) deliberately deferred, same MVP-scope tradeoff already applied to the backend rate limiter.

## 2026-07-28 — Phase 2 backend implemented (Saad / Claude)

Added:

- `POST /api/analyze`, `GET /api/alerts`, `GET /api/alerts/<id>`, `DELETE /api/alerts/<id>` on `backend/app.py`, alongside the existing `/health`.
- `backend/db.py` — SQLAlchemy engine/scoped-session setup against `DATABASE_URL`, robust absolute-path SQLite fallback.
- `backend/alert_engine.py` — the "Alert Engine" step from `docs/architecture.md`: regex IoC dedup/validation, and a keyword-based severity cross-check that can only upgrade the LLM's severity call, never downgrade it.
- `backend/services/llm_service.py` rewritten around LangChain (`prompt | chat_model | PydanticOutputParser`, 2-shot structured-JSON prompt) with a provider registry supporting Gemini, Grok (xAI, via the OpenAI-compatible `ChatOpenAI` wrapper), and local Ollama, selected via `LLM_PROVIDER`.
- `backend/tests/` — 18 pytest tests (preprocess regression, alert engine, `/api/analyze`, `/api/alerts`), LLM mocked so no live API key is needed to run them.
- `backend/__init__.py`, `backend/services/__init__.py`, `backend/tests/__init__.py` — `backend` is now a proper Python package (needed for relative imports and `from backend.app import create_app`-style test imports).

Changed:

- `backend/schemas.py` — `AlertOut` fields given explicit `None` defaults and `created_at` added (required under Pydantic v2 semantics, which don't default `Optional` fields to `None` the way v1 did); `AnalyzeRequest.text` gets a blank-input validator.
- `requirements.txt` — removed `spacy` (confirmed unused since Phase 0), added `langchain`, `langchain-core`, `langchain-openai`, `langchain-google-genai`, `langchain-ollama`, `nltk`.
- `.env.example` — replaced `OPENAI_API_KEY` with `LLM_PROVIDER`, `GEMINI_API_KEY`/`GEMINI_MODEL`, `XAI_API_KEY`/`XAI_MODEL`/`XAI_BASE_URL`, `OLLAMA_BASE_URL`/`OLLAMA_MODEL`.
- `README.md` Quick Start — backend now runs as `flask --app backend.app:create_app run` from the repo root, not `cd backend; flask run`, since `backend` is a package with relative imports now.

Fixed:

- `_serialize()` in `app.py` originally called `AlertOut.model_validate()` directly on the ORM object before flattening `ioc_list` from its stored dict shape to the API's `List[str]` contract — Pydantic validated the raw dict against `List[str]` and crashed before the flattening code ever ran. Fixed by building the flattened dict first, then constructing `AlertOut` from it.
- Blank-input requests returned 500 instead of 400 — Pydantic's `ValidationError.errors()` included a non-JSON-serializable exception object in `ctx` for the custom blank-text validator. Fixed with `e.errors(include_url=False, include_context=False)`.
- Default Gemini model name (`gemini-1.5-flash`) had been retired by the provider; corrected to `gemini-2.5-flash` after checking `ListModels` against the actual configured API key.
- A real API key was briefly committed to the working tree in `.env.example` (git-tracked) instead of `.env` (gitignored) by mistake; moved to `.env` and cleared from `.env.example` before any commit — confirmed via `git log --all -p` that it never entered git history.

Notes:

- Grok and Ollama providers are implemented on the same registry pattern as Gemini but have not been tested against a real key or local instance.
- Rate limiting on `/api/analyze` remains a deliberately deferred stretch item (decision logged in `docs/implementation_notes.md`), not implemented.
- `docs/architecture.md` and `docs/implementation_notes.md` updated to match what's actually built (LangChain/provider registry instead of the originally documented plain OpenAI/Gemini client; Flask retained over FastAPI; nltk replacing the never-used spaCy dependency).

## 2026-07-27 — Evaluation label set reviewed and accepted (Saad)

Changed:

- Completed human review of the 20-record balanced evaluation selection in `data/annotations/labels.csv`; it is now accepted as ground truth for formal evaluation (Phase 4).

Notes:

- `data/annotations/draft_labels.csv` remains separate and unreviewed; it was not used as the source for the accepted labels.
- Next milestone: Phase 2 backend implementation (`/api/analyze`, `/api/alerts`, real LLM service call, DB wiring).

## 2026-07-27 — IoC completeness pass on evaluation labels (Saad / Claude)

Added:

- Real IoCs (domains, IPs, malware/tool names, file hashes) sourced from original advisory pages for 3 previously IoC-empty evaluation records: `google_001_youtube_cookie_theft.txt`, `google_002_apt42_phishing.txt`, `microsoft_001_spoofed_domains.txt`. Added to both `data/annotations/labels.csv` and as an appendix in the corresponding `data/raw/*.txt` files.
- File hashes (25 total, SHA256) verified by fetching raw HTML directly with `curl` and checking each hash's surrounding context — avoids the transcription-error risk of the LLM-summarizing fetch tool.
- Threat actor name `Storm-1747` added for `microsoft_001_spoofed_domains.txt`, found only via the raw-HTML pass, missed by the initial summarized fetch.

Fixed:

- A raw-HTML regex pass over `microsoft_001`'s page also matched 7 non-IoC hex strings (6 WordPress CSS cache-busting `?ver=` values, 1 Microsoft Threat Intel actor-profile URL slug). Verified by context and excluded — not malware hashes.

Notes:

- 7 CISA-sourced records remain IoC-empty; their source pages are bot-blocked (HTTP 403) and the Wayback Machine is unreachable from this environment. Need manual retrieval. See `docs/evaluation_plan.md` for the full list.
- `microsoft_005_human_operated_ransomware.txt` confirmed to have no IoCs in its source; empty field is accurate.

## 2026-07-27 — draft_labels.csv regenerated for all 50 raw documents (Saad / Claude)

Changed:

- Rebuilt `data/annotations/draft_labels.csv` from scratch, covering all 50 records in `data/raw/` (previously only the 20-document NVD/CISA starter batch). `threat_type` now comes from `data/metadata.csv`'s `category_hint`; `iocs` is populated by a single deterministic regex pass (CVE/hash/IP/domain) run directly against each raw file's stored text, matching `backend/preprocess.py`'s extraction logic — replacing the earlier inconsistency where some records carried only a CVE and others carried richer, inconsistently-sourced indicator lists.
- New category balance across the 50 drafts: 11 phishing, 9 vulnerability, 7 exploit, 6 malware, 5 ransomware, 5 DDoS, 4 APT, 3 supply-chain.

Fixed:

- Excluded the `Source URL:` metadata line from domain extraction — an earlier pass was incorrectly picking up the publisher's own domain (e.g. `www.cisa.gov`, `nvd.nist.gov`) as a false-positive IoC.
- Kept CVE/hash/IP extraction scoped to the full document (not just body text) after an intermediate version wrongly stripped the `CVE:` metadata line, zeroing out all 10 NVD records' IoCs.

Notes:

- 20 of 50 rows have non-empty `iocs`; the other 30 (mostly CISA advisory extracts) genuinely contain no indicators in the stored raw text, so an empty field there is accurate, not missing.
- `severity` values are draft judgment calls (not text-derived, except NVD's explicit `NVD severity:` field) and still need human review, same as every other field in this file.
- This file remains separate from and does not affect `data/annotations/labels.csv`'s accepted-ground-truth status.

## 2026-07-27 — labels.csv regenerated from draft_labels.csv for consistency (Saad / Claude)

Changed:

- Rebuilt `data/annotations/labels.csv` from scratch as a balanced 20-record subset of the now-comprehensive `data/annotations/draft_labels.csv`, reusing its `threat_type`/`severity`/`iocs`/`summary` values directly rather than re-deriving them, so both files now agree by construction.
- Dropped free-text malware/actor names (e.g. `RedLine`, `Storm-1747`) that a previous pass had added to 3 rows' `iocs` — `data/README.md`'s own schema documents `iocs` as IPs/domains/hashes/CVEs only, so this restores schema consistency.
- New category balance: 3 vulnerability, 3 exploit, 3 malware, 3 phishing, 2 supply-chain, 2 ransomware, 2 DDoS, 2 APT (20 total) — the most even split achievable given per-category availability in the 50-document corpus.

Removed:

- `cisa_001_lockbit.txt` and `cisa_008_iranian_apt.txt` are no longer in the selected evaluation set. Both had `iocs` entries not actually present in their raw source text (flagged in an audit this session); rather than trim or enrich them, they were simply excluded and replaced by cleaner records (`cisa_003`/`microsoft_005` for ransomware, `cisa_007`/`cisa_010` for APT).

Notes:

- 8 of the 20 rows have an accurate empty `iocs` field; the other 12 carry regex-verified CVEs/hashes/IPs/domains extracted directly from `data/raw/*.txt`.

## 2026-07-27 — labels.csv regenerated selection reviewed and accepted (Saad)

Changed:

- Human review of the regenerated `data/annotations/labels.csv` (see entry above) is complete; it is accepted as ground truth for evaluation. The prior sign-off on the old row set does not apply here — this is an independent review of the new content.

## 2026-07-23 — Initial scaffold and Phase 0 completion (Saad)

Added:

- Repository scaffold (`backend/`, `frontend/`, `data/`, `docs/`)
- Minimal Flask app and placeholder LLM service (`backend/app.py`, `backend/services/llm_service.py`)
- SQLAlchemy `Alert` model (`backend/models.py`)
- Preprocessing utilities (`backend/preprocess.py`)
- Minimal React frontend scaffold (Vite + Tailwind) in `frontend/`
- `README.md` with tracking template and initial update

Notes:

- Backend running at http://127.0.0.1:5000
- Frontend dev server running at http://localhost:5173

--
