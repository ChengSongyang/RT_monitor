# Data Layer Refactoring — SQLite + Unified Schema

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace flat JSON files with SQLite, define a unified content schema, add paper report MD rendering, and make it easy to add new data sources.

**Architecture:** SQLite database (`data/rt_monitor.db`) stores all content. Python `db.py` provides data access layer. Each data source is a standalone script outputting unified format. Reports stored as MD files in `reports/{year}/{month}/{source}/{id}.md`.

**Tech Stack:** Python 3 (sqlite3 built-in), Next.js (react-markdown for MD rendering)

---

## File Map

```
Create:
  scripts/db.py                          — SQLite schema + data access layer
  scripts/sources/__init__.py             — Source registry
  scripts/sources/arxiv.py               — arXiv collector (migrated)
  scripts/sources/pubmed.py              — PubMed collector (migrated)
  scripts/sources/google_news.py         — Google News collector (migrated)
  scripts/sources/semantic_scholar.py    — Semantic Scholar collector (migrated)
  scripts/collect.py                     — Unified collection entry point
  scripts/reports/generate_report.py     — Report MD file generator
  src/app/reports/[year]/[month]/[source]/[id]/page.tsx — MD rendering page

Modify:
  api_server.py                          — Read from SQLite instead of JSON
  src/types/index.ts                     — Update NewsItem meta fields
  src/components/feed/NewsCard.tsx       — Add "查看解读" button for papers
  src/app/api/items/route.ts             — Support source_type filter
  data/news.json                         — Will be replaced by SQLite
  data/papers.json                       — Will be replaced by SQLite

Keep (deprecated):
  scripts/fetch_radiotherapy_news.py     — Replaced by scripts/sources/google_news.py
  scripts/monitor_radiotherapy_ai.py     — Replaced by scripts/sources/*.py
```

---

## Task 1: Database Schema and Access Layer

**Files:**
- Create: `scripts/db.py`

- [ ] **Step 1: Create db.py with schema and CRUD operations**

