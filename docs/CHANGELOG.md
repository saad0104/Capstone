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
- `data/metadata.csv` with a source URL, publication date, collection date, and category hint for every starter record
- `data/annotations/draft_labels.csv` with reviewable seed labels and summaries
- Draft labels for every document in the 20-record starter corpus

### Changed

- Documented the dataset provenance and the separation between draft labels and accepted evaluation ground truth

### Notes

- The 50-document starter corpus spans vulnerability, supply-chain, ransomware, malware, phishing, exploit, DDoS, and APT material across five publishers (NVD, CISA, Google TAG, Microsoft, CERT/CC).
- `data/annotations/draft_labels.csv` (the broader NVD/CISA starter batch) remains unreviewed and is not accepted ground truth.

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
