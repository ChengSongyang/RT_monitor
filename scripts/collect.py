#!/usr/bin/env python3
"""
统一数据采集入口 - 联影放疗事业部信息监控平台
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import init_db, upsert_content, log_sync
from sources import papers, vendor_news


SOURCES = [
    ('papers', papers),           # 放疗+AI论文
    ('vendor_news', vendor_news), # 指定厂商新闻
]


def collect_all(days_back: int = 14):
    init_db()
    total_stats = {'found': 0, 'new': 0, 'updated': 0}

    for name, source in SOURCES:
        print(f"\n📡 采集 {name}...", file=sys.stderr)
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
    parser.add_argument('--days', type=int, default=14)
    args = parser.parse_args()
    collect_all(days_back=args.days)
