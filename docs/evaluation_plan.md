# Evaluation Plan

This document outlines how ThreatGPT will be evaluated for correctness, usefulness, and performance.

---

## Evaluation Overview

**Objective:** Measure the accuracy and utility of threat summarization and alert generation.

**Evaluation Set:** 20 manually annotated threat reports (curated from Phase 1 data collection).

**Metrics:** Classification accuracy, severity precision/recall/F1, IoC extraction quality, response latency, and human-rated usefulness.

---

## Test Dataset

### Dataset Composition

- **Total documents:** 20 real-world threat reports
- **Sources:** CISA, NVD, Google Threat Analysis Group, Microsoft Security, CERT/CC
- **Format:** Plain text, deduplicated, sanitized
- **Storage:** `data/annotations/labels.csv` — regenerated 2026-07-27, human-reviewed and accepted as ground truth (see Current Collection Status below)

### Current Collection Status (2026-07-27)

- **Starter corpus:** 50 public-source records from NVD, CISA, Google Threat Analysis Group, Microsoft Security, and CERT/CC
- **Provenance:** 50 source rows in `data/metadata.csv`
- **Draft annotations:** all 50 rows in `data/annotations/draft_labels.csv`, marked `needs-human-review` (separate scratch set, not used as evaluation ground truth on its own)
- **Selected evaluation set:** 20 balanced records in `data/annotations/labels.csv`, **regenerated and human-reviewed/accepted as ground truth on 2026-07-27**

**Regeneration (2026-07-27):** `labels.csv` was rebuilt from scratch as a selected subset of the now-comprehensive `draft_labels.csv` (all 50 raw documents), to fix an inconsistency: some rows previously carried richly-sourced IoCs while others carried only a bare CVE, and two rows (`cisa_001_lockbit.txt`, `cisa_008_iranian_apt.txt`) contained IoCs that did not actually appear in their corresponding `data/raw/*.txt` source text — ground truth asserting something no system could have derived from the given input. Both problem rows were dropped from the new selection rather than patched.

Every row now uses one uniform, deterministic method: `threat_type` from `data/metadata.csv`'s `category_hint`, `iocs` from a single regex pass (CVE/hash/IP/domain, matching `backend/preprocess.py`'s logic) run directly against the stored raw text, restricted to the four categories `data/README.md`'s schema actually documents (IPs, domains, hashes, CVEs — free-text malware/actor names added in an earlier pass were dropped for schema consistency).

The new balance is 3 vulnerability, 3 exploit, 3 malware, 3 phishing, 2 supply-chain, 2 ransomware, 2 DDoS, 2 APT (20 total) — the closest even split achievable given the corpus's per-category availability. 8 of 20 rows have an accurate empty `iocs` field (source extract genuinely contains no indicators); the other 12 have regex-verified CVEs, hashes, IPs, or domains.

**Human review of this regenerated selection is complete (2026-07-27).** Keep it held out from prompt or rule tuning during backend development.

8 of the 20 rows have an empty `iocs` field, accurately reflecting that their raw source extract contains no indicators: `cisa_025_solarwinds_supply_chain.txt`, `cisa_005_androxgh0st.txt`, `cisa_016_snake_malware.txt`, `cisa_017_emotet.txt`, `cisa_003_akira_ransomware.txt`, `microsoft_005_human_operated_ransomware.txt`, `cisa_007_volt_typhoon.txt`, `cisa_010_russian_military.txt`. Most of these are CISA advisory pages that return HTTP 403 to automated fetches (bot-blocked) and would need manual retrieval of the full advisory to populate further; the Microsoft record was independently confirmed to have no IoCs at the source.

### Ground Truth Annotation Schema

| Column        | Type   | Example                                              | Notes                                                                                         |
| ------------- | ------ | ---------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `filename`    | string | `cisa_001.txt`                                       | Reference to raw file in `data/raw/`                                                          |
| `threat_type` | enum   | `phishing`                                           | One of: phishing, ransomware, DDoS, APT, exploit, malware, vulnerability, supply-chain, other |
| `severity`    | enum   | `High`                                               | One of: Low, Medium, High, Critical                                                           |
| `iocs`        | CSV    | `192.168.1.1,malicious.com`                          | Comma-separated list (IPs, domains, CVE IDs, hashes)                                          |
| `summary`     | text   | "Sophisticated phishing targeting banking sector..." | 2–3 sentences, human-written                                                                  |