```python
#!/usr/bin/env python3
"""
SQLite 数据库操作层
统一管理放射治疗领域内容数据
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'rt_monitor.db')

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS content (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  summary TEXT DEFAULT '',
  content TEXT DEFAULT '',
  url TEXT DEFAULT '',

  source TEXT DEFAULT '',
  source_type TEXT DEFAULT 'news',
  source_user TEXT DEFAULT '',
  source_verified INTEGER DEFAULT 0,
  source_verified_reason TEXT DEFAULT '',

  date TEXT DEFAULT '',
  timestamp REAL DEFAULT 0,

  category TEXT DEFAULT 'industry_news',
  tags TEXT DEFAULT '[]',
  images TEXT DEFAULT '[]',

  meta TEXT DEFAULT '{}',
  ai TEXT DEFAULT '{}',
  extra TEXT DEFAULT '{}',

  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY,
  content_id TEXT NOT NULL,
  report_type TEXT DEFAULT 'ai_analysis',
  file_path TEXT NOT NULL,
  year INTEGER,
  month INTEGER,
  source TEXT,
  md_content TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (content_id) REFERENCES content(id)
);

CREATE TABLE IF NOT EXISTS sync_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  items_found INTEGER DEFAULT 0,
  items_new INTEGER DEFAULT 0,
  items_updated INTEGER DEFAULT 0,
  status TEXT DEFAULT 'success',
  error_message TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_content_date ON content(date);
CREATE INDEX IF NOT EXISTS idx_content_category ON content(category);
CREATE INDEX IF NOT EXISTS idx_content_source ON content(source);
CREATE INDEX IF NOT EXISTS idx_content_source_type ON content(source_type);
CREATE INDEX IF NOT EXISTS idx_content_timestamp ON content(timestamp);
CREATE INDEX IF NOT EXISTS idx_reports_content_id ON reports(content_id);
"""


def get_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def upsert_content(items: List[Dict]) -> Dict:
    conn = get_db()
    stats = {'found': len(items), 'new': 0, 'updated': 0}

    for item in items:
        existing = conn.execute(
            'SELECT id FROM content WHERE id = ?', (item['id'],)
        ).fetchone()

        tags = json.dumps(item.get('tags', []), ensure_ascii=False)
        images = json.dumps(item.get('images', []), ensure_ascii=False)
        meta = json.dumps(item.get('meta', {}), ensure_ascii=False)
        ai = json.dumps(item.get('ai', {}), ensure_ascii=False)
        extra = json.dumps(item.get('extra', {}), ensure_ascii=False)

        if existing:
            conn.execute('''UPDATE content SET
                title=?, summary=?, content=?, url=?,
                source=?, source_type=?, source_user=?, source_verified=?,
                source_verified_reason=?, date=?, timestamp=?, category=?,
                tags=?, images=?, meta=?, ai=?, extra=?,
                updated_at=datetime('now')
                WHERE id=?''', (
                item['title'], item.get('summary', ''), item.get('content', ''),
                item.get('url', ''), item.get('source', ''),
                item.get('source_type', 'news'),
                item.get('source_user', ''),
                1 if item.get('source_verified') else 0,
                item.get('source_verified_reason', ''),
                item.get('date', ''), item.get('timestamp', 0),
                item.get('category', 'industry_news'),
                tags, images, meta, ai, extra,
                item['id']
            ))
            stats['updated'] += 1
        else:
            conn.execute('''INSERT INTO content
                (id, title, summary, content, url,
                source, source_type, source_user, source_verified,
                source_verified_reason, date, timestamp, category,
                tags, images, meta, ai, extra)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                item['id'], item['title'], item.get('summary', ''),
                item.get('content', ''), item.get('url', ''),
                item.get('source', ''), item.get('source_type', 'news'),
                item.get('source_user', ''),
                1 if item.get('source_verified') else 0,
                item.get('source_verified_reason', ''),
                item.get('date', ''), item.get('timestamp', 0),
                item.get('category', 'industry_news'),
                tags, images, meta, ai, extra
            ))
            stats['new'] += 1

    conn.commit()
    conn.close()
    return stats


def query_content(
    category: Optional[str] = None,
    source: Optional[str] = None,
    source_type: Optional[str] = None,
    search: Optional[str] = None,
    is_featured: Optional[bool] = None,
    page: int = 1,
    limit: int = 20
) -> Dict:
    conn = get_db()
    conditions = []
    params = []

    if category:
        conditions.append('category = ?')
        params.append(category)
    if source:
        conditions.append('source = ?')
        params.append(source)
    if source_type:
        conditions.append('source_type = ?')
        params.append(source_type)
    if search:
        conditions.append('(title LIKE ? OR summary LIKE ? OR content LIKE ?)')
        like = f'%{search}%'
        params.extend([like, like, like])
    if is_featured is not None:
        conditions.append("json_extract(ai, '$.is_featured') = ?")
        params.append(1 if is_featured else 0)

    where = ' AND '.join(conditions) if conditions else '1=1'
    count = conn.execute(f'SELECT COUNT(*) FROM content WHERE {where}', params).fetchone()[0]

    total_pages = max(1, (count + limit - 1) // limit)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * limit

    rows = conn.execute(
        f'SELECT * FROM content WHERE {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?',
        params + [limit, offset]
    ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        item['tags'] = json.loads(item['tags']) if item['tags'] else []
        item['images'] = json.loads(item['images']) if item['images'] else []
        item['meta'] = json.loads(item['meta']) if item['meta'] else {}
        item['ai'] = json.loads(item['ai']) if item['ai'] else {}
        item['extra'] = json.loads(item['extra']) if item['extra'] else {}
        item['source_verified'] = bool(item['source_verified'])
        item['recommendation_score'] = item['ai'].get('score', 0)
        item['is_featured'] = item['ai'].get('is_featured', False)
        item['recommendation_reason'] = item['ai'].get('recommendation_reason', '')
        item['quoted_text'] = item['extra'].get('quoted_text', '')
        item['quoted_author'] = item['extra'].get('quoted_author', '')
        item['journal'] = item['meta'].get('journal', '')
        item['pdf_url'] = item['meta'].get('pdf_url', '')
        item['html_url'] = item['meta'].get('html_url', '')
        item['report_path'] = item['meta'].get('report_path', '')
        items.append(item)

    conn.close()
    return {
        'items': items,
        'total': count,
        'page': page,
        'totalPages': total_pages,
        'limit': limit,
    }


def get_report(content_id: str) -> Optional[Dict]:
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM reports WHERE content_id = ?', (content_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_report(content_id: str, report_type: str, file_path: str, md_content: str):
    conn = get_db()
    # Extract year, month, source from file_path
    parts = file_path.replace('\\', '/').split('/')
    year = int(parts[-4]) if len(parts) >= 4 else datetime.now().year
    month = int(parts[-3]) if len(parts) >= 4 else datetime.now().month
    source = parts[-2] if len(parts) >= 4 else 'unknown'

    conn.execute('''INSERT OR REPLACE INTO reports
        (id, content_id, report_type, file_path, year, month, source, md_content)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (content_id, content_id, report_type, file_path, year, month, source, md_content)
    )
    conn.commit()
    conn.close()


def log_sync(source: str, items_found: int, items_new: int, items_updated: int,
             status: str = 'success', error_message: str = ''):
    conn = get_db()
    conn.execute('''INSERT INTO sync_log
        (source, items_found, items_new, items_updated, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (source, items_found, items_new, items_updated, status, error_message)
    )
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print(f"Database initialized at {DB_PATH}")
```

