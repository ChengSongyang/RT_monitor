"""arXiv 数据源采集器"""
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
