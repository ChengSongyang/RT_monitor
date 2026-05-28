#!/usr/bin/env python3
"""Repair existing database rows after crawler/enrichment changes."""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(__file__))

from db import _report_path_for, get_db, init_db, upsert_content
from llm_enrichment import enrich_item
from sources import guidelines


def _json_load(value: Any, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except Exception:
        return fallback


def _row_to_item(row) -> Dict[str, Any]:
    return {
        'id': row['id'],
        'title': row['title'],
        'summary': row['summary'] or '',
        'content': row['content'] or '',
        'url': row['url'] or '',
        'source': row['source'] or '',
        'source_type': row['source_type'] or 'news',
        'source_user': row['source_user'] or '',
        'source_verified': bool(row['source_verified']),
        'source_verified_reason': row['source_verified_reason'] or '',
        'date': row['date'] or '',
        'timestamp': row['timestamp'] or 0,
        'category': row['category'] or 'industry_news',
        'tags': _json_load(row['tags'], []),
        'images': _json_load(row['images'], []),
        'meta': _json_load(row['meta'], {}),
        'ai': _json_load(row['ai'], {}),
        'extra': _json_load(row['extra'], {}),
    }


def _is_route_report_path(path: str) -> bool:
    parts = (path or '').split('/')
    return len(parts) >= 5 and parts[0] == 'reports'


def repair_report_paths() -> int:
    conn = get_db()
    rows = conn.execute('''
        SELECT c.*
        FROM content c
        JOIN reports r ON r.content_id = c.id
        WHERE c.source_type = 'paper'
    ''').fetchall()

    updated = 0
    for row in rows:
        item = _row_to_item(row)
        meta = dict(item.get('meta') or {})
        if _is_route_report_path(meta.get('report_path', '')):
            continue
        meta['report_path'] = _report_path_for(item)
        meta['report_type'] = meta.get('report_type') or 'ai_analysis'
        conn.execute(
            'UPDATE content SET meta=?, updated_at=datetime("now") WHERE id=?',
            (json.dumps(meta, ensure_ascii=False), item['id']),
        )
        updated += 1

    conn.commit()
    conn.close()
    return updated


def rows_needing_enrichment(limit: int) -> List[Dict[str, Any]]:
    conn = get_db()
    rows = conn.execute(
        '''
        SELECT c.*, CASE WHEN r.content_id IS NULL THEN 0 ELSE 1 END AS has_report
        FROM content c
        LEFT JOIN reports r ON r.content_id = c.id
        WHERE
          coalesce(json_extract(c.ai, '$.title_cn'), '') = ''
          OR coalesce(json_extract(c.ai, '$.summary_cn'), '') = ''
          OR coalesce(json_extract(c.ai, '$.recommendation_reason'), '') = ''
          OR (c.source_type = 'paper' AND r.content_id IS NULL)
        ORDER BY c.timestamp DESC
        LIMIT ?
        ''',
        (limit,),
    ).fetchall()
    result = []
    for row in rows:
        item = _row_to_item(row)
        item['_has_report'] = bool(row['has_report'])
        result.append(item)
    conn.close()
    return result


def backfill(limit: int, skip_ai: bool = False) -> Dict[str, int]:
    init_db()
    guideline_stats = upsert_content(guidelines.collect())
    repaired_paths = repair_report_paths()

    enriched = 0
    if not skip_ai:
        for item in rows_needing_enrichment(limit):
            include_report = item.get('source_type') == 'paper' and not item.pop('_has_report', False)
            print(f"🧠 回填中文化/解读: {item['id']} {item['title'][:60]}", file=sys.stderr)
            upsert_content([enrich_item(item, include_report=include_report, force=True)])
            enriched += 1

    return {
        'guidelines_new': guideline_stats['new'],
        'guidelines_updated': guideline_stats['updated'],
        'report_paths_repaired': repaired_paths,
        'ai_enriched': enriched,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=30)
    parser.add_argument('--skip-ai', action='store_true')
    args = parser.parse_args()
    print(json.dumps(backfill(args.limit, args.skip_ai), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
