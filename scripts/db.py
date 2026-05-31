#!/usr/bin/env python3
"""
SQLite 数据库操作层
统一管理放射治疗领域内容数据
"""
import sqlite3
import json
import os
import re
from typing import List, Dict, Optional, Any
from datetime import datetime

from source_catalog import (
    SOURCE_CATALOG,
    SOURCE_KIND_LABELS,
    find_source_by_name,
    get_source,
    infer_source,
    iter_sources_by_kind,
    source_catalog_summary,
    source_filter_terms,
)
from rss_source_catalog import RSS_SOURCES

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


def _json_load(value: Any, fallback: Any) -> Any:
    if value is None or value == '':
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return fallback


def _slugify_path(value: str) -> str:
    value = (value or '').strip().lower()
    value = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '-', value)
    return re.sub(r'-+', '-', value).strip('-') or 'unknown'


def _parse_year_month(date_str: str) -> tuple[int, int]:
    date_str = (date_str or '').strip()
    now = datetime.now()

    patterns = (
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y-%m',
        '%Y %b %d',
        '%Y %B %d',
        '%Y %b',
        '%Y %B',
        '%b %d, %Y',
        '%B %d, %Y',
    )
    for pattern in patterns:
        try:
            parsed = datetime.strptime(date_str[:max(len(date_str), len(pattern))], pattern)
            return parsed.year, parsed.month
        except Exception:
            continue

    if len(date_str) >= 4 and date_str[:4].isdigit():
        return int(date_str[:4]), now.month
    return now.year, now.month


def _core_journal_source(journal: str, fallback: str) -> str:
    journal_lower = (journal or '').lower()
    if (
        'int j radiat oncol biol phys' in journal_lower
        or 'international journal of radiation oncology' in journal_lower
        or 'ijrobp' in journal_lower
        or 'red journal' in journal_lower
    ):
        return 'IJROBP'
    if 'radiother oncol' in journal_lower or 'radiotherapy and oncology' in journal_lower or 'green journal' in journal_lower:
        return 'Radiotherapy and Oncology'
    return fallback


def _content_id(source: str, raw_id: str, url: str = '') -> str:
    raw_id = str(raw_id or '').strip()
    if raw_id:
        lowered = raw_id.lower()
        if lowered.startswith(('pubmed_', 'arxiv_', 'semantic_scholar_', 'tavily_', 'vendor_news_', 'guideline_')):
            return raw_id.replace(' ', '_')

    source_slug = _slugify_path(source).replace('-', '_')
    if not raw_id:
        raw_id = str(abs(hash(url or source or datetime.now().isoformat())))

    if source_slug in ('pubmed', 'arxiv', 'semantic_scholar', 'semanticscholar', 'ijrobp', 'radiotherapy_and_oncology'):
        return f'{source_slug}_{raw_id}'.replace(' ', '_')
    return raw_id.replace(' ', '_')


def _report_path_for(item: Dict[str, Any]) -> str:
    year, month = _parse_year_month(item.get('date', ''))
    source = _slugify_path(item.get('source') or item.get('source_type') or 'source')
    return f"reports/{year}/{month:02d}/{source}/{item['id']}"


