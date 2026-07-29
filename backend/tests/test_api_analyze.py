def test_analyze_happy_path(client, mock_llm):
    resp = client.post("/api/analyze", json={"text": "CVE-2021-44228 exploited at 10.0.0.1"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["threat_type"] == "ransomware"
    assert "CVE-2021-44228" in body["ioc_list"]
    assert body["id"]


def test_analyze_rejects_empty_text(client, mock_llm):
    resp = client.post("/api/analyze", json={"text": "   "})
    assert resp.status_code == 400


def test_analyze_rejects_malformed_json(client, mock_llm):
    resp = client.post("/api/analyze", data="not json", content_type="application/json")
    assert resp.status_code == 400


def test_analyze_llm_failure_returns_502(client, monkeypatch):
    def boom():
        class F:
            def summarize(self, text):
                raise RuntimeError("provider down")
        return F()
    monkeypatch.setattr("backend.app.get_llm_service", boom)
    resp = client.post("/api/analyze", json={"text": "some report text"})
    assert resp.status_code == 502


def test_analyze_with_explicit_provider_uses_llmservice(client, monkeypatch):
    calls = {}

    class FakeLLM:
        def __init__(self, provider=None):
            calls["provider"] = provider

        def summarize(self, text):
            return {
                "summary": "s",
                "threat_type": "malware",
                "severity": "Low",
                "recommended_action": "a",
                "processing_ms": 1,
            }

    monkeypatch.setattr("backend.app.LLMService", FakeLLM)
    resp = client.post("/api/analyze", json={"text": "some text", "provider": "grok"})
    assert resp.status_code == 201
    assert calls["provider"] == "grok"


def test_analyze_rejects_unknown_provider(client, mock_llm):
    resp = client.post("/api/analyze", json={"text": "some text", "provider": "bogus"})
    assert resp.status_code == 400
