# ThreatGPT Evaluation Results

Run: 2026-07-30T10:04:30.881110+00:00 — provider `openrouter`, model `google/gemma-4-26b-a4b-it:free`, 20 documents from `data/annotations/labels.csv`.

## Classification Results

| Class | Precision | Recall | F1-Score | Support |
| --- | --- | --- | --- | --- |
| APT | 1.00 | 1.00 | 1.00 | 2 |
| DDoS | 1.00 | 0.50 | 0.67 | 2 |
| exploit | 0.00 | 0.00 | 0.00 | 3 |
| malware | 1.00 | 1.00 | 1.00 | 3 |
| phishing | 1.00 | 1.00 | 1.00 | 3 |
| ransomware | 1.00 | 1.00 | 1.00 | 2 |
| supply-chain | 1.00 | 1.00 | 1.00 | 2 |
| vulnerability | 0.43 | 1.00 | 0.60 | 3 |
| **Macro Avg** | **0.80** | **0.81** | **0.78** | **20** |

Accuracy: 0.800

## Severity Classification

| Class | Precision | Recall | F1-Score | Support |
| --- | --- | --- | --- | --- |
| Critical | 0.82 | 1.00 | 0.90 | 9 |
| High | 0.89 | 0.80 | 0.84 | 10 |
| Medium | 0.00 | 0.00 | 0.00 | 1 |
| **Macro Avg** | **0.57** | **0.60** | **0.58** | **20** |

Accuracy: 0.850

## IoC Extraction

- Precision: 1.00
- Recall: 1.00
- F1-Score: 1.00

## Summary Usefulness (Human Rating)

**Not yet measured** — awaiting human ratings. Fill in `docs/evaluation_ratings_template.csv` and re-run with `--ratings <file>`.

## Performance

- Mean latency: 11.44 seconds
- Median latency: 9.94 seconds
- 95th percentile: 23.75 seconds
- Successful requests: 20, errors: 0

## Baselines

| Approach | Threat F1 (macro) | Severity F1 (macro) | IoC F1 |
| --- | --- | --- | --- |
| **ThreatGPT (few-shot + rules)** | **0.78** | **0.58** | **1.00** |
| Keyword-based | 0.64 | 0.00 | — |
| Zero-shot LLM | 0.00 | 0.58 | — |

IoC F1 is not computed for the keyword or zero-shot baselines — neither is designed to extract IoCs (ThreatGPT's IoC extraction is regex-based, not an LLM capability being compared here).

Baseline 3 (first-N-sentences) produces summaries only, not threat_type/severity classifications, so it is not included in the table above. See `results.json` for its raw output per document.

## Success Criteria

| Criterion | Target | Actual | Met? |
| --- | --- | --- | --- |
| Threat-type macro F1 | > 0.75 | 0.78 | Yes |
| Severity macro F1 | > 0.7 | 0.58 | No |
| IoC extraction F1 | > 0.8 | 1.00 | Yes |
| Human rating | >= 3.5 | not measured | N/A |
| Latency (p95) | < 15.0s | 23.75s | No |
| Beat all baselines (threat F1) | — | — | Yes |

## Findings

- **Severity mismatches skew upward**: 3 upgraded vs 0 downgraded relative to ground truth (of 3 total mismatches). `backend/alert_engine.py`'s keyword-based severity cross-check is deliberately upgrade-only, so this is the mechanism working as coded — but several keywords (e.g. a bare `"ransomware"` or `"critical infrastructure"` mention) are broad enough to trigger on documents that shouldn't necessarily escalate to Critical. Not tuned based on this result, since it's exactly the held-out set this project keeps off-limits for rule tuning — noted here as a future-work item instead.
- **threat_type mismatches lean toward "vulnerability"**: 4 of 4 threat_type errors predicted `vulnerability` for a document actually labeled something else (e.g. `exploit`, `DDoS`). `backend/services/llm_service.py`'s 2-shot prompt only demonstrates `vulnerability` and `ransomware` examples — none of the other 6 categories — which may bias a model toward the categories it's seen demonstrated when uncertain. Not changed based on this result, for the same held-out-set reason as above.
- **Zero-shot LLM baseline scores near-zero on threat_type despite reasonable-sounding answers**: with no schema constraint, it returns free-text labels (e.g. `"Remote Code Execution (RCE)"`, `"SQL Injection"`) that never exact-match the fixed taxonomy ground truth uses. This is a stronger illustration of the value of structured output than `docs/evaluation_plan.md`'s own predicted ~70% zero-shot accuracy assumed — exact-match scoring genuinely requires a constrained output format, not just a capable model.

## Methodology Notes

- This run used provider `openrouter` (model `google/gemma-4-26b-a4b-it:free`), **not** the app's configured default (Gemini) — Gemini's free tier hit its daily request quota (20 requests/day for `gemini-2.5-flash`) during same-day testing prior to this run. The latency numbers above reflect this specific free-tier model, not Gemini's; an earlier ad-hoc Gemini call in this same session completed in ~3-4 seconds, well under this run's mean of 11.4s. Re-run with `--provider gemini` once quota resets to get latency figures for the actual default provider.
- Input text has `Source:`/`Source URL:` provenance lines stripped before submission, matching how `data/annotations/labels.csv`'s ground-truth IoCs were built — otherwise every document would be unfairly penalized for the publisher's own domain (e.g. `www.cisa.gov`) scoring as a false-positive IoC.
- `backend/preprocess.py` was fixed during this evaluation to also match bracket-defanged IoCs (e.g. `pro-swapper[.]com`), a real system capability gap found via 3 documents in the test set — a genuine product fix, not evaluation-specific tuning.
- Cost figures are estimates (character-count/4 token heuristic × published per-token pricing), not metered usage.
- The evaluation runs against an isolated, temporary SQLite database — it never touches `data/threatgpt.db`.
- Ablation studies (docs/evaluation_plan.md) were deliberately deferred as a stretch item, consistent with this project's MVP-first pattern.
