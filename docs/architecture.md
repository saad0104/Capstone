# ThreatGPT System Architecture

## Overview

ThreatGPT is an end-to-end LLM-assisted pipeline for cyber threat intelligence (CTI) summarization and alert generation. The system ingests raw threat reports, processes them through a preprocessing pipeline, uses an LLM to extract and structure threat information, applies rule-based severity refinement, and stores results in a searchable database. A web dashboard allows analysts to review, filter, and export alerts.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           User Interface                         │
│                     (React + Tailwind Dashboard)                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Analyze    │  │  Alerts Log  │  │  Alert View  │          │
│  │    Page      │  │   & Filter   │  │  & Export    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬──────────────────────────────────┘
                             │ HTTP / REST API
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
│  │  │ 2. Text Preprocessing (spaCy + Regex)              ││  │
│  │  │    - Remove HTML, normalize whitespace              ││  │
│  │  │    - Tokenization, sentence splitting               ││  │
│  │  │    - Extract IoCs: IPs, CVEs, domains, hashes       ││  │
│  │  └─────────────────────────────────────────────────────┘│  │
│  │                         ▼                                │  │
│  │  ┌─────────────────────────────────────────────────────┐│  │
│  │  │ 3. LLM Service (OpenAI / Google Gemini API)         ││  │
│  │  │    - Apply prompt template (structured output)      ││  │
│  │  │    - Retry logic + exponential backoff              ││  │
│  │  │    - Response caching (prevent duplicate calls)     ││  │
│  │  │    - Return: {summary, threat_type, severity, ..}  ││  │
│  │  └─────────────────────────────────────────────────────┘│  │
│  │                         ▼                                │  │
│  │  ┌─────────────────────────────────────────────────────┐│  │
│  │  │ 4. Alert Engine (Validation & Enrichment)           ││  │
│  │  │    - Validate JSON structure                        ││  │
│  │  │    - Cross-check severity with keyword signals      ││  │
│  │  │    - Add metadata: UUID, timestamp, processing_ms   ││  │
│  │  │    - Apply confidence scoring                       ││  │
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

1. **User inputs raw threat text** → dashboard textarea or file upload
2. **API receives request** → `/api/analyze` endpoint validates and processes
3. **Preprocessing stage** → normalizes text, extracts IoCs with regex
4. **LLM call** → sends structured prompt to external API (Gemini/GPT)
5. **Alert enrichment** → validates output, applies severity rules, adds metadata
6. **Persistence** → stores complete alert in SQLite database
7. **Response** → returns structured JSON to frontend
8. **Display** → dashboard renders alert with badges, IoC list, export options

---

## Component Responsibilities

| Component            | Technology              | Responsibility                                             |
| -------------------- | ----------------------- | ---------------------------------------------------------- |
| **Frontend**         | React + Vite + Tailwind | UI for threat submission, alert viewing, filtering, export |
| **API Server**       | Flask + Werkzeug        | HTTP endpoint routing, request/response handling           |
| **Input Validation** | Pydantic                | Schema validation, error handling                          |
| **Preprocessing**    | spaCy + Regex           | Text normalization, IoC extraction                         |
| **LLM Service**      | OpenAI / Google Gemini  | LLM API client, prompt templating, retry logic             |
| **Alert Engine**     | Custom Python           | Validation, severity refinement, metadata enrichment       |
| **Database**         | SQLAlchemy + SQLite     | Alert persistence, schema management                       |

---

## Key Design Decisions

1. **LLM as a service** — External API (not local model) for cost-effectiveness and accuracy
2. **Hybrid severity scoring** — Combine LLM output with keyword-based confidence signals
3. **Structured JSON output** — Force LLM to return deterministic schema (not free-text)
4. **Rule-based preprocessing** — Fast regex-based IoC extraction before LLM (reduces hallucination)
5. **Caching** — Avoid redundant API calls for identical inputs
6. **SQLite for MVP** — Lightweight, no external DB required; can upgrade to PostgreSQL later

---

## Deployment Model

- **Backend** — Render / Railway / Heroku (Flask app + SQLite DB)
- **Frontend** — Vercel / Netlify (static build + React bundle)
- **LLM API** — Paid service (OpenAI or Google Cloud)
- **Infrastructure** — Minimal, cost-effective (no serverless complexity)

---

## Performance Targets

- **Latency**: Average response time < 10 seconds per analyze request
- **Throughput**: Handle 10–20 concurrent requests
- **Cost**: < $0.10 per analyze call (depends on LLM pricing tier)
- **Accuracy**: Threat-type classification F1 > 0.80 on test set
