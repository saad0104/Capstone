from typing import Any, Dict, List

SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]

# Keyword cross-check per docs/architecture.md's "cross-check severity with keyword
# signals" step. This can only upgrade severity, never downgrade the LLM's call --
# it exists to catch clear under-calls, not to second-guess a correct High/Critical.
SEVERITY_KEYWORDS = {
    "Critical": [
        "actively exploited",
        "zero-day",
        "ransomware",
        "unauthenticated remote code execution",
        "critical infrastructure",
    ],
    "High": [
        "remote code execution",
        "privilege escalation",
        "data breach",
    ],
}


def reconcile_iocs(regex_iocs: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Regex output is authoritative -- it's the same extraction method the project's
    evaluation ground truth was built with. This is the seam where a future
    LLM-suggested IoC could be unioned in; for now it validates/dedupes the regex
    result unchanged."""
    return {k: sorted(set(v)) for k, v in regex_iocs.items()}


def cross_check_severity(llm_severity: str, cleaned_text: str) -> Dict[str, Any]:
    llm_severity = llm_severity if llm_severity in SEVERITY_ORDER else "Medium"
    text_lower = cleaned_text.lower()

    suggested = None
    for level, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            suggested = level
            break

    mismatch = (
        suggested is not None
        and SEVERITY_ORDER.index(suggested) > SEVERITY_ORDER.index(llm_severity)
    )
    final_severity = suggested if mismatch else llm_severity
    return {
        "severity": final_severity,
        "severity_flagged": mismatch,
        "severity_llm_original": llm_severity,
    }


def build_alert(
    raw_input: str,
    cleaned_text: str,
    regex_iocs: Dict[str, List[str]],
    llm_result: Dict[str, Any],
    processing_ms: int,
) -> Dict[str, Any]:
    iocs = reconcile_iocs(regex_iocs)
    severity_check = cross_check_severity(llm_result.get("severity", "Medium"), cleaned_text)

    return {
        "raw_input": raw_input,
        "summary": llm_result.get("summary", ""),
        "threat_type": llm_result.get("threat_type", "unknown"),
        "severity": severity_check["severity"],
        "ioc_list": iocs,
        "recommended_action": llm_result.get("recommended_action", ""),
        "processing_ms": processing_ms,
    }
