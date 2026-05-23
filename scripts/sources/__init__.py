"""数据源采集器"""
import urllib.request
import time
from typing import List, Dict

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def fetch_url(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}")
        return b""


def make_content_id(source: str, raw_id: str) -> str:
    return f"{source}_{raw_id}".replace(' ', '_').lower()


def deduplicate(items: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for item in items:
        key = item['title'].lower().strip()[:100]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique
