"""Tavily Search 数据源采集器（替代Google News RSS）"""
import sys
import re
import json
import urllib.request
from datetime import datetime
from typing import List, Dict
from . import make_content_id, deduplicate

TAVILY_API_KEY = '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'
TAVILY_API_URL = 'https://api.tavily.com/search'

SEARCH_QUERIES = [
    '放射治疗 最新进展 2026',
    'radiotherapy AI artificial intelligence news',
    '放疗 技术创新 新设备',
    'radiation oncology clinical trial results',
    '放射治疗 指南 共识 更新',
    'radiotherapy deep learning treatment planning',
]


def clean_html(text: str) -> str:
    """清理HTML标签"""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#39;', "'", text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_date(date_str: str) -> str:
    """解析日期为 YYYY-MM-DD 格式"""
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
    for fmt in [
        '%a, %d %b %Y %H:%M:%S %Z',
        '%a, %d %b %Y %H:%M:%S %z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except Exception:
            continue
    if len(date_str) >= 10:
        return date_str[:10]
    return datetime.now().strftime('%Y-%m-%d')


def extract_source(url: str) -> str:
    """从URL提取来源名称"""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ''
        host = re.sub(r'^www\.', '', host)
        domain_map = {
            'nature.com': 'Nature',
            'pubmed.ncbi.nlm.nih.gov': 'PubMed',
            'arxiv.org': 'arXiv',
            'biospace.com': 'BioSpace',
            'medscape.com': 'Medscape',
            'medicalnewstoday.com': 'Medical News Today',
            'cancer.gov': 'NCI',
            'astro.org': 'ASTRO',
            'estro.org': 'ESTRO',
        }
        for domain, name in domain_map.items():
            if domain in host:
                return name
        parts = host.split('.')
        if len(parts) >= 2:
            return parts[-2].capitalize()
        return host
    except Exception:
        return 'Tavily'


def tavily_search(query: str, max_results: int = 10) -> List[Dict]:
    """调用Tavily Search API"""
    payload = json.dumps({
        'query': query,
        'max_results': max_results,
        'topic': 'news',
        'search_depth': 'basic',
        'include_answer': False,
    }).encode('utf-8')

    req = urllib.request.Request(
        TAVILY_API_URL,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {TAVILY_API_KEY}',
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get('results', [])
    except Exception as e:
        print(f'  [WARN] Tavily search failed for "{query}": {e}', file=sys.stderr)
        return []


def collect(days_back: int = 7) -> List[Dict]:
    """采集放射治疗相关新闻"""
    news_items = []
    seen_urls = set()

    for query in SEARCH_QUERIES:
        print(f'  📡 Tavily: {query}...', file=sys.stderr)
        results = tavily_search(query, max_results=8)

        for r in results:
            url = r.get('url', '')
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = clean_html(r.get('title', ''))
            if not title:
                continue

            content = clean_html(r.get('content', ''))
            published = r.get('published_date', '') or ''
            date = parse_date(published)
            source = extract_source(url)

            text_lower = (title + ' ' + content).lower()
            has_rt = any(kw in text_lower for kw in [
                '放射治疗', '放疗', 'radiotherapy', 'radiation therapy',
                'radiation oncology', '放射肿瘤',
            ])
            has_ai = any(kw in text_lower for kw in [
                'ai', '人工智能', 'deep learning', 'machine learning',
                'artificial intelligence', '大模型', 'llm', 'transformer',
            ])

            hot_score = 50
            if has_rt:
                hot_score += 10
            if has_ai:
                hot_score += 10

            tags = []
            if has_rt:
                tags.append('放射治疗')
            if has_ai:
                tags.append('AI')

            news_items.append({
                'id': make_content_id('tavily', str(hash(url))),
                'title': title,
                'content': content,
                'summary': content[:200] + ('...' if len(content) > 200 else ''),
                'url': url,
                'source': source,
                'source_type': 'news',
                'source_user': source,
                'source_verified': False,
                'source_verified_reason': '',
                'date': date,
                'timestamp': datetime.now().timestamp(),
                'category': 'industry_news',
                'tags': tags,
                'images': [],
                'meta': {},
                'ai': {'score': hot_score, 'is_featured': False, 'recommendation_reason': ''},
                'extra': {},
            })

    return deduplicate(news_items)
