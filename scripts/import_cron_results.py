#!/usr/bin/env python3
"""
适配 Hermes cron 论文监控结果 → RT_monitor 数据库

读取 monitor_radiotherapy_ai.py 的 JSON 输出（论文列表），
转换为 content 表格式并 upsert 到 rt_monitor.db。

用法:
  # 从文件导入
  python3 scripts/import_cron_results.py --file /path/to/papers.json

  # 从 stdin 导入（管道）
  python3 ~/.hermes/scripts/paper-monitor/monitor_radiotherapy_ai.py | python3 scripts/import_cron_results.py --stdin

  # 直接运行监控脚本并导入
  python3 scripts/import_cron_results.py --run-monitor
"""
import sys
import os
import json
import argparse
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from db import init_db, upsert_content, log_sync, save_report


def convert_paper_to_content(paper: dict) -> dict:
    """将 monitor_radiotherapy_ai.py 输出的论文格式转换为 content 表格式"""
    source = paper.get('source', 'Unknown')
    raw_id = paper.get('id', '')
    # 构造 content 表的 id: {source}_{raw_id}
    content_id = f"{source.lower().replace(' ', '_')}_{raw_id}".replace('.', '_')

    title = paper.get('title', '').strip()
    abstract = paper.get('abstract', '').strip()
    authors = paper.get('authors', '')
    date_str = paper.get('date', '')

    # 解析日期为 timestamp
    timestamp = 0.0
    if date_str:
        try:
            # 处理多种日期格式
            if len(date_str) == 10 and '-' in date_str:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            elif len(date_str) == 7 and '-' in date_str:
                dt = datetime.strptime(date_str + '-01', '%Y-%m-%d')
            elif len(date_str) == 4 and date_str.isdigit():
                dt = datetime.strptime(date_str + '-01-01', '%Y-%m-%d')
            else:
                # 尝试 PubMed 格式 "2024 May 20" 或其他
                for fmt in ('%Y %b %d', '%Y %B %d', '%b %d, %Y', '%B %d, %Y',
                            '%Y/%m/%d', '%d %b %Y', '%d %B %Y'):
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    dt = datetime.now()
            timestamp = dt.timestamp()
        except Exception:
            timestamp = datetime.now().timestamp()

    # 确定 category
    source_lower = source.lower()
    if any(kw in source_lower for kw in ['arxiv', 'pubmed', 'semantic', 'biorxiv', 'medrxiv',
                                           'ijrobp', 'radiotherapy and oncology', 'cvpr',
                                           'iccv', 'eccv', 'miccai']):
        category = 'paper'
        source_type = 'paper'
    else:
        category = 'paper'
        source_type = 'paper'

    # 构造 tags
    tags = ['论文', source]
    categories = paper.get('categories', '')
    if categories:
        for cat in categories.split(',')[:3]:
            cat = cat.strip()
            if cat:
                tags.append(cat)

    # 构造 meta
    meta = {
        'authors': authors,
        'journal': paper.get('journal', source),
        'pdf_url': paper.get('pdf_url', ''),
        'html_url': paper.get('html_url', ''),
        'doi': paper.get('doi', ''),
    }

    return {
        'id': content_id,
        'title': title,
        'summary': abstract[:200] + ('...' if len(abstract) > 200 else ''),
        'content': abstract,
        'url': paper.get('url', ''),
        'source': source,
        'source_type': source_type,
        'source_user': authors,
        'source_verified': True,
        'source_verified_reason': '学术论文',
        'date': date_str,
        'timestamp': timestamp,
        'category': category,
        'tags': tags,
        'images': [],
        'meta': meta,
        'ai': {'score': 70, 'is_featured': False, 'recommendation_reason': ''},
        'extra': {},
    }


def import_papers(papers: list) -> dict:
    """导入论文列表到数据库"""
    init_db()
    items = [convert_paper_to_content(p) for p in papers]
    stats = upsert_content(items)
    log_sync('cron_monitor', stats['found'], stats['new'], stats['updated'])
    return stats


def main():
    parser = argparse.ArgumentParser(description='导入 Hermes cron 论文监控结果到 RT_monitor 数据库')
    parser.add_argument('--file', '-f', help='JSON 文件路径')
    parser.add_argument('--stdin', action='store_true', help='从 stdin 读取 JSON')
    parser.add_argument('--run-monitor', action='store_true', help='直接运行监控脚本并导入')
    parser.add_argument('--monitor-script', default=os.path.expanduser('~/.hermes/scripts/paper-monitor/monitor_radiotherapy_ai.py'),
                        help='监控脚本路径')
    args = parser.parse_args()

    papers = []

    if args.run_monitor:
        print(f"📡 运行监控脚本: {args.monitor_script}", file=sys.stderr)
        result = subprocess.run(
            ['python3', args.monitor_script],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode != 0:
            print(f"❌ 监控脚本失败: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        papers = json.loads(result.stdout)
    elif args.stdin:
        data = sys.stdin.read()
        papers = json.loads(data)
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
    else:
        parser.print_help()
        sys.exit(1)

    print(f"📥 读取到 {len(papers)} 篇论文", file=sys.stderr)
    stats = import_papers(papers)
    print(f"✅ 导入完成: {stats['new']} 新增, {stats['updated']} 更新, {stats['found']} 总计", file=sys.stderr)
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    main()
