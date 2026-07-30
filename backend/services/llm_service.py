import os
import time
from typing import Any, Dict, Optional

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class LLMAnalysis(BaseModel):
    summary: str = Field(description="2-3 sentence summary of the threat report")
    threat_type: str = Field(
        description="one of: vulnerability, ransomware, phishing, malware, DDoS, APT, supply-chain, exploit, other"
    )
    severity: str = Field(description="one of: Low, Medium, High, Critical")
    recommended_action: str = Field(description="short actionable remediation guidance")


_PARSER = PydanticOutputParser(pydantic_object=LLMAnalysis)

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a cyber threat intelligence analyst. Respond ONLY with JSON matching "
            "the schema below -- no free text, no markdown fences.\n{format_instructions}\n\n"
            "Example 1:\n"
            "Input: Apache Log4j2 contains a JNDI-related remote code execution vulnerability "
            "when attacker-controlled data reaches vulnerable message lookup functionality.\n"
            'Output: {{"summary": "Apache Log4j2 has a JNDI-related RCE vulnerability triggered '
            'by attacker-controlled log data. Organizations should identify affected log4j-core '
            'deployments and upgrade to a fixed release.", "threat_type": "vulnerability", '
            '"severity": "Critical", "recommended_action": "Upgrade log4j-core to a patched '
            'version and audit for signs of exploitation."}}\n\n'
            "Example 2:\n"
            "Input: CISA and partners described Black Basta ransomware activity, including "
            "observed tactics and indicators, and provide mitigation guidance for defenders.\n"
            'Output: {{"summary": "Black Basta is a ransomware operation with documented '
            'tactics and indicators. Defenders should apply the advisory\'s mitigation guidance '
            'to reduce risk and impact.", "threat_type": "ransomware", "severity": "High", '
            '"recommended_action": "Apply CISA\'s mitigation guidance and maintain protected, '
            'offline backups."}}',
        ),
        ("human", "{report_text}"),
    ]
).partial(format_instructions=_PARSER.get_format_instructions())


def _build_gemini():
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0,
    )


def _build_grok():
    from langchain_openai import ChatOpenAI  # Grok's API is OpenAI-compatible

    return ChatOpenAI(
        model=os.getenv("XAI_MODEL", "grok-2-latest"),
        api_key=os.getenv("XAI_API_KEY"),
        base_url=os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"),
        temperature=0,
    )


def _build_ollama():
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0,
    )


def _build_openrouter():
    from langchain_openai import ChatOpenAI  # OpenRouter's API is OpenAI-compatible

    return ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0,
    )


PROVIDER_REGISTRY = {
    "gemini": _build_gemini,
    "grok": _build_grok,
    "ollama": _build_ollama,
    "openrouter": _build_openrouter,
}


class LLMService:
    """LangChain-based structured-output service. Provider is resolved once at
    construction (from the `provider` arg or LLM_PROVIDER env var) -- a single
    active provider for MVP, per project decision. The constructor already
    accepting `provider=` explicitly is what makes a future per-request selector
    a small addition later rather than a rewrite."""

    def __init__(self, provider: Optional[str] = None):
        self.provider_name = provider or os.getenv("LLM_PROVIDER", "gemini")
        if self.provider_name not in PROVIDER_REGISTRY:
            raise ValueError(
                f"Unknown LLM_PROVIDER '{self.provider_name}', expected one of {list(PROVIDER_REGISTRY)}"
            )
        self._chat_model = PROVIDER_REGISTRY[self.provider_name]()
        self._chain = _PROMPT | self._chat_model | _PARSER

    def summarize(self, text: str) -> Dict[str, Any]:
        start = time.time()
        result: LLMAnalysis = self._chain.invoke({"report_text": text})
        return {
            **result.model_dump(),
            "processing_ms": int((time.time() - start) * 1000),
        }


_default_instance = None


def get_llm_service() -> LLMService:
    """Lazy singleton so a missing API key or unreachable local Ollama host doesn't
    crash `flask run` or pytest collection at import time -- only actual requests
    that need the LLM should fail. Also gives tests a clean monkeypatch seam."""
    global _default_instance
    if _default_instance is None:
        _default_instance = LLMService()
    return _default_instance
