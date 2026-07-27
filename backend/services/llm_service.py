import os
import time
from typing import Dict, Any

class LLMService:
    """Minimal LLM service placeholder. Replace with real API calls."""
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def summarize(self, text: str) -> Dict[str, Any]:
        # Placeholder behavior: very simple heuristic summary
        start = time.time()
        summary = text.strip().replace('\n', ' ')[:280]
        result = {
            "summary": summary,
            "threat_type": "unknown",
            "severity": "Medium",
            "ioc_list": [],
            "recommended_action": "Review the report and investigate IoCs.",
            "processing_ms": int((time.time()-start)*1000)
        }
        return result
