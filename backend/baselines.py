import json
import re
import time
from typing import Any, Dict

from .services.llm_service import PROVIDER_REGISTRY

# --- Baseline 1: keyword-based (no LLM call) --------------------------------
# Deliberately independent from backend/alert_engine.py's SEVERITY_KEYWORDS /
# cross_check_severity -- that logic is a component of the production system
# under test; reusing it here would make this baseline artificially strong
# and undermine the "does the LLM add value over rules" comparison.
THREAT_TYPE_KEYWORDS = [
    ("ransomware", ["ransomware", "encrypt", "extortion"]),
    ("phishing", ["phishing", "credential", "spoofed domain"]),
    ("DDoS", ["denial-of-service", "ddos", "flow-control", "flood"]),
    ("APT", ["state-sponsored", "advanced persistent threat", "nation-state"]),
    ("supply-chain", ["supply chain", "supply-chain", "upstream package", "tarball"]),
    ("exploit", ["actively exploited", "in the wild", "zero-day"]),
    ("malware", ["malware", "botnet", "trojan"]),
    ("vulnerability", ["vulnerability", "cve-"]),
]

DANGER_KEYWORDS = [
    "zero-day",
    "exploit",
    "actively exploited",
    "critical infrastructure",
    "remote code execution",
    "unauthenticated",
]
SEVERITY_THRESHOLDS = [(3, "Critical"), (2, "High"), (1, "Medium")]  # else "Low"


def run_keyword_baseline(text: str) -> Dict[str, str]:
    """No LLM call."""
    text_lower = text.lower()

    threat_type = "unknown"
    for label, keywords in THREAT_TYPE_KEYWORDS:
        if any(kw in text_lower for kw in keywords):
            threat_type = label
            break

    danger_count = sum(1 for kw in DANGER_KEYWORDS if kw in text_lower)
    severity = "Low"
    for threshold, label in SEVERITY_THRESHOLDS:
        if danger_count >= threshold:
            severity = label
            break

    return {"threat_type": threat_type, "severity": severity}


# --- Baseline 2: zero-shot LLM (own real LLM calls) -------------------------
# Deliberately NOT reusing services.llm_service._PROMPT/_PARSER: those carry
# the 2-shot examples and PydanticOutputParser format_instructions that are
# themselves part of what's being evaluated (few-shot + structured output).
# Reuses PROVIDER_REGISTRY only for provider/model construction (avoids
# duplicating API-key/base-url wiring), then issues its own minimal,
# unconstrained prompt via .invoke() and reads .content directly.
_ZERO_SHOT_PROMPT = (
    "Read this threat report and answer with the threat type, severity, "
    'and a short summary as JSON: {{"threat_type": ..., "severity": ..., '
    '"summary": ...}}\n\nReport:\n{report_text}'
)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def run_zero_shot_llm_baseline(text: str, provider_name: str) -> Dict[str, Any]:
    """Makes one real LLM call."""
    if provider_name not in PROVIDER_REGISTRY:
        raise ValueError(f"Unknown provider '{provider_name}'")
    chat_model = PROVIDER_REGISTRY[provider_name]()

    start = time.time()
    response = chat_model.invoke(_ZERO_SHOT_PROMPT.format(report_text=text))
    processing_ms = int((time.time() - start) * 1000)
    raw_output = response.content

    parsed_json = None
    fence_match = _JSON_FENCE_RE.search(raw_output)
    candidate = fence_match.group(1) if fence_match else raw_output
    try:
        parsed_json = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        parsed_json = None

    return {
        "threat_type": parsed_json.get("threat_type") if parsed_json else None,
        "severity": parsed_json.get("severity") if parsed_json else None,
        "summary": parsed_json.get("summary") if parsed_json else None,
        "raw_output": raw_output,
        "parsed": parsed_json is not None,
        "processing_ms": processing_ms,
    }


# --- Baseline 3: first-N-sentences (no LLM call, summary only) -------------
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _strip_remaining_header_lines(text: str) -> str:
    """eval_utils.load_document() only strips Source:/Source URL: lines
    (narrowly scoped to fix an IoC-extraction false-positive). That leaves
    Published:/Title:/CVE:/NVD severity: lines in place, which the LLM-based
    approaches handle gracefully but this baseline's naive sentence splitter
    cannot -- it would otherwise glue leftover metadata lines into the
    "summary" as if they were real sentences, unfairly weakening this
    baseline relative to the LLM approaches for a reason that has nothing to
    do with summarization quality. Skip everything through the first blank
    line (the consistent header/body boundary in data/raw/*.txt)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "":
            return "\n".join(lines[i + 1 :])
    return text


def run_first_n_sentences_baseline(text: str, n: int = 3) -> str:
    """No threat_type/severity -- docs/evaluation_plan.md only specifies this
    baseline for summary quality."""
    body = _strip_remaining_header_lines(text)
    sentences = _SENTENCE_SPLIT_RE.split(body.strip())
    return " ".join(sentences[:n])