---

## Evaluation Metrics

### 1. Threat Type Classification

**Metric:** Multi-class accuracy, precision, recall, F1-score per class

**Calculation:**

```
Accuracy = (# correct threat_type) / (# total predictions)
Precision(phishing) = TP / (TP + FP)
Recall(phishing) = TP / (TP + FN)
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Target:** F1 > 0.80 across all threat types

**Why:** Models can be biased toward common threat types (phishing); per-class metrics reveal this.

---

### 2. Severity Classification

**Metric:** Multi-class accuracy, macro-average F1-score

**Calculation:**

```
Macro F1 = mean(F1_Low, F1_Medium, F1_High, F1_Critical)
```

**Target:** Macro F1 > 0.75

**Why:** Severity is imbalanced (fewer Critical-rated reports); macro-average prevents high-frequency class from masking poor performance on rare classes.

---

### 3. IoC Extraction Quality

**Metric:** Precision, recall, F1 at token level (exact match)

**Calculation:**

```
Precision = (# correctly extracted IoCs) / (# total extracted IoCs)
Recall = (# correctly extracted IoCs) / (# ground truth IoCs)
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Target:** F1 > 0.85 (strict exact match)

**Why:** IoCs are actionable; false positives (hallucinations) waste analyst time; false negatives miss threats.

---

### 4. Summary Usefulness (Human Rating)

**Metric:** Mean usefulness score (1–5 Likert scale)

**Procedure:**

- Have 3 human reviewers (team members) rate each summary independently:
  - 1 = Not useful, inaccurate, misleading
  - 2 = Somewhat useful, but lacks important details
  - 3 = Acceptable, captures key points
  - 4 = Good, actionable, minimal noise
  - 5 = Excellent, concise, actionable, complete
- Calculate inter-rater agreement (Cohen's kappa)
- Compute mean and std. dev. across reviewers

**Target:** Mean score ≥ 3.5, Cohen's kappa ≥ 0.60

**Why:** Ultimately, analysts judge usefulness; this captures it directly.

---

### 5. Response Latency

**Metric:** Mean, median, 95th percentile latency (milliseconds)

**Procedure:**

- Run 20 test documents through `/api/analyze`
- Record total time from request to response
- Breakdown: preprocessing, LLM API call, alert engine, database write

**Target:** Mean latency < 10 seconds, 95th percentile < 15 seconds

**Why:** Analysts expect real-time feedback; > 30s is unacceptable.

---

### 6. API Cost (if using paid LLM)

**Metric:** Mean cost per analyze request (USD)

**Calculation:**

```
Cost per request = (Total tokens / 1000) * (price per 1K tokens)
```

**Target:** < $0.10 per request (with caching)

**Why:** Operational cost matters for deployment; caching should reduce redundant calls.

---

## Baseline Comparisons

To demonstrate the value of LLM-assisted summarization, compare against simpler baselines:

### Baseline 1: Keyword-based Extraction

- Extract threat type and severity based on rule-based keyword lists
- Example: If text contains "ransomware" → threat_type = ransomware
- Severity: count of danger keywords (zero-day, exploit, active, etc.)
- **Expected accuracy:** ~60% (many reports use varied terminology)

### Baseline 2: Zero-shot LLM (no few-shot examples)

- Call LLM without prompt engineering, no structure constraints
- **Expected accuracy:** ~70% (LLM hallucinates without examples)

### Baseline 3: Simple Summarization (first N sentences)

- Take first 3 sentences of original report as "summary"
- **Expected human rating:** ~2.5/5 (incomplete, often off-topic)

---

## Ablation Study

To prove that specific components matter, run ablations:

### Ablation 1: Without Preprocessing

- Send raw text directly to LLM (skip preprocessing step)
- **Hypothesis:** Classification accuracy drops (more noise)
- **Expected impact:** ~5–10% F1 reduction

### Ablation 2: Without Rule-based Severity Boost

- Use only LLM severity, no keyword cross-check
- **Hypothesis:** Severity confidence decreases
- **Expected impact:** ~5% F1 reduction, more borderline cases

### Ablation 3: Without Prompt Constraints (free-text)

- Ask LLM to return free-text summary without JSON schema
- **Hypothesis:** More hallucinations, harder to parse
- **Expected impact:** ~15% accuracy reduction, 20% parsing errors

---

## Evaluation Timeline

| Phase   | Dates      | Activity                                               |
| ------- | ---------- | ------------------------------------------------------ |
| Phase 1 | Days 8–16  | Collect 50–100 docs, manually label 20                 |
| Phase 2 | Days 17–27 | Implement backend, test on validation set (informal)   |
| Phase 3 | Days 28–37 | Build frontend, integrate end-to-end                   |
| Phase 4 | Days 38–40 | **Formal evaluation**: run all metrics on 20 test docs |
| Phase 5 | Days 41–45 | Document results, compare baselines, write report      |

---

## Reporting Results

### Results Table Template

```markdown
## Classification Results

| Threat Type   | Precision | Recall   | F1-Score | Support |
| ------------- | --------- | -------- | -------- | ------- |
| Phishing      | 0.92      | 0.85     | 0.88     | 7       |
| Ransomware    | 0.88      | 0.80     | 0.84     | 5       |
| DDoS          | 0.75      | 0.67     | 0.71     | 3       |
| APT           | 0.90      | 1.00     | 0.95     | 2       |
| Exploit       | 0.83      | 0.71     | 0.77     | 3       |
| **Macro Avg** | **0.86**  | **0.81** | **0.83** | **20**  |

## Severity Classification

| Severity      | Precision | Recall   | F1-Score | Support |
| ------------- | --------- | -------- | -------- | ------- |
| Low           | 0.80      | 0.67     | 0.73     | 3       |
| Medium        | 0.85      | 0.85     | 0.85     | 7       |
| High          | 0.90      | 0.89     | 0.89     | 9       |
| Critical      | 1.00      | 1.00     | 1.00     | 1       |
| **Macro Avg** | **0.89**  | **0.85** | **0.87** | **20**  |

## IoC Extraction

- Precision: 0.91
- Recall: 0.88
- F1-Score: 0.89

## Summary Usefulness (Human Rating)

- Mean score: 4.1 / 5.0
- Std. dev: 0.6
- Cohen's kappa (inter-rater): 0.72

## Performance

- Mean latency: 7.8 seconds
- 95th percentile: 12.3 seconds
- Mean cost per request: $0.08

## Baselines

| Approach                         | Threat F1 | Severity F1 | IoC F1   |
| -------------------------------- | --------- | ----------- | -------- |
| Keyword-based                    | 0.58      | 0.52        | 0.65     |
| Zero-shot LLM                    | 0.71      | 0.68        | 0.78     |
| **ThreatGPT (few-shot + rules)** | **0.83**  | **0.87**    | **0.89** |
```

---

## How to Run Evaluation

1. **Prepare test set:**

   ```bash
   # Ensure 20 annotated examples in data/annotations/labels.csv
   # Corresponding raw files in data/raw/
   ```

2. **Run evaluation script** (to be created):

   ```bash
   cd backend
   python evaluate.py --test_set ../data/annotations/labels.csv --output results.json
   ```

3. **Generate report:**
   ```bash
   python report_metrics.py results.json > ../docs/evaluation_results.md
   ```

---

## Success Criteria (Course Deliverable)

- ✓ Classification F1 > 0.75 (acceptable for capstone)
- ✓ Severity F1 > 0.70
- ✓ IoC extraction F1 > 0.80
- ✓ Human rating ≥ 3.5/5
- ✓ Latency < 15 seconds
- ✓ Beat all baselines

---

## Future Work (Post-Course)

- Expand test set to 100+ documents for statistical significance
- Test on out-of-domain threat reports (e.g., from different sectors)
- User study with real security analysts
- Explore fine-tuning smaller models for cost reduction
- Add adversarial robustness testing (adversarial prompts, malformed input)