- [ ] **Step 2: Commit**

```bash
git add scripts/db.py
git commit -m "feat: add SQLite database schema and data access layer"
```

---

## Task 2: Source Collectors

**Files:**
- Create: `scripts/sources/__init__.py`
- Create: `scripts/sources/arxiv.py`
- Create: `scripts/sources/pubmed.py`
- Create: `scripts/sources/google_news.py`
- Create: `scripts/sources/semantic_scholar.py`

- [ ] **Step 1: Create source __init__.py with base utilities**

```python
"""数据源采集器"""
import json
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
```

- [ ] **Step 2: Create arxiv.py**

```python
"""arXiv 数据源采集器"""
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import time
from . import fetch_url, make_content_id, deduplicate


def collect(days_back: int = 7, max_results: int = 50) -> List[Dict]:
    papers = []
    ns = {'a': 'http://www.w3.org/2005/Atom'}

    queries = [
        'all:radiotherapy+AND+all:large+language+model',
        'all:radiotherapy+AND+all:deep+learning',
        'all:radiation+therapy+AND+all:transformer',
        'all:radiation+oncology+AND+all:artificial+intelligence',
        'all:radiotherapy+AND+all:foundation+model',
        'all:radiotherapy+AND+all:segmentation+AND+cat:cs.CV',
    ]

    seen_ids = set()
    for query in queries:
        url = f"https://export.arxiv.org/api/query?search_query={query}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        data = fetch_url(url)
        if not data:
            continue

        try:
            root = ET.fromstring(data)
            for entry in root.findall('a:entry', ns):
                arxiv_id = entry.find('a:id', ns).text.strip().split('/abs/')[-1]
                base_id = arxiv_id.split('v')[0]
                if base_id in seen_ids:
                    continue
                seen_ids.add(base_id)

                published = entry.find('a:published', ns).text[:10]
                pub_date = datetime.strptime(published, '%Y-%m-%d')
                if pub_date < datetime.now() - timedelta(days=days_back):
                    continue

                title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
                summary = entry.find('a:summary', ns).text.strip().replace('\n', ' ')
                authors = ', '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns)[:5])
                cats = ', '.join(c.get('term') for c in entry.findall('a:category', ns))

                papers.append({
                    'id': make_content_id('arxiv', base_id),
                    'title': title,
                    'summary': summary[:200] + ('...' if len(summary) > 200 else ''),
                    'content': summary,
                    'url': f"https://arxiv.org/abs/{base_id}",
                    'source': 'arXiv',
                    'source_type': 'paper',
                    'source_user': authors,
                    'source_verified': True,
                    'source_verified_reason': '学术论文',
                    'date': published,
                    'timestamp': pub_date.timestamp(),
                    'category': 'paper',
                    'tags': ['论文', 'arXiv'] + [t.strip() for t in cats.split(',')[:2]],
                    'images': [],
                    'meta': {
                        'authors': authors,
                        'journal': 'arXiv',
                        'pdf_url': f"https://arxiv.org/pdf/{base_id}",
                        'html_url': f"https://arxiv.org/html/{base_id}",
                        'doi': '',
                    },
                    'ai': {'score': 70, 'is_featured': False, 'recommendation_reason': ''},
                    'extra': {},
                })
        except Exception as e:
            print(f"  [WARN] Parse error for arXiv: {e}", file=sys.stderr)
        time.sleep(4)

    return deduplicate(papers)
```

