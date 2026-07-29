import os
from typing import Optional, Set

# Lines starting with these prefixes are pure source-provenance metadata added
# during data collection (Source:/Source URL:), not part of the report an
# analyst would actually submit. When data/annotations/labels.csv's `iocs`
# column was built, domain extraction deliberately excluded these lines to
# avoid false-positive-matching the publisher's own domain (e.g. www.cisa.gov,
# nvd.nist.gov) as a malicious IoC. evaluate.py must submit the same
# header-stripped body text, or /api/analyze's preprocess.extract_iocs() will
# pick up the publisher domain as a spurious IoC on every single document,
# tanking IoC precision for a reason that has nothing to do with the system's
# real capability.
_HEADER_PREFIXES = ("Source:", "Source URL:")


def strip_source_header(raw_text: str) -> str:
    lines = raw_text.splitlines()
    kept = [ln for ln in lines if not ln.startswith(_HEADER_PREFIXES)]
    return "\n".join(kept)


def load_document(filename: str, raw_dir: str) -> str:
    """Single source of truth for 'what text gets submitted to evaluate the
    system' -- evaluate.py and baselines.py both call this, so every
    approach is compared on identical input."""
    path = os.path.join(raw_dir, filename)
    with open(path, encoding="utf-8") as f:
        raw_text = f.read()
    return strip_source_header(raw_text)


def parse_ground_truth_iocs(iocs_field: str) -> Set[str]:
    if not iocs_field or not iocs_field.strip():
        return set()
    return {v.strip() for v in iocs_field.split(",") if v.strip()}


CHARS_PER_TOKEN = 4  # documented heuristic, not a real tokenizer

# Published per-1K-token USD pricing (standard tier), verified against
# https://ai.google.dev/gemini-api/docs/pricing at the time this was written.
# These are estimates based on a chars/4 token approximation, not metered
# usage -- label as such everywhere they're reported. Re-verify against the
# provider's current pricing page before publishing final numbers, since
# pricing changes over time.
PRICING_USD_PER_1K_TOKENS = {
    ("gemini", "gemini-2.5-flash"): {"input": 0.0003, "output": 0.0025},
}


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def estimate_cost_usd(
    input_text: str, output_text: str, provider: str, model: str
) -> Optional[float]:
    pricing = PRICING_USD_PER_1K_TOKENS.get((provider, model))
    if pricing is None:
        return None
    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)
    return (input_tokens / 1000) * pricing["input"] + (output_tokens / 1000) * pricing["output"]
