"""Semantic Scholar 数据源采集器"""
import sys
import json
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict
import time
from . import fetch_url, make_content_id, deduplicate


def collect(days_back: int = 7, max_results: int = 50) -> List[Dict]:
    papers = []

    queries = [
        "radiotherapy large language model",
        "radiation therapy AI agent",
        "radiation oncology deep learning",
        "radiotherapy foundation model GPT",
        "radiotherapy segmentation neural network",
    ]

    seen_ids = set()

    for query in queries:
        url = (
            f"https://api.semanticscholar.org/graph/v1/paper/search?"
            f"query={urllib.parse.quote(query)}"
            f"&limit={max_results}"
            f"&fields=title,authors,year,abstract,url,externalIds,publicationDate,citationCount,openAccessPdf,venue"
            f"&sort=publicationDate:desc"
        )

        data = fetch_url(url)
        if not data:
            continue

        try:
            result = json.loads(data)
            for item in result.get('data', []):
                paper_id = item.get('paperId', '')
                if paper_id in seen_ids:
                    continue
                seen_ids.add(paper_id)

                pub_date = item.get('publicationDate', '')
                if pub_date:
                    try:
                        pub_dt = datetime.strptime(pub_date, '%Y-%m-%d')
                        if pub_dt < datetime.now() - timedelta(days=days_back):
                            continue
                    except:
                        pass

                ext_ids = item.get('externalIds', {})
                arxiv_id = ext_ids.get('ArXiv', '')
                doi = ext_ids.get('DOI', '')

                authors_list = item.get('authors', [])
                authors = ', '.join(a.get('name', '') for a in authors_list[:5])

                source_url = item.get('url', '')
                if arxiv_id:
                    source_url = f"https://arxiv.org/abs/{arxiv_id}"
                elif doi:
                    source_url = f"https://doi.org/{doi}"

                open_access = item.get('openAccessPdf', {})
                pdf_url = open_access.get('url', '') if open_access else ''

                venue = item.get('venue', '')
                source_label = 'SemanticScholar'
                if venue:
                    venue_lower = venue.lower()
                    if 'cvpr' in venue_lower:
                        source_label = 'CVPR'
                    elif 'iccv' in venue_lower:
                        source_label = 'ICCV'
                    elif 'eccv' in venue_lower:
                        source_label = 'ECCV'
                    elif 'miccai' in venue_lower:
                        source_label = 'MICCAI'
                    elif 'ijrobp' in venue_lower or 'int j radiat oncol' in venue_lower:
                        source_label = 'IJROBP'
                    elif 'radiother oncol' in venue_lower:
                        source_label = 'Radiotherapy and Oncology'

                papers.append({
                    'id': make_content_id('semantic_scholar', paper_id[:20]),
                    'title': item.get('title', ''),
                    'summary': (item.get('abstract') or '')[:200] + ('...' if len(item.get('abstract') or '') > 200 else ''),
                    'content': item.get('abstract') or '',
                    'url': source_url,
                    'source': source_label,
                    'source_type': 'paper',
                    'source_user': authors,
                    'source_verified': True,
                    'source_verified_reason': '学术论文',
                    'date': pub_date or str(item.get('year', '')),
                    'timestamp': datetime.now().timestamp(),
                    'category': 'paper',
                    'tags': ['论文', 'SemanticScholar', venue],
                    'images': [],
                    'meta': {
                        'authors': authors,
                        'journal': venue,
                        'pdf_url': pdf_url,
                        'html_url': '',
                        'doi': doi,
                        'citation_count': item.get('citationCount', 0),
                    },
                    'ai': {'score': 70, 'is_featured': False, 'recommendation_reason': ''},
                    'extra': {},
                })
        except Exception as e:
            print(f"  [WARN] Parse error for Semantic Scholar: {e}", file=sys.stderr)

        time.sleep(3)  # Semantic Scholar 免费API限100请求/5分钟

    return deduplicate(papers)