- [ ] **Step 3: Create pubmed.py, google_news.py, semantic_scholar.py** — migrate from existing scripts using same pattern. Each exports a `collect(days_back, max_results) -> List[Dict]` function returning unified schema items.

- [ ] **Step 4: Commit**

```bash
git add scripts/sources/
git commit -m "feat: add unified source collectors for arxiv, pubmed, google_news, semantic_scholar"
```

---

## Task 3: Unified Collection Entry Point

**Files:**
- Create: `scripts/collect.py`

- [ ] **Step 1: Create collect.py**

```python
#!/usr/bin/env python3
"""
统一数据采集入口
从各数据源采集数据，写入 SQLite
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import init_db, upsert_content, log_sync
from sources import arxiv, pubmed, google_news, semantic_scholar


SOURCES = [
    ('arxiv', arxiv),
    ('pubmed', pubmed),
    ('google_news', google_news),
    ('semantic_scholar', semantic_scholar),
]


def collect_all(days_back: int = 7):
    init_db()
    total_stats = {'found': 0, 'new': 0, 'updated': 0}

    for name, source in SOURCES:
        print(f"📡 采集 {name}...", file=sys.stderr)
        try:
            items = source.collect(days_back=days_back)
            stats = upsert_content(items)
            log_sync(name, stats['found'], stats['new'], stats['updated'])
            total_stats['found'] += stats['found']
            total_stats['new'] += stats['new']
            total_stats['updated'] += stats['updated']
            print(f"  ✅ {name}: {stats['new']} new, {stats['updated']} updated", file=sys.stderr)
        except Exception as e:
            log_sync(name, 0, 0, 0, 'error', str(e))
            print(f"  ❌ {name} failed: {e}", file=sys.stderr)

    print(f"\n📊 总计: {total_stats['found']} found, {total_stats['new']} new, {total_stats['updated']} updated", file=sys.stderr)
    return total_stats


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=7)
    args = parser.parse_args()
    collect_all(days_back=args.days)
```

- [ ] **Step 2: Commit**

```bash
git add scripts/collect.py
git commit -m "feat: add unified collection entry point"
```

---

## Task 4: Backend — Read from SQLite

**Files:**
- Modify: `api_server.py`

- [ ] **Step 1: Rewrite api_server.py to use db.py**

Replace the data loading and query logic in `api_server.py`:
- Remove `load_papers()`, `load_news()`, `save_papers()`, `save_news()`
- Remove `get_combined_data()` with its paper-to-news conversion
- Import and use `db.py`: `init_db()`, `query_content()`, `upsert_content()`
- The `/api/items` endpoint calls `query_content()` from db.py
- The `/api/refresh` endpoint calls `collect_all()` from collect.py
- Add `/api/reports/{content_id}` endpoint to serve report data

- [ ] **Step 2: Commit**

```bash
git add api_server.py
git commit -m "feat: rewrite api_server to use SQLite database"
```

---

## Task 5: TypeScript Types Update

**Files:**
- Modify: `src/types/index.ts`

- [ ] **Step 1: Add meta type and update NewsItem**

Add to `src/types/index.ts`:

```ts
export interface PaperMeta {
  authors?: string;
  journal?: string;
  pdf_url?: string;
  html_url?: string;
  doi?: string;
  report_path?: string;
  report_type?: string;
  citation_count?: number;
  [key: string]: unknown;
}

export interface WechatMeta {
  account_name?: string;
  account_avatar?: string;
  account_id?: string;
  [key: string]: unknown;
}

export interface AIEnrichment {
  score: number;
  is_featured: boolean;
  recommendation_reason: string;
}

export interface NewsItemMeta {
  quoted_text?: string;
  quoted_author?: string;
  [key: string]: unknown;
}
```

Update the `NewsItem` interface `meta` field from loose typing to use the specific interfaces.

- [ ] **Step 2: Commit**

```bash
git add src/types/index.ts
git commit -m "feat: add typed meta interfaces for different source types"
```

---

## Task 6: MD Rendering Page

**Files:**
- Install: `react-markdown`
- Create: `src/app/reports/[year]/[month]/[source]/[id]/page.tsx`

- [ ] **Step 1: Install react-markdown**

```bash
npm install react-markdown
```

- [ ] **Step 2: Create the report page**

