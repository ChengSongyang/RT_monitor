#!/usr/bin/env python3
"""
统一数据采集入口 - 联影放疗事业部信息监控平台
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import init_db, upsert_content, log_sync
from llm_enrichment import enrich_items
from sources import google_news, guidelines, papers, rss_feeds, vendor_news


SOURCES = [
    ('rss_feeds', rss_feeds),           # RSS/Atom论文、新闻与监管信源
    ('papers', papers),                 # 放疗+AI论文
    ('guidelines', guidelines),         # 常见癌种/协会指南入口
    ('vendor_news', vendor_news),       # 指定厂商官网/相关新闻
    ('radiotherapy_news', google_news), # 行业新闻与学会/监管动态
]


def collect_rss_sources(days_back: int = 14):
    total_stats = {'found': 0, 'new': 0, 'updated': 0, 'failed': 0, 'errors': []}

    for result in rss_feeds.collect_by_source(days_back=days_back):
        source = result.get('source') or {}
        source_id = str(source.get('id') or 'rss_feeds')
        error = result.get('error') or ''

        if error:
            total_stats['failed'] += 1
            total_stats['errors'].append(f'{source_id}: {error}')
            log_sync(source_id, 0, 0, 0, 'error', str(error))
            print(f"  ❌ {source_id} failed: {error}", file=sys.stderr)
            continue

        items = enrich_items(result.get('items') or [], source_name=source_id)
        stats = upsert_content(items)
        log_sync(source_id, stats['found'], stats['new'], stats['updated'])
        total_stats['found'] += stats['found']
        total_stats['new'] += stats['new']
        total_stats['updated'] += stats['updated']
        print(f"  ✅ {source_id}: {stats['new']} new, {stats['updated']} updated", file=sys.stderr)

    return total_stats


def collect_all(days_back: int = 14):
    init_db()
    total_stats = {'found': 0, 'new': 0, 'updated': 0}

    for name, source in SOURCES:
        print(f"\n📡 采集 {name}...", file=sys.stderr)
        try:
            if name == 'rss_feeds':
                stats = collect_rss_sources(days_back=days_back)
                aggregate_status = 'error' if stats.get('failed') else 'success'
                aggregate_error = '; '.join(stats.get('errors', []))
                log_sync(name, stats['found'], stats['new'], stats['updated'], aggregate_status, aggregate_error)
                total_stats['found'] += stats['found']
                total_stats['new'] += stats['new']
                total_stats['updated'] += stats['updated']
                if stats.get('failed'):
                    print(f"  ⚠️ {name}: {stats['failed']} failed, {stats['new']} new, {stats['updated']} updated", file=sys.stderr)
                else:
                    print(f"  ✅ {name}: {stats['new']} new, {stats['updated']} updated", file=sys.stderr)
                continue

            items = source.collect(days_back=days_back)
            items = enrich_items(items, source_name=name)
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
    parser.add_argument('--days', type=int, default=14)
    args = parser.parse_args()
    collect_all(days_back=args.days)