def _normalize_content_item(item: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(item)

    meta = _json_load(normalized.get('meta'), {})
    ai = _json_load(normalized.get('ai'), {})
    extra = _json_load(normalized.get('extra'), {})

    for key in ('authors', 'journal', 'pdf_url', 'html_url', 'doi', 'citation_count', 'categories'):
        value = normalized.get(key)
        if value not in (None, '') and key not in meta:
            meta[key] = value

    source = normalized.get('source', '') or meta.get('source', '')
    journal = meta.get('journal') or normalized.get('journal') or ''
    source = _core_journal_source(journal, source)
    normalized['source'] = source

    normalized['id'] = _content_id(source, normalized.get('id', ''), normalized.get('url', ''))
    normalized['title'] = normalized.get('title') or normalized.get('title_cn') or '未命名内容'
    normalized['content'] = normalized.get('content') or normalized.get('abstract') or ''
    normalized['summary'] = normalized.get('summary') or normalized.get('description') or normalized['content'][:240]
    normalized['source_type'] = normalized.get('source_type') or ('paper' if normalized.get('category') == 'paper' else 'news')
    normalized['source_user'] = normalized.get('source_user') or normalized.get('authors') or meta.get('authors', '')
    normalized['source_verified'] = bool(normalized.get('source_verified'))
    normalized['source_verified_reason'] = normalized.get('source_verified_reason', '')
    normalized['date'] = normalized.get('date') or ''
    normalized['timestamp'] = normalized.get('timestamp') or 0
    normalized['category'] = normalized.get('category') or ('paper' if normalized['source_type'] == 'paper' else 'industry_news')

    tags = _json_load(normalized.get('tags'), [])
    if not isinstance(tags, list):
        tags = []
    for tag in (normalized['source'], journal, normalized['category']):
        if tag and tag not in tags:
            tags.append(tag)
    normalized['tags'] = tags[:12]

    images = _json_load(normalized.get('images'), [])
    normalized['images'] = images if isinstance(images, list) else []

    for flat_key in ('title_cn', 'summary_cn', 'recommendation_reason'):
        value = normalized.get(flat_key)
        if value and not ai.get(flat_key):
            ai[flat_key] = value
    if 'score' in normalized and 'score' not in ai:
        ai['score'] = normalized.get('score')
    if 'is_featured' in normalized and 'is_featured' not in ai:
        ai['is_featured'] = normalized.get('is_featured')

    report_md = normalized.pop('report_md', '') or normalized.pop('md_content', '')
    if report_md:
        meta['report_path'] = _report_path_for(normalized)
        meta['report_type'] = meta.get('report_type') or 'ai_analysis'
        normalized['_report_md'] = report_md

    normalized['meta'] = meta
    normalized['ai'] = ai
    normalized['extra'] = extra
    return normalized


def _decode_content_row(row: sqlite3.Row) -> Dict:
    item = dict(row)
    item['tags'] = _json_load(item.get('tags'), [])
    item['images'] = _json_load(item.get('images'), [])
    item['image_urls'] = item['images']
    item['meta'] = _json_load(item.get('meta'), {})
    item['ai'] = _json_load(item.get('ai'), {})
    item['extra'] = _json_load(item.get('extra'), {})
    item['source_verified'] = bool(item.get('source_verified'))
    item['recommendation_score'] = item['ai'].get('score', 0)
    item['hot_score'] = item['ai'].get('score', 0)
    item['is_featured'] = item['ai'].get('is_featured', False)
    item['recommendation_reason'] = item['ai'].get('recommendation_reason', '')
    item['title_cn'] = item['ai'].get('title_cn', '')
    item['summary_cn'] = item['ai'].get('summary_cn', '')
    item['quoted_text'] = item['extra'].get('quoted_text', '')
    item['quoted_author'] = item['extra'].get('quoted_author', '')
    item['journal'] = item['meta'].get('journal', '')
    item['pdf_url'] = item['meta'].get('pdf_url', '')
    item['html_url'] = item['meta'].get('html_url', '')
    item['report_path'] = item['meta'].get('report_path', '')
    item['content_type'] = item.get('category', 'industry_news')

    source_info = infer_source(item)
    item['source_info'] = source_info
    item['source_id'] = source_info.get('id', '')
    item['source_kind'] = source_info.get('kind', '')
    item['source_kind_label'] = source_info.get('kind_label', '')
    item['source_display_name'] = source_info.get('name', item.get('source', ''))
    item['source_short_name'] = source_info.get('short_name', item.get('source', ''))
    item['source_homepage'] = source_info.get('homepage', '')
    item['source_trust_level'] = source_info.get('trust_level', '')
    item['source_collection_method'] = source_info.get('collection_method', '')
    item['source_origin_host'] = source_info.get('origin_host', '')
    item['source_origin_url'] = source_info.get('origin_url', item.get('url', ''))
    item['source_note'] = source_info.get('note', '')
    item['mentioned_source'] = source_info.get('mentioned_source')
    item['mentioned_vendor'] = item['meta'].get('mentioned_vendor') or item['meta'].get('vendor', '')
    if not item['source_verified'] and source_info.get('trust_level') in ('high', 'official'):
        item['source_verified'] = True
        item['source_verified_reason'] = item['source_kind_label']
    return item


def _source_record_condition(source: Dict[str, Any]) -> tuple:
    terms = source_filter_terms(source)
    parts = ["json_extract(meta, '$.source_id') = ?"]
    params: List[Any] = [source['id']]

    if terms['names']:
        placeholders = ','.join(['?'] * len(terms['names']))
        parts.append(f"source IN ({placeholders})")
        params.extend(terms['names'])

    for domain in terms['domains']:
        parts.append('url LIKE ?')
        params.append(f'%{domain}%')

    return '(' + ' OR '.join(parts) + ')', params


def _append_source_filters(
    conditions: List[str],
    params: List[Any],
    source_id: Optional[str],
    source_kind: Optional[str],
):
    if source_id:
        source_record = get_source(source_id) or find_source_by_name(source_id)
        if source_record:
            condition, values = _source_record_condition(source_record)
            conditions.append(condition)
            params.extend(values)
        else:
            conditions.append("(source = ? OR json_extract(meta, '$.source_id') = ?)")
            params.extend([source_id, source_id])

    if source_kind:
        kind_parts = ["json_extract(meta, '$.source_kind') = ?"]
        kind_params: List[Any] = [source_kind]
        for source_record in iter_sources_by_kind(source_kind):
            condition, values = _source_record_condition(source_record)
            kind_parts.append(condition)
            kind_params.extend(values)
        conditions.append('(' + ' OR '.join(kind_parts) + ')')
        params.extend(kind_params)


def upsert_content(items: List[Dict]) -> Dict:
    conn = get_db()
    stats = {'found': len(items), 'new': 0, 'updated': 0}

    for raw_item in items:
        item = _normalize_content_item(raw_item)
        existing = conn.execute(
            'SELECT id FROM content WHERE id = ?',
            (item['id'],),
        ).fetchone()
        if not existing and item.get('url'):
            existing = conn.execute(
                'SELECT id FROM content WHERE url <> "" AND url = ?',
                (item.get('url', ''),),
            ).fetchone()
        if existing and existing['id'] != item['id']:
            item['id'] = existing['id']
            if item.get('_report_md'):
                item['meta']['report_path'] = _report_path_for(item)

        tags = json.dumps(item.get('tags', []), ensure_ascii=False)
        images = json.dumps(item.get('images', []), ensure_ascii=False)
        meta = json.dumps(item.get('meta', {}), ensure_ascii=False)
        ai = json.dumps(item.get('ai', {}), ensure_ascii=False)
        extra = json.dumps(item.get('extra', {}), ensure_ascii=False)
        report_md = item.get('_report_md', '')

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

        if report_md:
            report_path = item.get('meta', {}).get('report_path') or _report_path_for(item)
            year, month = _parse_year_month(item.get('date', ''))
            source_slug = _slugify_path(item.get('source', 'source'))
            conn.execute('''INSERT OR REPLACE INTO reports
                (id, content_id, report_type, file_path, year, month, source, md_content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
                item['id'],
                item['id'],
                item.get('meta', {}).get('report_type', 'ai_analysis'),
                report_path,
                year,
                month,
                source_slug,
                report_md,
            ))

    conn.commit()
    conn.close()
    return stats


def query_content(
    category: Optional[str] = None,
    source: Optional[str] = None,
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    source_kind: Optional[str] = None,
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
    _append_source_filters(conditions, params, source_id, source_kind)
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
        items.append(_decode_content_row(row))

    conn.close()
    return {
        'items': items,
        'total': count,
        'page': page,
        'totalPages': total_pages,
        'limit': limit,
    }


def _empty_source_card(source: Dict[str, Any]) -> Dict[str, Any]:
    card = dict(source)
    card['kind_label'] = SOURCE_KIND_LABELS.get(card.get('kind', ''), card.get('kind', '来源'))
    card['count'] = 0
    card['featured_count'] = 0
    card['latest_date'] = ''
    card['latest_timestamp'] = 0
    card['categories'] = {}
    card['source_types'] = {}
    card['origin_hosts'] = {}
    card['last_item'] = None
    return card


def _update_source_card(card: Dict[str, Any], item: Dict[str, Any]):
    card['count'] += 1
    if item.get('is_featured'):
        card['featured_count'] += 1

    category = item.get('category', 'unknown')
    card['categories'][category] = card['categories'].get(category, 0) + 1

    source_type = item.get('source_type', 'unknown')
    card['source_types'][source_type] = card['source_types'].get(source_type, 0) + 1

    origin_host = item.get('source_origin_host', '')
    if origin_host:
        card['origin_hosts'][origin_host] = card['origin_hosts'].get(origin_host, 0) + 1

    timestamp = item.get('timestamp') or 0
    if timestamp >= (card.get('latest_timestamp') or 0):
        card['latest_timestamp'] = timestamp
        card['latest_date'] = item.get('date', '')
        card['last_item'] = {
            'id': item.get('id'),
            'title': item.get('title', ''),
            'url': item.get('url', ''),
            'date': item.get('date', ''),
            'category': item.get('category', ''),
            'source_note': item.get('source_note', ''),
        }


def _recent_syncs(conn: sqlite3.Connection, limit: int = 12) -> List[Dict[str, Any]]:
    rows = conn.execute(
        'SELECT source, items_found, items_new, items_updated, status, error_message, created_at '
        'FROM sync_log ORDER BY created_at DESC LIMIT ?',
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def query_rss_sources() -> Dict[str, Any]:
    conn = get_db()

    latest_syncs: Dict[str, Dict[str, Any]] = {}
    rows = conn.execute(
        'SELECT source, items_found, items_new, items_updated, status, error_message, created_at '
        'FROM sync_log WHERE source IN ({}) ORDER BY created_at DESC, id DESC'.format(
            ','.join(['?'] * len(RSS_SOURCES))
        ),
        [source['id'] for source in RSS_SOURCES],
    ).fetchall()
    for row in rows:
        source_id = row['source']
        if source_id not in latest_syncs:
            latest_syncs[source_id] = dict(row)

    sources: List[Dict[str, Any]] = []
    for catalog_source in RSS_SOURCES:
        source = dict(catalog_source)
        sync = latest_syncs.get(source['id'], {})
        source['last_sync_at'] = sync.get('created_at', '')
        source['items_found'] = sync.get('items_found', 0)
        source['items_new'] = sync.get('items_new', 0)
        source['items_updated'] = sync.get('items_updated', 0)
        source['status'] = sync.get('status', 'pending')
        source['error_message'] = sync.get('error_message', '')
        sources.append(source)

    conn.close()
    return {
        'sources': sources,
        'total_sources': len(sources),
        'enabled_sources': sum(1 for source in sources if source.get('enabled')),
        'active_sources': sum(1 for source in sources if source.get('status') == 'success'),
    }


def query_sources(source_kind: Optional[str] = None, include_empty: bool = True) -> Dict:
    conn = get_db()

    cards: Dict[str, Dict[str, Any]] = {}
    if include_empty:
        for source in SOURCE_CATALOG:
            if source_kind and source.get('kind') != source_kind:
                continue
            cards[source['id']] = _empty_source_card(source)

    rows = conn.execute('SELECT * FROM content ORDER BY timestamp DESC').fetchall()
    total_items = 0

    for row in rows:
        item = _decode_content_row(row)
        if source_kind and item.get('source_kind') != source_kind:
            continue

        total_items += 1
        source_id = item.get('source_id') or 'unknown'
        if source_id not in cards:
            cards[source_id] = _empty_source_card(item['source_info'])
        _update_source_card(cards[source_id], item)

    sources = list(cards.values())
    sources.sort(
        key=lambda source: (
            1 if source.get('count', 0) > 0 else 0,
            source.get('count', 0),
            source.get('latest_timestamp', 0),
            source.get('name', ''),
        ),
        reverse=True,
    )

    kind_summary: Dict[str, Dict[str, Any]] = {}
    for source in sources:
        kind = source.get('kind', 'unknown')
        if kind not in kind_summary:
            kind_summary[kind] = {
                'label': SOURCE_KIND_LABELS.get(kind, kind),
                'sources': 0,
                'active_sources': 0,
                'items': 0,
            }
        kind_summary[kind]['sources'] += 1
        if source.get('count', 0) > 0:
            kind_summary[kind]['active_sources'] += 1
            kind_summary[kind]['items'] += source.get('count', 0)

    result = {
        'sources': sources,
        'total_sources': len(sources),
        'active_sources': sum(1 for source in sources if source.get('count', 0) > 0),
        'total_items': total_items,
        'source_kinds': kind_summary,
        'catalog': source_catalog_summary(),
        'recent_syncs': _recent_syncs(conn),
    }

    conn.close()
    return result


def query_stats() -> Dict:
    data = query_content(limit=10000)
    items = data['items']
    source_data = query_sources(include_empty=True)

    stats = {
        'total_items': data['total'],
        'sources': {},
        'source_types': {},
        'source_kinds': {},
        'categories': {},
        'dates': {},
        'source_cards': source_data['sources'],
        'active_sources': source_data['active_sources'],
        'configured_sources': source_data['catalog']['total_configured'],
        'recent_syncs': source_data['recent_syncs'],
    }

    for item in items:
        source = item.get('source_display_name') or item.get('source', 'unknown')
        stats['sources'][source] = stats['sources'].get(source, 0) + 1

        st = item.get('source_type', 'unknown')
        stats['source_types'][st] = stats['source_types'].get(st, 0) + 1

        sk = item.get('source_kind', 'unknown')
        stats['source_kinds'][sk] = stats['source_kinds'].get(sk, 0) + 1

        cat = item.get('category', 'unknown')
        stats['categories'][cat] = stats['categories'].get(cat, 0) + 1

        date = (item.get('date', '') or '')[:10]
        if date:
            stats['dates'][date] = stats['dates'].get(date, 0) + 1

    return stats


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
