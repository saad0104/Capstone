from backend.alert_engine import build_alert, cross_check_severity


def test_severity_upgraded_on_strong_keyword():
    result = cross_check_severity("Medium", "this is actively exploited ransomware")
    assert result["severity"] == "Critical"
    assert result["severity_flagged"] is True


def test_severity_unchanged_when_no_signal():
    result = cross_check_severity("High", "a routine advisory with no strong keywords")
    assert result["severity"] == "High"
    assert result["severity_flagged"] is False


def test_severity_never_downgraded():
    result = cross_check_severity("Critical", "remote code execution possible")
    assert result["severity"] == "Critical"
    assert result["severity_flagged"] is False


def test_build_alert_shapes_ioc_list_as_dict():
    alert = build_alert(
        raw_input="raw",
        cleaned_text="cleaned CVE-2021-44228",
        regex_iocs={"cves": ["CVE-2021-44228"], "ips": [], "hashes": [], "domains": []},
        llm_result={"severity": "High", "threat_type": "vulnerability", "summary": "s", "recommended_action": "a"},
        processing_ms=10,
    )
    assert alert["ioc_list"]["cves"] == ["CVE-2021-44228"]
    assert alert["threat_type"] == "vulnerability"
