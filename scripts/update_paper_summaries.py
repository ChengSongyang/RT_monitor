#!/usr/bin/env python3
"""
更新 RT_monitor 数据库中论文的中文总结内容

用法:
  # 从 JSON 文件导入
  python3 scripts/update_paper_summaries.py --file summaries.json

  # 从 stdin 导入
  echo '{"paper_id": "xxx", "summary_cn": "..."}' | python3 scripts/update_paper_summaries.py --stdin

JSON 格式:
  单篇: {"paper_id": "arxiv_2605.15671", "summary_cn": "中文总结内容..."}
  多篇: [{"paper_id": "...", "summary_cn": "..."}, ...]
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(__file__))
from db import get_db


def update_summary(paper_id: str, summary_cn: str) -> bool:
    """更新指定论文的中文总结"""
    conn = get_db()
    existing = conn.execute('SELECT id, ai FROM content WHERE id = ?', (paper_id,)).fetchone()
    if not existing:
        conn.close()
        return False

    # 更新 ai 字段，加入中文总结
    ai = json.loads(existing['ai']) if existing['ai'] else {}
    ai['summary_cn'] = summary_cn

    conn.execute(
        'UPDATE content SET ai = ?, updated_at = datetime("now") WHERE id = ?',
        (json.dumps(ai, ensure_ascii=False), paper_id)
    )
    conn.commit()
    conn.close()
    return True


def find_paper_id(title: str) -> str:
    """根据标题模糊匹配论文 ID"""
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM content WHERE category='paper' AND title LIKE ?",
        (f'%{title[:50]}%',)
    ).fetchone()
    conn.close()
    return row['id'] if row else None


def main():
    parser = argparse.ArgumentParser(description='更新 RT_monitor 论文中文总结')
    parser.add_argument('--file', '-f', help='JSON 文件路径')
    parser.add_argument('--stdin', action='store_true', help='从 stdin 读取 JSON')
    args = parser.parse_args()

    data = None
    if args.stdin:
        data = json.loads(sys.stdin.read())
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        parser.print_help()
        sys.exit(1)

    # 支持单篇或多篇
    items = data if isinstance(data, list) else [data]

    success = 0
    failed = 0
    for item in items:
        paper_id = item.get('paper_id', '')
        summary_cn = item.get('summary_cn', '')

        if not paper_id or not summary_cn:
            print(f"⚠️  跳过: 缺少 paper_id 或 summary_cn", file=sys.stderr)
            failed += 1
            continue

        # 支持用标题模糊匹配
        if item.get('title') and not paper_id:
            paper_id = find_paper_id(item['title'])

        if update_summary(paper_id, summary_cn):
            success += 1
            print(f"✅ 更新: {paper_id}", file=sys.stderr)
        else:
            failed += 1
            print(f"❌ 未找到: {paper_id}", file=sys.stderr)

    print(json.dumps({'success': success, 'failed': failed}, ensure_ascii=False))


if __name__ == '__main__':
    main()
