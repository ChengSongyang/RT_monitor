# RSS-first Collection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add RSS-first paper collection for arXiv, IJROBP Red Journal, and Radiotherapy and Oncology Green Journal, with a read-only RSS source status page in the app navigation.

**Architecture:** Add a small RSS source catalog, a standard-library RSS/Atom parser/collector, and a `/api/rss-sources` status endpoint backed by existing `sync_log`. The Next.js app proxies that endpoint and renders a read-only `/rss-sources` page linked from the sidebar.

**Tech Stack:** Python 3 standard library (`urllib`, `xml.etree.ElementTree`, `email.utils`, SQLite), existing `scripts/db.py` persistence, Next.js 16 App Router, React 19, TypeScript strict, Tailwind CSS v4 utility classes.

---

## File Structure

- Create `scripts/rss_source_catalog.py` — owns the three first-phase RSS/Atom source definitions and helper functions for enabled sources.
- Create `scripts/sources/rss_feeds.py` — fetches RSS/Atom XML, parses entries, scores/normalizes them into existing content items, and exposes per-source collection results.
- Modify `scripts/collect.py` — runs `rss_feeds` first and logs/upserts each RSS source independently so UI status is per subscription.
- Modify `scripts/db.py` — adds `query_rss_sources()` to join catalog data with the latest `sync_log` row for each RSS source.
- Modify `api_server.py` — adds `GET /api/rss-sources`.
- Create `src/app/api/rss-sources/route.ts` — proxies the Python API through the existing `API_BASE_URL` pattern.
- Modify `src/types/index.ts` — adds `RssSource` and `RssSourcesResponse` TypeScript interfaces.
- Modify `src/components/layout/Sidebar.tsx` — supports an active nav key and adds a real “RSS 订阅源” link.
- Modify `src/app/page.tsx` — passes `active="home"` to `Sidebar`.
- Create `src/app/rss-sources/page.tsx` — renders the read-only RSS subscription status page.

---

### Task 1: Add RSS source catalog

**Files:**
- Create: `scripts/rss_source_catalog.py`

- [ ] **Step 1: Write a failing import smoke test**

