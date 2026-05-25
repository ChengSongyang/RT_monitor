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
        item['summary_cn'] = item['ai'].get('summary_cn', '')
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
