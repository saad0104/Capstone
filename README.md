# ThreatGPT

LLM-assisted Cyber Threat Intelligence summarization and alert-generation system.

## Repository Layout

- `backend/` — Flask API, preprocessing, LLM service, models, schemas
- `frontend/` — React + Tailwind UI (Vite)
- `data/` — raw and processed threat documents and annotations
- `docs/` — architecture, evaluation results, deployment guide

## Quick Start

1. Create Python venv and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Start the backend (run from repo root — `backend` is a Python package):
```bash
export FLASK_APP=backend.app:create_app
export FLASK_ENV=development
flask run --host 0.0.0.0 --port 5000
```

3. Start the frontend:
```bash
cd frontend
npm install
npm run dev
# open http://localhost:5173
```

## Configuration

Copy `.env.example` to `.env` and add your LLM API keys.

## Status

- **Phase 1:** 50 source-attributed CTI records, 20-record human-reviewed evaluation set ✓
- **Phase 2:** Flask API with multi-provider LLM pipeline, regex IoC extraction, SQLite ✓
- **Phase 3:** React dashboard (Analyze, Alerts List, Alert Detail), filters, CSV/JSON export ✓
- **Phase 4:** Evaluation complete — see `docs/evaluation_results.md`

See `docs/architecture.md` for system design and `docs/deployment.md` for production setup.