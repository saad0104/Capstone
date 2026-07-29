from backend.preprocess import clean_text, extract_iocs


def test_extract_cve():
    assert "CVE-2021-44228" in extract_iocs("Exploiting CVE-2021-44228 in Log4j")["cves"]


def test_extract_ip():
    assert "10.0.0.1" in extract_iocs("C2 server at 10.0.0.1 observed")["ips"]


def test_extract_hash():
    h = "d41d8cd98f00b204e9800998ecf8427e" * 2  # 64 hex chars
    assert h in extract_iocs(f"payload hash {h}")["hashes"]


def test_extract_domain():
    assert "evil.example.com" in extract_iocs("beaconing to evil.example.com")["domains"]


def test_extract_defanged_ip():
    assert "162.19.196[.]13" in extract_iocs("C2 server at 162.19.196[.]13 observed")["ips"]


def test_extract_defanged_domain():
    assert "pro-swapper[.]com" in extract_iocs("beaconing to pro-swapper[.]com")["domains"]


def test_clean_text_normalizes_whitespace():
    assert clean_text("a\r\n\n  b") == "a b"


def test_no_false_positive_on_plain_text():
    iocs = extract_iocs("This report mentions no indicators at all.")
    assert all(len(v) == 0 for v in iocs.values())