Run this before creating the file:

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from rss_source_catalog import RSS_SOURCES, enabled_rss_sources, get_rss_source
assert len(RSS_SOURCES) == 3
assert [source['id'] for source in enabled_rss_sources()] == [
    'arxiv-radiotherapy-ai',
    'ijrobp-red-journal',
    'radonc-green-journal',
]
assert get_rss_source('ijrobp-red-journal')['short_name'] == 'Red Journal'
print('rss source catalog ok')
PY
```

Expected: FAIL with `ModuleNotFoundError: No module named 'rss_source_catalog'`.

- [ ] **Step 2: Create `scripts/rss_source_catalog.py`**

```python
"""RSS/Atom subscription source catalog for paper discovery."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

RSS_SOURCES: List[Dict[str, Any]] = [
    {
        'id': 'arxiv-radiotherapy-ai',
        'name': 'arXiv 放疗 + AI',
        'short_name': 'arXiv RT+AI',
        'kind': 'academic',
        'kind_label': '预印本',
        'source': 'arXiv',
        'source_type': 'paper',
        'category': 'paper',
        'feed_url': 'https://export.arxiv.org/api/query?search_query=all:radiotherapy+AND+all:%22artificial+intelligence%22&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending',
        'homepage': 'https://arxiv.org/',
        'enabled': True,
        'trust_level': 'medium',
        'collection_method': 'arXiv Atom 检索源',
        'description': 'arXiv 中 radiotherapy 与 artificial intelligence 相关的最新预印本。',
        'base_score': 70,
        'tags': ['arXiv', '预印本', '放疗', 'AI'],
    },
    {
        'id': 'ijrobp-red-journal',
        'name': 'International Journal of Radiation Oncology•Biology•Physics',
        'short_name': 'Red Journal',
        'kind': 'journal',
        'kind_label': '放疗期刊',
        'source': 'IJROBP',
        'source_type': 'paper',
        'category': 'paper',
        'feed_url': 'https://rss.sciencedirect.com/publication/science/03603016',
        'homepage': 'https://www.sciencedirect.com/journal/international-journal-of-radiation-oncology-biology-physics',
        'enabled': True,
        'trust_level': 'high',
        'collection_method': 'ScienceDirect RSS 订阅',
        'description': '红皮期刊 International Journal of Radiation Oncology•Biology•Physics 最新论文 RSS。',
        'base_score': 85,
        'tags': ['Red Journal', 'IJROBP', '放疗期刊'],
    },
    {
        'id': 'radonc-green-journal',
        'name': 'Radiotherapy and Oncology',
        'short_name': 'Green Journal',
        'kind': 'journal',
        'kind_label': '放疗期刊',
        'source': 'Radiotherapy and Oncology',
        'source_type': 'paper',
        'category': 'paper',
        'feed_url': 'https://rss.sciencedirect.com/publication/science/01678140',
        'homepage': 'https://www.sciencedirect.com/journal/radiotherapy-and-oncology',
        'enabled': True,
        'trust_level': 'high',
        'collection_method': 'ScienceDirect RSS 订阅',
        'description': '绿皮期刊 Radiotherapy and Oncology 最新论文 RSS。',
        'base_score': 85,
        'tags': ['Green Journal', 'Radiotherapy and Oncology', '放疗期刊'],
    },
]


def enabled_rss_sources() -> List[Dict[str, Any]]:
    return [dict(source) for source in RSS_SOURCES if source.get('enabled')]


def get_rss_source(source_id: str) -> Optional[Dict[str, Any]]:
    for source in RSS_SOURCES:
        if source['id'] == source_id:
            return dict(source)
    return None
```

- [ ] **Step 3: Run the smoke test again**

Run:

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from rss_source_catalog import RSS_SOURCES, enabled_rss_sources, get_rss_source
assert len(RSS_SOURCES) == 3
assert [source['id'] for source in enabled_rss_sources()] == [
    'arxiv-radiotherapy-ai',
    'ijrobp-red-journal',
    'radonc-green-journal',
]
assert get_rss_source('ijrobp-red-journal')['short_name'] == 'Red Journal'
print('rss source catalog ok')
PY
```

Expected: PASS and prints `rss source catalog ok`.

- [ ] **Step 4: Commit**

```bash
git add scripts/rss_source_catalog.py
git commit -m "feat: add RSS source catalog"
```

---

### Task 2: Add RSS/Atom parser and collector

**Files:**
- Create: `scripts/sources/rss_feeds.py`

- [ ] **Step 1: Write failing parser smoke tests**

Run this before creating the file:

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from sources.rss_feeds import parse_feed, score_entry

atom = b'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2605.12345v1</id>
    <title>Artificial intelligence for radiotherapy planning</title>
    <summary>Deep learning improves auto-contouring for radiotherapy.</summary>
    <published>2026-05-30T10:00:00Z</published>
    <author><name>Zhang W</name></author>
    <link href="http://arxiv.org/abs/2605.12345v1" rel="alternate" />
  </entry>
</feed>'''

rss = b'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><item>
  <title>SBRT outcomes in lung cancer</title>
  <link>https://example.com/article</link>
  <description>Radiation oncology article. doi:10.1016/j.ijrobp.2026.01.001</description>
  <pubDate>Fri, 29 May 2026 12:00:00 GMT</pubDate>
</item></channel></rss>'''

atom_entries = parse_feed(atom)
rss_entries = parse_feed(rss)
assert atom_entries[0]['arxiv_id'] == '2605.12345'
assert atom_entries[0]['authors'] == 'Zhang W'
assert rss_entries[0]['doi'] == '10.1016/j.ijrobp.2026.01.001'
assert score_entry({'base_score': 70}, atom_entries[0]) >= 80
print('rss parser ok')
PY
```

Expected: FAIL with `ModuleNotFoundError: No module named 'sources.rss_feeds'`.

- [ ] **Step 2: Create `scripts/sources/rss_feeds.py`**

```python
"""RSS/Atom collectors for paper sources."""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

from . import fetch_url
from rss_source_catalog import enabled_rss_sources

ATOM_NS = {'atom': 'http://www.w3.org/2005/Atom'}
CONTENT_NS = {'content': 'http://purl.org/rss/1.0/modules/content/'}

KEYWORD_BONUSES = {
    'artificial intelligence': 6,
    'machine learning': 5,
    'deep learning': 5,
    'ai': 4,
    'adaptive radiotherapy': 6,
    'auto-contouring': 6,
    'autocontouring': 6,
    'segmentation': 4,
    'treatment planning': 5,
    'dose prediction': 5,
    'proton': 4,
    'flash': 5,
    'sbrt': 4,
    'mr-linac': 5,
    'cbct': 4,
}

RADIOTHERAPY_TERMS = (
    'radiotherapy',
    'radiation therapy',
    'radiation oncology',
    '放疗',
)

AI_TERMS = (
    'artificial intelligence',
    'machine learning',
    'deep learning',
    ' ai ',
    'automatic',
    'auto-contouring',
    'segmentation',
)


def clean_text(value: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', value or '')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    return re.sub(r'\s+', ' ', text).strip()


def parse_date(value: str) -> tuple[str, float]:
    raw = (value or '').strip()
    if not raw:
        now = datetime.now(timezone.utc)
        return now.strftime('%Y-%m-%d'), now.timestamp()

    parsers = (
        lambda text: datetime.fromisoformat(text.replace('Z', '+00:00')),
        parsedate_to_datetime,
    )
    for parser in parsers:
        try:
            parsed = parser(raw)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            parsed = parsed.astimezone(timezone.utc)
            return parsed.strftime('%Y-%m-%d'), parsed.timestamp()
        except Exception:
            continue

    if len(raw) >= 10 and re.match(r'\d{4}-\d{2}-\d{2}', raw[:10]):
        parsed = datetime.strptime(raw[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        return parsed.strftime('%Y-%m-%d'), parsed.timestamp()

    now = datetime.now(timezone.utc)
    return now.strftime('%Y-%m-%d'), now.timestamp()


def extract_doi(text: str) -> str:
    match = re.search(r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+', text or '')
    return match.group(0).rstrip('.,);]') if match else ''


def extract_arxiv_id(text: str) -> str:
    match = re.search(r'(?:arxiv\.org/(?:abs|pdf)/|arXiv:)?(\d{4}\.\d{4,5})(?:v\d+)?', text or '', re.I)
    return match.group(1) if match else ''


def stable_identifier(entry: Dict[str, str]) -> str:
    doi = entry.get('doi', '')
    if doi:
        return 'doi_' + slug_identifier(doi)
    arxiv_id = entry.get('arxiv_id', '')
    if arxiv_id:
        return 'arxiv_' + slug_identifier(arxiv_id)
    link = entry.get('link', '')
    if link:
        parsed = urlparse(link)
        return 'url_' + slug_identifier(f'{parsed.netloc}_{parsed.path}')
    return 'title_' + slug_identifier(entry.get('title', 'untitled'))


def slug_identifier(value: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', value.lower()).strip('_')
    return re.sub(r'_+', '_', slug) or 'unknown'


def _find_atom_link(entry: ET.Element) -> str:
    for link in entry.findall('atom:link', ATOM_NS):
        rel = link.attrib.get('rel', 'alternate')
        href = link.attrib.get('href', '')
        if href and rel == 'alternate':
            return href
    first = entry.find('atom:link', ATOM_NS)
    return first.attrib.get('href', '') if first is not None else ''


def _parse_atom(root: ET.Element) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    for entry in root.findall('atom:entry', ATOM_NS):
        title = clean_text(entry.findtext('atom:title', default='', namespaces=ATOM_NS))
        summary = clean_text(entry.findtext('atom:summary', default='', namespaces=ATOM_NS))
        link = _find_atom_link(entry)
        published = entry.findtext('atom:published', default='', namespaces=ATOM_NS) or entry.findtext('atom:updated', default='', namespaces=ATOM_NS)
        authors = [clean_text(author.findtext('atom:name', default='', namespaces=ATOM_NS)) for author in entry.findall('atom:author', ATOM_NS)]
        joined = ' '.join([entry.findtext('atom:id', default='', namespaces=ATOM_NS), title, summary, link])
        entries.append({
            'title': title,
            'summary': summary,
            'content': summary,
            'link': link,
            'published': published,
            'authors': ', '.join([author for author in authors if author]),
            'doi': extract_doi(joined),
            'arxiv_id': extract_arxiv_id(joined),
        })
    return entries


def _parse_rss(root: ET.Element) -> List[Dict[str, str]]:
    channel = root.find('channel')
    if channel is None:
        return []

    entries: List[Dict[str, str]] = []
    for item in channel.findall('item'):
        title = clean_text(item.findtext('title', default=''))
        description = clean_text(item.findtext('description', default=''))
        content_encoded = ''
        for child in item:
            if child.tag.endswith('encoded'):
                content_encoded = clean_text(child.text or '')
                break
        summary = description or content_encoded
        link = clean_text(item.findtext('link', default=''))
        published = item.findtext('pubDate', default='') or item.findtext('date', default='')
        creator = ''
        for child in item:
            if child.tag.endswith('creator'):
                creator = clean_text(child.text or '')
                break
        joined = ' '.join([title, summary, link])
        entries.append({
            'title': title,
            'summary': summary,
            'content': summary,
            'link': link,
            'published': published,
            'authors': creator,
            'doi': extract_doi(joined),
            'arxiv_id': extract_arxiv_id(joined),
        })
    return entries


def parse_feed(data: bytes) -> List[Dict[str, str]]:
    root = ET.fromstring(data)
    if root.tag.endswith('feed'):
        return _parse_atom(root)
    if root.tag == 'rss' or root.tag.endswith('rss'):
        return _parse_rss(root)
    raise ValueError(f'Unsupported feed root: {root.tag}')


def is_relevant_to_arxiv(entry: Dict[str, str]) -> bool:
    text = f" {entry.get('title', '')} {entry.get('summary', '')} ".lower()
    return any(term in text for term in RADIOTHERAPY_TERMS) and any(term in text for term in AI_TERMS)


def score_entry(source: Dict[str, Any], entry: Dict[str, str]) -> int:
    text = f" {entry.get('title', '')} {entry.get('summary', '')} ".lower()
    score = int(source.get('base_score', 70))
    for keyword, bonus in KEYWORD_BONUSES.items():
        if keyword in text:
            score += bonus
    return min(score, 98)


def recommendation_reason(source: Dict[str, Any], score: int, entry: Dict[str, str]) -> str:
    title = entry.get('title', '')
    if source['id'] == 'arxiv-radiotherapy-ai':
        return f"arXiv 放疗与 AI 相关预印本，适合跟踪早期研究动态；规则评分 {score}。"
    return f"{source['short_name']} 是放疗核心期刊，最新论文《{title[:48]}》值得关注；规则评分 {score}。"


def entry_to_content(source: Dict[str, Any], entry: Dict[str, str]) -> Dict[str, Any]:
    date, timestamp = parse_date(entry.get('published', ''))
    score = score_entry(source, entry)
    journal = source['name'] if source['kind'] == 'journal' else source['source']
    tags = list(dict.fromkeys([*source.get('tags', []), source['kind_label'], 'RSS']))
    return {
        'id': stable_identifier(entry),
        'title': entry.get('title') or '未命名论文',
        'summary': entry.get('summary', '')[:500],
        'content': entry.get('content') or entry.get('summary', ''),
        'url': entry.get('link', ''),
        'source': source['source'],
        'source_type': source['source_type'],
        'source_user': entry.get('authors', ''),
        'source_verified': True,
        'source_verified_reason': source['kind_label'],
        'date': date,
        'timestamp': timestamp,
        'category': source['category'],
        'tags': tags,
        'images': [],
        'meta': {
            'authors': entry.get('authors', ''),
            'journal': journal,
            'doi': entry.get('doi', ''),
            'html_url': entry.get('link', ''),
            'source_id': source['id'],
            'source_kind': source['kind'],
            'source_kind_label': source['kind_label'],
            'origin_host': urlparse(entry.get('link', '')).hostname or '',
            'collection_method': source['collection_method'],
            'rss_feed_url': source['feed_url'],
            'arxiv_id': entry.get('arxiv_id', ''),
        },
        'ai': {
            'score': score,
            'is_featured': score >= 85,
            'recommendation_reason': recommendation_reason(source, score, entry),
        },
        'extra': {},
    }


def collect_source(source: Dict[str, Any], days_back: int = 14) -> Dict[str, Any]:
    del days_back
    data = fetch_url(source['feed_url'], timeout=30, max_retries=3)
    if not data:
        return {'source': source, 'items': [], 'error': 'Feed request returned empty response'}

    try:
        entries = parse_feed(data)
    except Exception as exc:
        return {'source': source, 'items': [], 'error': f'Feed parse failed: {exc}'}

    items: List[Dict[str, Any]] = []
    for entry in entries:
        if not entry.get('title'):
            continue
        if source['id'] == 'arxiv-radiotherapy-ai' and not is_relevant_to_arxiv(entry):
            continue
        items.append(entry_to_content(source, entry))

    return {'source': source, 'items': items, 'error': ''}


def collect_by_source(days_back: int = 14) -> List[Dict[str, Any]]:
    results = []
    for source in enabled_rss_sources():
        print(f"  📡 RSS 订阅 {source['short_name']}...", file=sys.stderr)
        result = collect_source(source, days_back=days_back)
        print(f"  ✅ {source['short_name']}: {len(result['items'])} found", file=sys.stderr)
        if result.get('error'):
            print(f"  ❌ {source['short_name']}: {result['error']}", file=sys.stderr)
        results.append(result)
    return results


def collect(days_back: int = 14) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for result in collect_by_source(days_back=days_back):
        items.extend(result['items'])
    return items
```

- [ ] **Step 3: Run parser smoke tests**

Run:

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from sources.rss_feeds import parse_feed, score_entry

atom = b'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2605.12345v1</id>
    <title>Artificial intelligence for radiotherapy planning</title>
    <summary>Deep learning improves auto-contouring for radiotherapy.</summary>
    <published>2026-05-30T10:00:00Z</published>
    <author><name>Zhang W</name></author>
    <link href="http://arxiv.org/abs/2605.12345v1" rel="alternate" />
  </entry>
</feed>'''

rss = b'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><item>
  <title>SBRT outcomes in lung cancer</title>
  <link>https://example.com/article</link>
  <description>Radiation oncology article. doi:10.1016/j.ijrobp.2026.01.001</description>
  <pubDate>Fri, 29 May 2026 12:00:00 GMT</pubDate>
</item></channel></rss>'''

atom_entries = parse_feed(atom)
rss_entries = parse_feed(rss)
assert atom_entries[0]['arxiv_id'] == '2605.12345'
assert atom_entries[0]['authors'] == 'Zhang W'
assert rss_entries[0]['doi'] == '10.1016/j.ijrobp.2026.01.001'
assert score_entry({'base_score': 70}, atom_entries[0]) >= 80
print('rss parser ok')
PY
```

Expected: PASS and prints `rss parser ok`.

- [ ] **Step 4: Verify live feeds parse**

Run:

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from sources.rss_feeds import collect_by_source
results = collect_by_source(days_back=14)
assert len(results) == 3
for result in results:
    print(result['source']['id'], len(result['items']), result['error'])
    assert not result['error']
    assert len(result['items']) > 0
print('live RSS feeds ok')
PY
```

Expected: PASS, prints all three source IDs with item counts greater than zero.

- [ ] **Step 5: Commit**

```bash
git add scripts/sources/rss_feeds.py
git commit -m "feat: add RSS feed collector"
```

---

### Task 3: Integrate RSS collector into collection workflow

**Files:**
- Modify: `scripts/collect.py`

- [ ] **Step 1: Write failing workflow smoke test**

Run this before modifying `scripts/collect.py`:

```bash
python - <<'PY'
from pathlib import Path
text = Path('scripts/collect.py').read_text(encoding='utf-8')
assert 'rss_feeds' in text
assert 'collect_rss_sources' in text
print('collect workflow includes RSS first')
PY
```

Expected: FAIL with `AssertionError`.

- [ ] **Step 2: Modify imports in `scripts/collect.py`**

Replace:

```python
from db import init_db, upsert_content, log_sync
from llm_enrichment import enrich_items
from sources import google_news, guidelines, papers, vendor_news
```

With:

```python
from db import init_db, upsert_content, log_sync
from llm_enrichment import enrich_items
from sources import google_news, guidelines, papers, rss_feeds, vendor_news
```

- [ ] **Step 3: Modify `SOURCES` in `scripts/collect.py`**

Replace:

```python
SOURCES = [
    ('papers', papers),                 # 放疗+AI论文
    ('guidelines', guidelines),         # 常见癌种/协会指南入口
    ('vendor_news', vendor_news),       # 指定厂商官网/相关新闻
    ('radiotherapy_news', google_news), # 行业新闻与学会/监管动态
]
```

With:

```python
SOURCES = [
    ('rss_feeds', rss_feeds),           # RSS-first 论文订阅源
    ('papers', papers),                 # 放疗+AI论文兜底
    ('guidelines', guidelines),         # 常见癌种/协会指南入口
    ('vendor_news', vendor_news),       # 指定厂商官网/相关新闻
    ('radiotherapy_news', google_news), # 行业新闻与学会/监管动态
]
```

- [ ] **Step 4: Add RSS-specific workflow function in `scripts/collect.py`**

Insert this function above `collect_all`:

```python
def collect_rss_sources(days_back: int = 14):
    total_stats = {'found': 0, 'new': 0, 'updated': 0}

    for result in rss_feeds.collect_by_source(days_back=days_back):
        source = result['source']
        items = result['items']
        error = result.get('error', '')
        if error:
            log_sync(source['id'], 0, 0, 0, 'error', error)
            continue

        stats = upsert_content(items)
        log_sync(source['id'], stats['found'], stats['new'], stats['updated'])
        total_stats['found'] += stats['found']
        total_stats['new'] += stats['new']
        total_stats['updated'] += stats['updated']
        print(
            f"  ✅ {source['short_name']}: {stats['new']} new, {stats['updated']} updated",
            file=sys.stderr,
        )

    return total_stats
```

- [ ] **Step 5: Special-case `rss_feeds` inside `collect_all`**

Inside the `for name, source in SOURCES:` loop, immediately after the `print(f"\n📡 采集 {name}...", file=sys.stderr)` line, insert:

```python
            if name == 'rss_feeds':
                stats = collect_rss_sources(days_back=days_back)
                log_sync(name, stats['found'], stats['new'], stats['updated'])
                total_stats['found'] += stats['found']
                total_stats['new'] += stats['new']
                total_stats['updated'] += stats['updated']
                print(f"  ✅ {name}: {stats['new']} new, {stats['updated']} updated", file=sys.stderr)
                continue
```

The resulting `collect_all` loop should keep the existing non-RSS branch unchanged after this inserted block.

- [ ] **Step 6: Run workflow smoke test**

Run:

```bash
python - <<'PY'
from pathlib import Path
text = Path('scripts/collect.py').read_text(encoding='utf-8')
assert 'rss_feeds' in text
assert 'collect_rss_sources' in text
assert "('rss_feeds', rss_feeds)" in text
print('collect workflow includes RSS first')
PY
```

Expected: PASS and prints `collect workflow includes RSS first`.

- [ ] **Step 7: Run live RSS-only collection without search sources**

Run:

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from db import init_db
from collect import collect_rss_sources
init_db()
stats = collect_rss_sources(days_back=14)
print(stats)
assert stats['found'] > 0
PY
```

Expected: PASS, prints a stats dict with `found` greater than zero. `new` may be zero if the database already contains the entries.

- [ ] **Step 8: Commit**

```bash
git add scripts/collect.py
git commit -m "feat: run RSS feeds before fallback collectors"
```

---

### Task 4: Add RSS source status API

**Files:**
- Modify: `scripts/db.py`
- Modify: `api_server.py`
- Create: `src/app/api/rss-sources/route.ts`
- Modify: `src/types/index.ts`

- [ ] **Step 1: Write failing backend API smoke test**

Run this before modifying backend files:

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from db import init_db, query_rss_sources
init_db()
data = query_rss_sources()
assert len(data['sources']) == 3
assert data['sources'][0]['feed_url']
assert 'last_sync_at' in data['sources'][0]
print('rss sources api data ok')
PY
```

Expected: FAIL with `ImportError: cannot import name 'query_rss_sources' from 'db'`.

- [ ] **Step 2: Modify imports in `scripts/db.py`**

Add this import after the existing `from source_catalog import (...)` block:

```python
from rss_source_catalog import RSS_SOURCES
```

- [ ] **Step 3: Add `query_rss_sources()` in `scripts/db.py`**

Insert this function above `query_stats()`:

```python
def query_rss_sources() -> Dict[str, Any]:
    conn = get_db()
    sources: List[Dict[str, Any]] = []

    for source in RSS_SOURCES:
        row = conn.execute(
            'SELECT source, items_found, items_new, items_updated, status, error_message, created_at '
            'FROM sync_log WHERE source = ? ORDER BY created_at DESC LIMIT 1',
            (source['id'],),
        ).fetchone()
        status = dict(row) if row else {}
        sources.append({
            'id': source['id'],
            'name': source['name'],
            'short_name': source['short_name'],
            'kind': source['kind'],
            'kind_label': source.get('kind_label', source['kind']),
            'source': source['source'],
            'source_type': source['source_type'],
            'category': source['category'],
            'feed_url': source['feed_url'],
            'homepage': source['homepage'],
            'enabled': bool(source.get('enabled')),
            'trust_level': source.get('trust_level', ''),
            'collection_method': source.get('collection_method', ''),
            'description': source.get('description', ''),
            'last_sync_at': status.get('created_at', ''),
            'items_found': status.get('items_found', 0),
            'items_new': status.get('items_new', 0),
            'items_updated': status.get('items_updated', 0),
            'status': status.get('status', 'pending'),
            'error_message': status.get('error_message', ''),
        })

    conn.close()
    return {
        'sources': sources,
        'total_sources': len(sources),
        'enabled_sources': sum(1 for source in sources if source['enabled']),
        'active_sources': sum(1 for source in sources if source['last_sync_at'] and source['status'] == 'success'),
    }
```

- [ ] **Step 4: Modify `api_server.py` imports**

Replace:

```python
from db import init_db, query_content, get_report, log_sync, query_sources, query_stats
```

With:

```python
from db import init_db, query_content, get_report, log_sync, query_sources, query_stats, query_rss_sources
```

- [ ] **Step 5: Add route in `api_server.py`**

Insert this branch in `do_GET`, after the existing `/api/sources` branch and before `/api/reports/`:

```python
        elif path == '/api/rss-sources':
            data = query_rss_sources()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
```

- [ ] **Step 6: Update endpoint startup logging in `api_server.py`**

Insert this print line after the existing `GET /api/sources` startup log:

```python
    print(f"   GET /api/rss-sources - RSS source catalog and sync status", file=sys.stderr)
```

- [ ] **Step 7: Create `src/app/api/rss-sources/route.ts`**

```typescript
import { NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8001";

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/rss-sources`, {
      cache: "no-store",
    });
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch RSS sources:", error);
    return NextResponse.json(
      {
        sources: [],
        total_sources: 0,
        enabled_sources: 0,
        active_sources: 0,
        error: "Failed to fetch RSS sources",
      },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 8: Add RSS types to `src/types/index.ts`**

Append these interfaces to the end of `src/types/index.ts`:

```typescript
export interface RssSource {
  id: string;
  name: string;
  short_name: string;
  kind: string;
  kind_label: string;
  source: string;
  source_type: string;
  category: string;
  feed_url: string;
  homepage: string;
  enabled: boolean;
  trust_level: string;
  collection_method: string;
  description: string;
  last_sync_at: string;
  items_found: number;
  items_new: number;
  items_updated: number;
  status: string;
  error_message: string;
}

export interface RssSourcesResponse {
  sources: RssSource[];
  total_sources: number;
  enabled_sources: number;
  active_sources: number;
  error?: string;
}
```

- [ ] **Step 9: Run backend data smoke test**

Run:

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from db import init_db, query_rss_sources
init_db()
data = query_rss_sources()
assert len(data['sources']) == 3
assert data['sources'][0]['feed_url']
assert 'last_sync_at' in data['sources'][0]
print('rss sources api data ok')
PY
```

Expected: PASS and prints `rss sources api data ok`.

- [ ] **Step 10: Run TypeScript check**

Run:

```bash
npm run typecheck
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 11: Commit**

```bash
git add scripts/db.py api_server.py src/app/api/rss-sources/route.ts src/types/index.ts
git commit -m "feat: expose RSS source status API"
```

---

### Task 5: Add RSS source navigation page

**Files:**
- Modify: `src/components/layout/Sidebar.tsx`
- Modify: `src/app/page.tsx`
- Create: `src/app/rss-sources/page.tsx`

- [ ] **Step 1: Write failing static smoke test**

Run this before modifying frontend files:

```bash
python - <<'PY'
from pathlib import Path
sidebar = Path('src/components/layout/Sidebar.tsx').read_text(encoding='utf-8')
assert 'rss-sources' in sidebar
assert 'RSS 订阅源' in sidebar
page = Path('src/app/rss-sources/page.tsx')
assert page.exists()
print('rss page static links ok')
PY
```

Expected: FAIL with `AssertionError`.

- [ ] **Step 2: Modify `src/components/layout/Sidebar.tsx` props**

Replace:

```typescript
interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
```

With:

```typescript
type SidebarActiveKey = "home" | "rss-sources";

interface SidebarProps {
  className?: string;
  active?: SidebarActiveKey;
}

export function Sidebar({ className, active = "home" }: SidebarProps) {
```

- [ ] **Step 3: Make the home link active conditionally in `Sidebar.tsx`**

Replace:

```typescript
className="side-link side-link-active"
```

With:

```typescript
className={cn("side-link", active === "home" && "side-link-active")}
```

- [ ] **Step 4: Add RSS subscription link in `Sidebar.tsx`**

Replace the disabled “信源提报” button block:

```typescript
          <button
            type="button"
            className="side-link text-left"
            disabled
            title="后续可接入信源管理"
          >
            <Rss className="side-icon" />
            <span>信源提报</span>
          </button>
```

With:

```typescript
          <Link
            href="/rss-sources"
            onClick={() => setOpen(false)}
            className={cn("side-link", active === "rss-sources" && "side-link-active")}
          >
            <Rss className="side-icon" />
            <span>RSS 订阅源</span>
          </Link>
```

- [ ] **Step 5: Modify `src/app/page.tsx` sidebar usage**

Replace:

```typescript
      <Sidebar />
```

With:

```typescript
      <Sidebar active="home" />
```

- [ ] **Step 6: Create `src/app/rss-sources/page.tsx`**

```typescript
"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, ExternalLink, Radio, Rss } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import type { RssSource, RssSourcesResponse } from "@/types";

function formatSyncTime(value: string): string {
  if (!value) return "暂无同步";
  return value.replace("T", " ").replace("Z", "").slice(0, 19);
}

function statusLabel(source: RssSource): string {
  if (!source.last_sync_at) return "待同步";
  return source.status === "success" ? "正常" : "异常";
}

function statusClass(source: RssSource): string {
  if (!source.last_sync_at) return "border-[var(--border-strong)] text-[var(--text-1)]";
  if (source.status === "success") return "border-emerald-400/30 text-emerald-300";
  return "border-rose-400/30 text-rose-300";
}

export default function RssSourcesPage() {
  const [data, setData] = useState<RssSourcesResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchSources() {
      setLoading(true);
      try {
        const response = await fetch("/api/rss-sources");
        const nextData: RssSourcesResponse = await response.json();
        if (!cancelled) setData(nextData);
      } catch (error) {
        console.error("Failed to fetch RSS sources:", error);
        if (!cancelled) {
          setData({ sources: [], total_sources: 0, enabled_sources: 0, active_sources: 0, error: "Failed to fetch RSS sources" });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchSources();
    return () => {
      cancelled = true;
    };
  }, []);

  const sources = data?.sources || [];
  const latestError = useMemo(
    () => sources.find((source) => source.error_message)?.error_message || data?.error || "",
    [data?.error, sources]
  );

  return (
    <div className="app-shell text-[var(--foreground)]">
      <Sidebar active="rss-sources" />

      <main className="app-main">
        <div className="app-main-inner">
          <section className="page-header-feed mb-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="page-title">RSS 订阅源</h1>
                <p className="page-subtitle">
                  查看当前用于 RSS-first 论文采集的订阅源、启用状态和最近同步结果。
                </p>
              </div>
              <span className="source-sync-pill">
                <Activity className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                {loading ? "加载中" : `${data?.active_sources ?? 0}/${data?.enabled_sources ?? 0} 活跃`}
              </span>
            </div>
          </section>

          {latestError && (
            <div className="mb-4 rounded-xl border border-rose-400/25 bg-rose-500/10 p-4 text-sm text-rose-200">
              <div className="flex items-start gap-2">
                <AlertTriangle className="mt-0.5 h-4 w-4 flex-none" />
                <span>{latestError}</span>
              </div>
            </div>
          )}

          <section className="grid gap-3">
            {sources.map((source) => (
              <article
                key={source.id}
                className="rounded-2xl border border-[var(--border)] bg-[var(--surface-elevated)] p-4 shadow-[var(--shadow-soft)]"
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="min-w-0">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[rgba(var(--accent-cyan-rgb),0.24)] bg-[rgba(var(--accent-cyan-rgb),0.08)] text-xs font-bold text-[var(--accent-cyan-fg)]">
                        <Rss className="h-4 w-4" />
                      </span>
                      <div>
                        <h2 className="text-base font-bold text-[var(--text-0)]">{source.short_name}</h2>
                        <p className="text-xs text-[var(--text-1)]">{source.name}</p>
                      </div>
                    </div>
                    <p className="text-sm leading-6 text-[var(--text-1)]">{source.description}</p>
                  </div>

                  <div className={`inline-flex w-fit items-center gap-2 rounded-full border px-3 py-1 text-xs font-bold ${statusClass(source)}`}>
                    {source.status === "success" ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Radio className="h-3.5 w-3.5" />}
                    {statusLabel(source)}
                  </div>
                </div>

                <div className="mt-4 grid gap-2 md:grid-cols-4">
                  <div className="rounded-xl border border-[var(--border-soft)] bg-[var(--surface-0)] p-3">
                    <p className="text-[10px] uppercase tracking-wide text-[var(--text-2)]">类型</p>
                    <p className="mt-1 text-sm font-semibold text-[var(--text-0)]">{source.kind_label}</p>
                  </div>
                  <div className="rounded-xl border border-[var(--border-soft)] bg-[var(--surface-0)] p-3">
                    <p className="text-[10px] uppercase tracking-wide text-[var(--text-2)]">最近同步</p>
                    <p className="mt-1 text-sm font-semibold text-[var(--text-0)]">{formatSyncTime(source.last_sync_at)}</p>
                  </div>
                  <div className="rounded-xl border border-[var(--border-soft)] bg-[var(--surface-0)] p-3">
                    <p className="text-[10px] uppercase tracking-wide text-[var(--text-2)]">发现 / 新增 / 更新</p>
                    <p className="mt-1 text-sm font-semibold text-[var(--text-0)]">
                      {source.items_found} / {source.items_new} / {source.items_updated}
                    </p>
                  </div>
                  <div className="rounded-xl border border-[var(--border-soft)] bg-[var(--surface-0)] p-3">
                    <p className="text-[10px] uppercase tracking-wide text-[var(--text-2)]">启用状态</p>
                    <p className="mt-1 text-sm font-semibold text-[var(--text-0)]">{source.enabled ? "已启用" : "已停用"}</p>
                  </div>
                </div>

                {source.error_message && (
                  <p className="mt-3 rounded-xl border border-rose-400/20 bg-rose-500/10 p-3 text-xs text-rose-200">
                    {source.error_message}
                  </p>
                )}

                <div className="mt-4 flex flex-col gap-2 text-xs text-[var(--text-2)] md:flex-row md:items-center md:justify-between">
                  <a
                    href={source.feed_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="min-w-0 truncate font-mono text-[var(--accent-cyan-fg)] hover:underline"
                    title={source.feed_url}
                  >
                    {source.feed_url}
                  </a>
                  <a
                    href={source.homepage}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex flex-none items-center gap-1 text-[var(--text-1)] hover:text-[var(--text-0)]"
                  >
                    来源主页
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </div>
              </article>
            ))}

            {!loading && sources.length === 0 && (
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-card)] p-8 text-center text-sm text-[var(--text-1)]">
                暂无 RSS 订阅源配置
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 7: Run static smoke test**

Run:

```bash
python - <<'PY'
from pathlib import Path
sidebar = Path('src/components/layout/Sidebar.tsx').read_text(encoding='utf-8')
assert 'rss-sources' in sidebar
assert 'RSS 订阅源' in sidebar
page = Path('src/app/rss-sources/page.tsx')
assert page.exists()
print('rss page static links ok')
PY
```

Expected: PASS and prints `rss page static links ok`.

- [ ] **Step 8: Run TypeScript check**

Run:

```bash
npm run typecheck
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 9: Commit**

```bash
git add src/components/layout/Sidebar.tsx src/app/page.tsx src/app/rss-sources/page.tsx
git commit -m "feat: add RSS source status page"
```

---

### Task 6: End-to-end verification

**Files:**
- No planned source edits. Fix defects in the files introduced above if any command fails.

- [ ] **Step 1: Run RSS parser and live feed checks**

Run:

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from sources.rss_feeds import collect_by_source
results = collect_by_source(days_back=14)
assert len(results) == 3
for result in results:
    print(result['source']['id'], len(result['items']), result['error'])
    assert not result['error']
    assert len(result['items']) > 0
print('live RSS feeds ok')
PY
```

Expected: PASS and item counts for all three feeds.

- [ ] **Step 2: Run RSS collection into SQLite**

Run:

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from db import init_db, query_rss_sources
from collect import collect_rss_sources
init_db()
stats = collect_rss_sources(days_back=14)
print('stats', stats)
data = query_rss_sources()
for source in data['sources']:
    print(source['id'], source['status'], source['items_found'], source['items_new'], source['items_updated'], source['error_message'])
    assert source['last_sync_at']
    assert source['status'] == 'success'
assert stats['found'] > 0
PY
```

Expected: PASS. `items_new` can be zero on repeated runs, but `items_found` and aggregate `found` must be greater than zero.

- [ ] **Step 3: Run frontend checks**

Run:

```bash
npm run lint
npm run typecheck
npm run build
```

Expected: all three commands PASS.

- [ ] **Step 4: Start backend API**

Run in a background terminal:

```bash
python api_server.py 8001
```

Expected: stderr includes `API server started on http://localhost:8001` and lists `GET /api/rss-sources`.

- [ ] **Step 5: Start Next.js dev server**

Run in a second background terminal:

```bash
npm run dev
```

Expected: Next.js starts successfully and prints a local URL, usually `http://localhost:3000`.

- [ ] **Step 6: Verify the UI manually in a browser**

Open `http://localhost:3000/rss-sources` and verify:

- Sidebar contains a real `RSS 订阅源` nav item.
- `RSS 订阅源` nav item is highlighted on the RSS page.
- Page shows exactly three source cards: arXiv RT+AI, Red Journal, Green Journal.
- Each card shows an RSS/Atom URL, enabled status, latest sync time, found/new/updated counts, and source homepage link.
- No card shows the unstable `redjournal.org/current.rss` URL.

- [ ] **Step 7: Verify homepage still works**

Open `http://localhost:3000/` and verify:

- Sidebar highlights `精选`.
- Existing feed loads.
- Refresh button still triggers `/api/refresh`.
- RSS-collected papers appear in the feed after collection completes.

- [ ] **Step 8: Commit verification fixes if needed**

If no fixes were needed, skip this step. If fixes were made, commit only the touched files:

```bash
git add <fixed-files>
git commit -m "fix: stabilize RSS source verification"
```

---

## Self-Review Checklist

- Spec coverage: Tasks cover RSS source config, three verified sources, RSS/Atom parsing, collection priority, per-source sync status, backend API, Next.js proxy, sidebar navigation, read-only page, error display, and verification.
- Placeholder scan: No TBD/TODO placeholders remain; all code steps include concrete snippets or exact replacements.
- Type consistency: Python API returns `last_sync_at`, `items_found`, `items_new`, `items_updated`, `status`, and `error_message`; TypeScript interfaces and page code use the same names.
- Scope control: Page is read-only; no edit/delete/toggle controls are included in first phase.
