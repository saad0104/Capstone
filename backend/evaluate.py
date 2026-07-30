"""Phase 4 formal evaluation harness. Run from the repo root:

    python -m backend.evaluate --test_set data/annotations/labels.csv --output results.json

See docs/evaluation_plan.md for the full methodology.
"""
import argparse
import csv
import json
import os
import statistics
import tempfile
import time
from datetime import datetime, timezone

# DATABASE_URL must be set BEFORE any backend.app/backend.db import, so the
# evaluation run never touches the shared dev DB at data/threatgpt.db.
_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="threatgpt_eval_")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

import numpy as np  # noqa: E402
from sklearn.metrics import accuracy_score, precision_recall_fscore_support  # noqa: E402

from backend.app import create_app  # noqa: E402
from backend.db import engine  # noqa: E402
from backend.models import Base  # noqa: E402
from backend import eval_utils  # noqa: E402
from backend import baselines  # noqa: E402


def load_ground_truth(test_set_path):
    with open(test_set_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _post_with_rate_limit_retry(client, payload, max_retries=2, backoff_s=35):
    """The free tier of several LLM providers (e.g. Gemini's free tier: 5
    requests/minute) can be exceeded by this harness's own back-to-back calls
    across 20 documents. A 429/RESOURCE_EXHAUSTED surfaces from our API as a
    502 llm_failure. This is a rate-limit artifact of running many evaluation
    calls quickly, not a real system defect -- retry with a fixed backoff
    rather than either failing the record or (wrongly) adding general
    retry/backoff to the production LLM service, which architecture.md
    deliberately documents as not yet implemented.

    Returns (response, latency_ms) where latency_ms times only the final
    attempt's actual request, excluding backoff sleep time, so retries don't
    pollute the reported latency distribution."""
    for attempt in range(max_retries + 1):
        t0 = time.time()
        resp = client.post("/api/analyze", json=payload)
        latency_ms = (time.time() - t0) * 1000
        if resp.status_code != 502:
            return resp, latency_ms
        body = resp.get_json() or {}
        if "RESOURCE_EXHAUSTED" not in str(body.get("details", "")):
            return resp, latency_ms
        if attempt < max_retries:
            print(f"    rate limited, waiting {backoff_s}s before retry {attempt + 1}/{max_retries}...")
            time.sleep(backoff_s)
    return resp, latency_ms


def run_main_system(client, rows, raw_dir, provider, pace_seconds=0):
    records = []
    for i, row in enumerate(rows):
        if pace_seconds and i > 0:
            time.sleep(pace_seconds)

        text = eval_utils.load_document(row["filename"], raw_dir)
        payload = {"text": text}
        if provider:
            payload["provider"] = provider

        resp, latency_ms = _post_with_rate_limit_retry(client, payload)

        gt_iocs = eval_utils.parse_ground_truth_iocs(row["iocs"])

        if resp.status_code != 201:
            records.append(
                {
                    "filename": row["filename"],
                    "status": "error",
                    "http_status": resp.status_code,
                    "error_body": resp.get_json(),
                    "ground_truth": {
                        "threat_type": row["threat_type"],
                        "severity": row["severity"],
                        "iocs": sorted(gt_iocs),
                    },
                    "latency_ms": latency_ms,
                }
            )
            continue

        body = resp.get_json()
        predicted_iocs = set(body.get("ioc_list") or [])
        resolved_provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        cost = eval_utils.estimate_cost_usd(
            text, json.dumps(body), resolved_provider, _current_model(resolved_provider)
        )

        records.append(
            {
                "filename": row["filename"],
                "status": "ok",
                "alert_id": body.get("id"),
                "predicted": {
                    "threat_type": body.get("threat_type"),
                    "severity": body.get("severity"),
                    "iocs": sorted(predicted_iocs),
                    "summary": body.get("summary"),
                    "recommended_action": body.get("recommended_action"),
                },
                "ground_truth": {
                    "threat_type": row["threat_type"],
                    "severity": row["severity"],
                    "iocs": sorted(gt_iocs),
                },
                "latency_ms": latency_ms,
                "processing_ms": body.get("processing_ms"),
                "cost_usd_est": cost,
            }
        )
    return records


def _current_model(provider=None):
    """Resolves the model name for the actually-active provider. Must accept
    an explicit provider (from --provider / a per-call override), not just
    read LLM_PROVIDER from the environment -- otherwise a CLI override (e.g.
    --provider openrouter) silently gets the wrong provider's model name."""
    provider = provider or os.getenv("LLM_PROVIDER", "gemini")
    if provider == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if provider == "grok":
        return os.getenv("XAI_MODEL", "grok-2-latest")
    if provider == "openrouter":
        return os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
    return os.getenv("OLLAMA_MODEL", "llama3.1")


def run_keyword_baseline_all(rows, raw_dir):
    records = []
    for row in rows:
        text = eval_utils.load_document(row["filename"], raw_dir)
        pred = baselines.run_keyword_baseline(text)
        records.append(
            {
                "filename": row["filename"],
                "predicted": pred,
                "ground_truth": {"threat_type": row["threat_type"], "severity": row["severity"]},
            }
        )
    return records


def run_zero_shot_baseline_all(rows, raw_dir, provider, pace_seconds=0):
    provider = provider or os.getenv("LLM_PROVIDER", "gemini")
    records = []
    for i, row in enumerate(rows):
        if pace_seconds and i > 0:
            time.sleep(pace_seconds)

        text = eval_utils.load_document(row["filename"], raw_dir)
        t0 = time.time()
        pred = baselines.run_zero_shot_llm_baseline(text, provider)
        latency_ms = (time.time() - t0) * 1000
        cost = eval_utils.estimate_cost_usd(text, pred.get("raw_output") or "", provider, _current_model(provider))
        records.append(
            {
                "filename": row["filename"],
                "predicted": pred,
                "ground_truth": {"threat_type": row["threat_type"], "severity": row["severity"]},
                "latency_ms": latency_ms,
                "cost_usd_est": cost,
            }
        )
    return records


def run_first_n_sentences_all(rows, raw_dir):
    records = []
    for row in rows:
        text = eval_utils.load_document(row["filename"], raw_dir)
        summary = baselines.run_first_n_sentences_baseline(text)
        records.append({"filename": row["filename"], "summary": summary})
    return records


def _classification_metrics(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    per_class = {
        labels[i]: {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
        }
        for i in range(len(labels))
    }
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    return {
        "per_class": per_class,
        "macro": {"precision": float(macro_p), "recall": float(macro_r), "f1": float(macro_f1)},
        "accuracy": float(accuracy_score(y_true, y_pred)),
    }


def _ioc_prf(records):
    """IoC quality is a per-document *set* comparison, not a single-label
    classification -- sklearn's classification metrics don't fit free-form
    string-set comparison without an artificial fixed vocabulary. Compute
    precision/recall/F1 by micro-aggregating TP/FP/FN across all documents'
    predicted-vs-ground-truth IoC sets instead."""
    tp = fp = fn = 0
    for r in records:
        if r.get("status") != "ok":
            continue
        predicted = set(r["predicted"]["iocs"])
        truth = set(r["ground_truth"]["iocs"])
        tp += len(predicted & truth)
        fp += len(predicted - truth)
        fn += len(truth - predicted)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def compute_main_system_metrics(records):
    ok_records = [r for r in records if r["status"] == "ok"]
    y_true_tt = [r["ground_truth"]["threat_type"] for r in ok_records]
    y_pred_tt = [r["predicted"]["threat_type"] for r in ok_records]
    y_true_sev = [r["ground_truth"]["severity"] for r in ok_records]
    y_pred_sev = [r["predicted"]["severity"] for r in ok_records]

    # Only successful requests' timings represent real analyze-pipeline
    # performance -- a fast 429 rejection isn't "low latency," it's a
    # different thing entirely, and mixing the two would skew the reported
    # distribution in a misleading direction.
    latencies = [r["latency_ms"] for r in ok_records]
    costs = [r["cost_usd_est"] for r in ok_records if r.get("cost_usd_est") is not None]

    return {
        "threat_type": _classification_metrics(y_true_tt, y_pred_tt) if ok_records else None,
        "severity": _classification_metrics(y_true_sev, y_pred_sev) if ok_records else None,
        "iocs": _ioc_prf(records),
        "latency": {
            "mean_ms": statistics.mean(latencies) if latencies else None,
            "median_ms": statistics.median(latencies) if latencies else None,
            "p95_ms": float(np.percentile(latencies, 95)) if latencies else None,
        },
        "cost": {"mean_usd_est": statistics.mean(costs) if costs else None},
        "n_ok": len(ok_records),
        "n_error": len(records) - len(ok_records),
    }


def compute_baseline_metrics(records):
    y_true_tt = [r["ground_truth"]["threat_type"] for r in records]
    y_pred_tt = [r["predicted"]["threat_type"] for r in records]
    y_true_sev = [r["ground_truth"]["severity"] for r in records]
    y_pred_sev = [r["predicted"]["severity"] for r in records]
    return {
        "threat_type": _classification_metrics(y_true_tt, y_pred_tt),
        "severity": _classification_metrics(y_true_sev, y_pred_sev),
    }


def main():
    parser = argparse.ArgumentParser(description="ThreatGPT Phase 4 evaluation harness")
    parser.add_argument("--test_set", default="data/annotations/labels.csv")
    parser.add_argument("--raw_dir", default="data/raw")
    parser.add_argument("--output", default="results.json")
    parser.add_argument("--ratings_template_output", default="docs/evaluation_ratings_template.csv")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip_baselines", action="store_true")
    parser.add_argument("--skip_baseline2", action="store_true")
    parser.add_argument(
        "--pace_seconds",
        type=float,
        default=15,
        help="Seconds to wait between real LLM calls (main system and Baseline 2), to stay "
        "under free-tier rate limits (e.g. Gemini free tier: 5 requests/minute = 1 per 12s). "
        "Set to 0 to disable if using a paid tier with higher limits.",
    )
    args = parser.parse_args()

    rows = load_ground_truth(args.test_set)
    if args.limit:
        rows = rows[: args.limit]

    Base.metadata.create_all(bind=engine)
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    print(f"Running main system against {len(rows)} document(s)...")
    main_records = run_main_system(client, rows, args.raw_dir, args.provider, args.pace_seconds)
    main_metrics = compute_main_system_metrics(main_records)

    results = {
        "run_meta": {
            "provider": args.provider or os.getenv("LLM_PROVIDER", "gemini"),
            "model": _current_model(args.provider),
            "n_docs": len(rows),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "records": main_records,
        "metrics": main_metrics,
        "baselines": {},
    }

    if not args.skip_baselines:
        print("Running Baseline 1 (keyword-based)...")
        kw_records = run_keyword_baseline_all(rows, args.raw_dir)
        results["baselines"]["keyword"] = {
            "records": kw_records,
            "metrics": compute_baseline_metrics(kw_records),
        }

        print("Running Baseline 3 (first-N-sentences)...")
        fns_records = run_first_n_sentences_all(rows, args.raw_dir)
        results["baselines"]["first_n_sentences"] = {"records": fns_records}

        if not args.skip_baseline2:
            print(f"Running Baseline 2 (zero-shot LLM, {len(rows)} real calls)...")
            zs_records = run_zero_shot_baseline_all(rows, args.raw_dir, args.provider, args.pace_seconds)
            zs_for_metrics = [
                r
                for r in zs_records
                if r["predicted"].get("threat_type") is not None and r["predicted"].get("severity") is not None
            ]
            parse_failures = len(zs_records) - len(zs_for_metrics)
            results["baselines"]["zero_shot_llm"] = {
                "records": zs_records,
                "metrics": compute_baseline_metrics(zs_for_metrics) if zs_for_metrics else None,
                "parse_failure_rate": parse_failures / len(zs_records) if zs_records else None,
            }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote {args.output}")

    ratings_dir = os.path.dirname(args.ratings_template_output)
    if ratings_dir:
        os.makedirs(ratings_dir, exist_ok=True)
    with open(args.ratings_template_output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["alert_id", "filename", "summary", "reviewer_1", "reviewer_2", "reviewer_3"])
        for r in main_records:
            if r["status"] == "ok":
                writer.writerow([r["alert_id"], r["filename"], r["predicted"]["summary"], "", "", ""])
    print(f"Wrote {args.ratings_template_output} (blank, awaiting human ratings)")

    _print_summary(results)

    Base.metadata.drop_all(bind=engine)
    if os.path.exists(_db_path):
        os.remove(_db_path)


def _print_summary(results):
    m = results["metrics"]
    print("\n--- Summary ---")
    print(f"Main system: {m['n_ok']} ok, {m['n_error']} error")
    if m["threat_type"]:
        print(f"Threat type macro F1: {m['threat_type']['macro']['f1']:.3f} (accuracy {m['threat_type']['accuracy']:.3f})")
    if m["severity"]:
        print(f"Severity macro F1: {m['severity']['macro']['f1']:.3f} (accuracy {m['severity']['accuracy']:.3f})")
    print(f"IoC F1: {m['iocs']['f1']:.3f} (precision {m['iocs']['precision']:.3f}, recall {m['iocs']['recall']:.3f})")
    if m["latency"]["mean_ms"] is not None:
        print(f"Latency: mean {m['latency']['mean_ms']:.0f}ms, p95 {m['latency']['p95_ms']:.0f}ms")
    if m["cost"]["mean_usd_est"] is not None:
        print(f"Estimated cost: ${m['cost']['mean_usd_est']:.5f}/request (mean, estimated)")


if __name__ == "__main__":
    main()
