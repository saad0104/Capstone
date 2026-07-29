import re
from typing import List, Dict

IP_RE = re.compile(r"\b(?:[0-9]{1,3}(?:\.|\[\.\])){3}[0-9]{1,3}\b")
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
HASH_RE = re.compile(r"\b[0-9a-fA-F]{32,128}\b")
DOMAIN_RE = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.|\[\.\]))+[a-z]{2,10}\b", re.IGNORECASE)

def clean_text(text: str) -> str:
    text = text.replace('\r', '\n')
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_iocs(text: str) -> Dict[str, List[str]]:
    return {
        "ips": list(set(IP_RE.findall(text))),
        "cves": list(set(CVE_RE.findall(text))),
        "hashes": list(set(HASH_RE.findall(text))),
        "domains": list(set(DOMAIN_RE.findall(text)))
    }