```tsx
import ReactMarkdown from "react-markdown";

interface ReportPageProps {
  params: Promise<{ year: string; month: string; source: string; id: string }>;
}

async function getReport(year: string, month: string, source: string, id: string) {
  // Try to fetch report content from API
  try {
    const res = await fetch(`${process.env.API_BASE_URL || 'http://localhost:8001'}/api/reports/${id}`, {
      cache: 'no-store',
    });
    if (res.ok) {
      const data = await res.json();
      return data.md_content || '';
    }
  } catch {}
  return '';
}

export default async function ReportPage({ params }: ReportPageProps) {
  const { year, month, source, id } = await params;
  const content = await getReport(year, month, source, id);

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <div className="mx-auto max-w-[800px] px-6 py-8">
        <a href="/" className="text-sm text-[var(--muted-foreground)] hover:text-[var(--accent)] mb-6 inline-block">
          ← 返回精选
        </a>
        {content ? (
          <article className="prose prose-invert max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </article>
        ) : (
          <div className="text-center py-16 text-[var(--muted-foreground)]">
            <p>暂无解读报告</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Add API endpoint for reports in api_server.py**

Add `GET /api/reports/{content_id}` that calls `get_report()` from db.py.

- [ ] **Step 4: Commit**

```bash
git add src/app/reports/ package.json package-lock.json
git commit -m "feat: add MD report rendering page with react-markdown"
```

---

## Task 7: NewsCard "查看解读" Button

**Files:**
- Modify: `src/components/feed/NewsCard.tsx`

- [ ] **Step 1: Add report link button**

In `NewsCard.tsx`, after the recommendation_reason section, add:

```tsx
{item.meta?.report_path && (
  <a
    href={`/reports/${item.date.substring(0,4)}/${item.date.substring(5,7)}/${item.source}/${item.id}`}
    className="mt-2 inline-flex items-center gap-1 text-xs text-[var(--accent)] hover:underline"
  >
    查看解读 →
  </a>
)}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/feed/NewsCard.tsx
git commit -m "feat: add report link button to NewsCard for papers"
```

---

## Task 8: Migrate Existing Data

- [ ] **Step 1: Create migration script**

```python
#!/usr/bin/env python3
"""从旧 JSON 格式迁移到 SQLite"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from db import init_db, upsert_content

def migrate():
    init_db()
    
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    # Migrate news
    news_file = os.path.join(data_dir, 'news.json')
    if os.path.exists(news_file):
        with open(news_file, 'r', encoding='utf-8') as f:
            news = json.load(f)
        if news:
            stats = upsert_content(news)
            print(f"Migrated {stats['new']} news items")
    
    # Migrate papers
    papers_file = os.path.join(data_dir, 'papers.json')
    if os.path.exists(papers_file):
        with open(papers_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        if papers:
            # Convert old paper format to unified format
            converted = []
            for p in papers:
                converted.append({
                    'id': p.get('id', ''),
                    'title': p.get('title', ''),
                    'summary': p.get('abstract', '')[:200],
                    'content': p.get('abstract', ''),
                    'url': p.get('url', ''),
                    'source': p.get('source', ''),
                    'source_type': 'paper',
                    'source_user': p.get('authors', ''),
                    'source_verified': True,
                    'source_verified_reason': '学术论文',
                    'date': p.get('date', ''),
                    'timestamp': 0,
                    'category': 'paper',
                    'tags': ['论文'],
                    'images': [],
                    'meta': {
                        'authors': p.get('authors', ''),
                        'journal': p.get('journal', ''),
                        'pdf_url': p.get('pdf_url', ''),
                        'html_url': p.get('html_url', ''),
                    },
                    'ai': {'score': 70, 'is_featured': False, 'recommendation_reason': ''},
                    'extra': {},
                })
            stats = upsert_content(converted)
            print(f"Migrated {stats['new']} papers")

if __name__ == '__main__':
    migrate()
```

- [ ] **Step 2: Run migration**

```bash
python scripts/migrate_json_to_sqlite.py
```

- [ ] **Step 3: Commit**

```bash
git add scripts/migrate_json_to_sqlite.py
git commit -m "feat: add JSON to SQLite migration script"
```

---

## Task 9: Verify Full Application

- [ ] **Step 1: Initialize database and collect sample data**

```bash
python scripts/collect.py --days 7
```

- [ ] **Step 2: Run typecheck**

```bash
npm run typecheck
```

- [ ] **Step 3: Run full build**

```bash
npm run build
```

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve issues from data layer refactoring"
```
