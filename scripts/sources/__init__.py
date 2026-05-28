"""数据源采集器"""
import urllib.request
import urllib.error
import time
import sys
from typing import List, Dict

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
}


def fetch_url(url: str, timeout: int = 30, max_retries: int = 3) -> bytes:
    """获取URL内容，遇到429/5xx自动重试（指数退避）"""
    for attempt in range(max_retries):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = min(2 ** (attempt + 2), 60)  # 4s, 8s, 16s...
                print(f"  [WARN] 429 Rate limited on {url[:80]}, retry {attempt+1}/{max_retries} after {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            elif e.code >= 500:
                wait = 2 ** attempt
                print(f"  [WARN] {e.code} Server error on {url[:80]}, retry {attempt+1}/{max_retries} after {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            else:
                print(f"  [WARN] HTTP {e.code} on {url[:80]}: {e}", file=sys.stderr)
                return b""
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            print(f"  [WARN] Failed to fetch {url[:80]}: {e}", file=sys.stderr)
            return b""
    print(f"  [ERROR] All {max_retries} retries exhausted for {url[:80]}", file=sys.stderr)
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
