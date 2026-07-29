"""Renders docs/evaluation_results.md from a results.json produced by
backend/evaluate.py. Run from the repo root:

    python -m backend.report_metrics results.json --output docs/evaluation_results.md
    # once human ratings exist:
    python -m backend.report_metrics results.json --output docs/evaluation_results.md --ratings docs/evaluation_ratings_filled.csv
"""
import argparse
import csv
import json
import statistics
from collections import defaultdict

from sklearn.metrics import cohen_kappa_score

# Success criteria from docs/evaluation_plan.md's "Success Criteria (Course
# Deliverable)" section -- the more lenient, binding targets, not the
# stricter per-metric targets stated earlier in that doc.
SUCCESS_CRITERIA = {
    "threat_type_f1": 0.75,
    "severity_f1": 0.70,
    "ioc_f1": 0.80,
    "human_rating": 3.5,
    "latency_p95_s": 15.0,
}


def _classification_table(metrics, title):
    lines = [f"## {title}", ""]
    lines.append("| Class | Precision | Recall | F1-Score | Support |")
    lines.append("| --- | --- | --- | --- | --- |")
    for label, m in sorted(metrics["per_class"].items()):
        lines.append(f"| {label} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} | {m['support']} |")
    macro = metrics["macro"]
    total_support = sum(m["support"] for m in metrics["per_class"].values())
    lines.append(
        f"| **Macro Avg** | **{macro['precision']:.2f}** | **{macro['recall']:.2f}** | "
        f"**{macro['f1']:.2f}** | **{total_support}** |"
    )
    lines.append("")
    lines.append(f"Accuracy: {metrics['accuracy']:.3f}")
    lines.append("")
    return lines


def compute_ratings_stats(ratings_csv_path):
    with open(ratings_csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    reviewer_cols = ["reviewer_1", "reviewer_2", "reviewer_3"]
    all_scores = []
    per_reviewer = defaultdict(list)
    for row in rows:
        for col in reviewer_cols:
            val = (row.get(col) or "").strip()
            if val:
                score = int(val)
                all_scores.append(score)
                per_reviewer[col].append(score)

    if not all_scores:
        return None

    mean = statistics.mean(all_scores)
    std = statistics.stdev(all_scores) if len(all_scores) > 1 else 0.0

    kappas = []
    filled_reviewers = [c for c in reviewer_cols if per_reviewer[c]]
    for i in range(len(filled_reviewers)):
        for j in range(i + 1, len(filled_reviewers)):
            a, b = filled_reviewers[i], filled_reviewers[j]
            paired = [
                (row[a], row[b])
                for row in rows
                if (row.get(a) or "").strip() and (row.get(b) or "").strip()
            ]
            if len(paired) >= 2:
                ya = [int(p[0]) for p in paired]
                yb = [int(p[1]) for p in paired]
                kappas.append(cohen_kappa_score(ya, yb))

    return {
        "mean": mean,
        "std": std,
        "kappa_mean": statistics.mean(kappas) if kappas else None,
        "n_ratings": len(all_scores),
    }


def render_markdown(results, ratings_stats):
    lines = ["# ThreatGPT Evaluation Results", ""]
    meta = results["run_meta"]
    lines.append(
        f"Run: {meta['timestamp']} — provider `{meta['provider']}`, model `{meta['model']}`, "
        f"{meta['n_docs']} documents from `data/annotations/labels.csv`."
    )
    lines.append("")

    m = results["metrics"]

    if m["threat_type"]:
        lines += _classification_table(m["threat_type"], "Classification Results")
    if m["severity"]:
        lines += _classification_table(m["severity"], "Severity Classification")

    lines.append("## IoC Extraction")
    lines.append("")
    ioc = m["iocs"]
    lines.append(f"- Precision: {ioc['precision']:.2f}")
    lines.append(f"- Recall: {ioc['recall']:.2f}")
    lines.append(f"- F1-Score: {ioc['f1']:.2f}")
    lines.append("")

    lines.append("## Summary Usefulness (Human Rating)")
    lines.append("")
    if ratings_stats:
        lines.append(f"- Mean score: {ratings_stats['mean']:.1f} / 5.0")
        lines.append(f"- Std. dev: {ratings_stats['std']:.2f}")
        if ratings_stats["kappa_mean"] is not None:
            lines.append(f"- Cohen's kappa (mean pairwise): {ratings_stats['kappa_mean']:.2f}")
        lines.append(f"- Based on {ratings_stats['n_ratings']} individual ratings")
    else:
        lines.append(
            "**Not yet measured** — awaiting human ratings. Fill in "
            "`docs/evaluation_ratings_template.csv` and re-run with `--ratings <file>`."
        )
    lines.append("")

    lines.append("## Performance")
    lines.append("")
    lat = m["latency"]
    if lat["mean_ms"] is not None:
        lines.append(f"- Mean latency: {lat['mean_ms']/1000:.2f} seconds")
        lines.append(f"- Median latency: {lat['median_ms']/1000:.2f} seconds")
        lines.append(f"- 95th percentile: {lat['p95_ms']/1000:.2f} seconds")
    if m["cost"]["mean_usd_est"] is not None:
        lines.append(f"- Mean estimated cost per request: ${m['cost']['mean_usd_est']:.5f} (estimate, not metered)")
    lines.append(f"- Successful requests: {m['n_ok']}, errors: {m['n_error']}")
    lines.append("")

    baselines = results.get("baselines") or {}
    if baselines:
        lines.append("## Baselines")
        lines.append("")
        lines.append("| Approach | Threat F1 (macro) | Severity F1 (macro) | IoC F1 |")
        lines.append("| --- | --- | --- | --- |")
        threat_f1 = m["threat_type"]["macro"]["f1"] if m["threat_type"] else None
        sev_f1 = m["severity"]["macro"]["f1"] if m["severity"] else None
        lines.append(
            f"| **ThreatGPT (few-shot + rules)** | **{threat_f1:.2f}** | **{sev_f1:.2f}** | **{ioc['f1']:.2f}** |"
        )
        if "keyword" in baselines:
            kb = baselines["keyword"]["metrics"]
            lines.append(f"| Keyword-based | {kb['threat_type']['macro']['f1']:.2f} | {kb['severity']['macro']['f1']:.2f} | — |")
        if "zero_shot_llm" in baselines and baselines["zero_shot_llm"]["metrics"]:
            zb = baselines["zero_shot_llm"]["metrics"]
            pf_rate = baselines["zero_shot_llm"].get("parse_failure_rate")
            note = f" (parse failure rate: {pf_rate:.0%})" if pf_rate else ""
            lines.append(f"| Zero-shot LLM{note} | {zb['threat_type']['macro']['f1']:.2f} | {zb['severity']['macro']['f1']:.2f} | — |")
        lines.append("")
        lines.append(
            "IoC F1 is not computed for the keyword or zero-shot baselines — neither is designed "
            "to extract IoCs (ThreatGPT's IoC extraction is regex-based, not an LLM capability being "
            "compared here)."
        )
        lines.append("")
        if "first_n_sentences" in baselines:
            lines.append(
                "Baseline 3 (first-N-sentences) produces summaries only, not threat_type/severity "
                "classifications, so it is not included in the table above. See `results.json` for "
                "its raw output per document."
            )
            lines.append("")

    lines.append("## Success Criteria")
    lines.append("")
    lines.append("| Criterion | Target | Actual | Met? |")
    lines.append("| --- | --- | --- | --- |")
    if m["threat_type"]:
        v = m["threat_type"]["macro"]["f1"]
        lines.append(f"| Threat-type macro F1 | > {SUCCESS_CRITERIA['threat_type_f1']} | {v:.2f} | {'Yes' if v > SUCCESS_CRITERIA['threat_type_f1'] else 'No'} |")
    if m["severity"]:
        v = m["severity"]["macro"]["f1"]
        lines.append(f"| Severity macro F1 | > {SUCCESS_CRITERIA['severity_f1']} | {v:.2f} | {'Yes' if v > SUCCESS_CRITERIA['severity_f1'] else 'No'} |")
    v = ioc["f1"]
    lines.append(f"| IoC extraction F1 | > {SUCCESS_CRITERIA['ioc_f1']} | {v:.2f} | {'Yes' if v > SUCCESS_CRITERIA['ioc_f1'] else 'No'} |")
    if ratings_stats:
        v = ratings_stats["mean"]
        lines.append(f"| Human rating | >= {SUCCESS_CRITERIA['human_rating']} | {v:.1f} | {'Yes' if v >= SUCCESS_CRITERIA['human_rating'] else 'No'} |")
    else:
        lines.append(f"| Human rating | >= {SUCCESS_CRITERIA['human_rating']} | not measured | N/A |")
    if lat["p95_ms"] is not None:
        v = lat["p95_ms"] / 1000
        lines.append(f"| Latency (p95) | < {SUCCESS_CRITERIA['latency_p95_s']}s | {v:.2f}s | {'Yes' if v < SUCCESS_CRITERIA['latency_p95_s'] else 'No'} |")
    beat_baselines = None
    if m["threat_type"] and "keyword" in baselines:
        beat_baselines = m["threat_type"]["macro"]["f1"] > baselines["keyword"]["metrics"]["threat_type"]["macro"]["f1"]
        if "zero_shot_llm" in baselines and baselines["zero_shot_llm"]["metrics"]:
            beat_baselines = beat_baselines and (
                m["threat_type"]["macro"]["f1"] > baselines["zero_shot_llm"]["metrics"]["threat_type"]["macro"]["f1"]
            )
    if beat_baselines is not None:
        lines.append(f"| Beat all baselines (threat F1) | — | — | {'Yes' if beat_baselines else 'No'} |")
    lines.append("")

    lines.append("## Methodology Notes")
    lines.append("")
    lines.append(
        "- Input text has `Source:`/`Source URL:` provenance lines stripped before submission, "
        "matching how `data/annotations/labels.csv`'s ground-truth IoCs were built — otherwise "
        "every document would be unfairly penalized for the publisher's own domain (e.g. "
        "`www.cisa.gov`) scoring as a false-positive IoC."
    )
    lines.append(
        "- `backend/preprocess.py` was fixed during this evaluation to also match bracket-defanged "
        "IoCs (e.g. `pro-swapper[.]com`), a real system capability gap found via 3 documents in the "
        "test set — a genuine product fix, not evaluation-specific tuning."
    )
    lines.append(
        "- Cost figures are estimates (character-count/4 token heuristic × published per-token "
        "pricing), not metered usage."
    )
    lines.append(
        "- The evaluation runs against an isolated, temporary SQLite database — it never touches "
        "`data/threatgpt.db`."
    )
    lines.append(
        "- Ablation studies (docs/evaluation_plan.md) were deliberately deferred as a stretch item, "
        "consistent with this project's MVP-first pattern."
    )
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results_json")
    parser.add_argument("--output", default="docs/evaluation_results.md")
    parser.add_argument("--ratings", default=None, help="path to a filled-in ratings CSV; omit if not yet collected")
    args = parser.parse_args()

    with open(args.results_json, encoding="utf-8") as f:
        results = json.load(f)

    ratings_stats = compute_ratings_stats(args.ratings) if args.ratings else None

    markdown = render_markdown(results, ratings_stats)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
