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
**Outcome:** Easy to implement and test.  
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
| spaCy model download large (~50MB)    | Make optional, fail gracefully if missing     | Medium    |
| SQLite locks under concurrent load    | Switch to PostgreSQL if > 20 concurrent users | Low (MVP) |

---

## Performance Metrics (to be updated)

As you run the system, record:

- Average latency per analyze request
- LLM API cost per call
- Database query time (alerts list, filter)
- Frontend page load time
- Classification accuracy on test set

Example:

```
Date: 2026-07-23
Metric: Average latency (n=10 requests)
Value: 8.2 seconds
Notes: Includes LLM API roundtrip (~6s), preprocessing (~0.5s), DB write (~0.1s)
```

---

## Refactoring Candidates

- [ ] Extract LLMService into a separate module with pluggable backends (OpenAI, Gemini, local)
- [ ] Add database session pooling for concurrent requests
- [ ] Migrate tests to pytest with fixtures for mocking LLM API
- [ ] Add frontend unit tests with React Testing Library

---

## References

- [spaCy NER documentation](https://spacy.io/usage/information-extraction)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat/create)
- [Flask best practices](https://flask.palletsprojects.com/en/latest/)
- [React Context API](https://react.dev/reference/react/createContext)
