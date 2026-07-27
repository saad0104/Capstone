# ThreatGPT (Capstone)

A reproducible scaffold and development tracker for the ThreatGPT capstone project: an LLM-assisted Cyber Threat Intelligence summarization and alert-generation system.

Repository layout

- `backend/` — Flask API, preprocessing, LLM service, models, schemas
- `frontend/` — React + Tailwind UI (Vite)
- `data/` — raw and processed threat documents and annotations
- `docs/` — architecture diagrams, literature notes, final report assets

Quick start (local)

1. Create Python venv and install dependencies:

```bash
cd /home/saad/Capstone
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Start the backend (development):

```bash
source .venv/bin/activate
cd backend
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host 0.0.0.0 --port 5000
```

3. Start the frontend (development):

```bash
cd /home/saad/Capstone/frontend
npm install
npm run dev
# open http://localhost:5173
```

Configuration

- Copy `.env.example` to `.env` and fill in API keys and DB path.

Development workflow

- Work on feature branches (`feature/<name>`) and open small PRs to `main`.
- Use the `backend/` tests with `pytest` and add frontend checks as needed.
- Keep `requirements.txt` and `frontend/package.json` updated when adding deps.

## Updates & Tracking

Use this section to record short, structured progress updates. Add one entry per update and commit the change so the project history reflects progress.

Entry format (copy this template for each update):

```
Date: YYYY-MM-DD
Author: Your name
Area: backend | frontend | data | docs
Summary: Short description of what was done (1-2 lines)
Files: list of files changed or added
Status: in-progress | done | blocked
Notes: optional details, blockers, or next steps
```

Example entry:

```
Date: 2026-07-23
Author: Saad
Area: setup
Summary: Scaffolded repo, created venv, started backend and frontend dev servers.
Files: README.md, backend/app.py, frontend/src/App.jsx
Status: done
Notes: Backend running at http://127.0.0.1:5000, frontend at http://localhost:5173
```

Changelog and Progress Log

- Keep a running `docs/CHANGELOG.md` for major milestones and releases.
- For day-to-day tracking, add short updates directly to this file under an "Updates" header and commit frequently.

Release checklist (course deliverable)

- Final code pushed to GitHub `main` branch
- Deployed demo URL (backend + frontend)
- 20 annotated test documents in `data/annotations`
- Final report in `docs/` and presentation poster file

Where to record issues and tasks

- Use GitHub Issues for feature requests and bugs.
- Use the built-in project todo list (managed by the development assistant) for highlevel milestones.

Contact

- Supervisor: Associate Professor Rezaul Karim
- Team: Student A (backend), Student B (frontend), Student C (data/devops)

--
Update Log

2026-07-23 — Repo scaffolded and Phase 0 complete. (Saad)

Date: 2026-07-27
Author: Saad / Codex
Area: data | docs
Summary: Created a verified Phase 1 starter corpus of ten public NVD vulnerability records, with provenance and draft annotations.
Files: data/raw/nvd_*.txt, data/metadata.csv, data/annotations/draft_labels.csv, data/README.md, docs/*.md
Status: in-progress
Notes: All raw files resolve from metadata. The draft annotations need human review, and the corpus needs campaign-level CISA/CTI reports before selecting the 20-document evaluation set.

Date: 2026-07-27
Author: Saad / Codex
Area: data | docs
Summary: Added ten source-attributed CISA campaign-advisory extracts and completed draft labels for the 20-record starter corpus.
Files: data/raw/cisa_*.txt, data/metadata.csv, data/annotations/draft_labels.csv, data/README.md, docs/CHANGELOG.md, docs/evaluation_plan.md
Status: in-progress
Notes: The corpus now covers vulnerability, supply-chain, ransomware, malware, and APT material. Draft labels are not accepted ground truth; human review is the next required action.

Date: 2026-07-27
Author: Saad / Codex
Area: data | docs
Summary: Expanded the public-source corpus to 25 records with CISA material on phishing, active exploitation, DoS, and software supply-chain risk.
Files: data/raw/cisa_011_*.txt through data/raw/cisa_015_*.txt, data/metadata.csv, data/README.md, docs/CHANGELOG.md, docs/evaluation_plan.md
Status: in-progress
Notes: The five new files are source-attributed extracts and await draft labeling and human review.

Date: 2026-07-27
Author: Saad / Codex
Area: data | docs
Summary: Expanded the corpus to 35 records with an additional category-focused CISA batch.
Files: data/raw/cisa_016_*.txt through data/raw/cisa_025_*.txt, data/metadata.csv, data/README.md, docs/CHANGELOG.md, docs/evaluation_plan.md
Status: in-progress
Notes: The added batch strengthens phishing, malware, DDoS/DoS, exploit, and supply-chain representation. The new records await draft labels and human review.

Date: 2026-07-27
Author: Saad / Codex
Area: data | docs
Summary: Reached the 50-record Phase 1 collection target by adding source-attributed reports from Google Threat Analysis Group, Microsoft Security, and CERT/CC.
Files: data/raw/google_*.txt, data/raw/microsoft_*.txt, data/raw/cert_*.txt, data/metadata.csv, data/README.md, docs/CHANGELOG.md, docs/evaluation_plan.md
Status: in-progress
Notes: The corpus now has five distinct publishers. The 15 added records await draft labeling and human review before they can be considered for evaluation ground truth.

Date: 2026-07-27
Author: Saad
Area: data
Summary: Completed human review of the 20-record evaluation set in data/annotations/labels.csv. It is now accepted as ground truth for formal evaluation.
Files: data/annotations/labels.csv, docs/CHANGELOG.md, docs/evaluation_plan.md, data/README.md
Status: done
Notes: data/annotations/draft_labels.csv (the broader NVD/CISA starter batch) remains unreviewed and separate; it is not part of the accepted evaluation set. Next step: begin Phase 2 backend implementation.

Date: 2026-07-27
Author: Saad / Claude
Area: data
Summary: Expanded data/annotations/draft_labels.csv to cover all 50 raw documents (was 20), then regenerated data/annotations/labels.csv from scratch as a balanced 20-record subset of it, fixing an inconsistency where some records had richly-sourced IoCs and others had only a bare CVE (or, in two cases, CVEs not actually present in the raw source text).
Files: data/annotations/draft_labels.csv, data/annotations/labels.csv, data/README.md, docs/CHANGELOG.md, docs/evaluation_plan.md
Status: done
Notes: labels.csv dropped cisa_001_lockbit.txt and cisa_008_iranian_apt.txt (unsupported IoCs) in favor of cleaner records. Human review of the regenerated labels.csv is complete and it is accepted as ground truth. Next step: Phase 2 backend implementation.

Date: 2026-07-27
Author: Saad
Area: data | docs
Summary: Phase 1 (data collection) declared complete. Exit criteria met: 50 raw documents across 5 publishers, 20 balanced human-reviewed labeled records in data/annotations/labels.csv.
Files: docs/implementation_notes.md, README.md
Status: done
Notes: draft_labels.csv's other 30 rows remain unreviewed scratch data, not required for Phase 1 exit. Next: Phase 2 — backend implementation (/api/analyze, /api/alerts, real LLM service call, DB wiring).
