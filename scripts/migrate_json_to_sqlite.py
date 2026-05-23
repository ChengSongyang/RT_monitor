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
