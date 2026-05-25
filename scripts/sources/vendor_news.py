"""
新闻采集器 - 仅限指定放疗厂商
允许的厂商：Elekta, Varian, RaySearch Laboratories, 中核安科瑞, 新华医疗, Manteia
"""
import sys
import re
import json
import urllib.request
from datetime import datetime
from typing import List, Dict
from . import make_content_id, deduplicate

TAVILY_API_KEY = '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'
TAVILY_API_URL = 'https://api.tavily.com/search'

# 允许的厂商列表（英文名、中文名、搜索关键词）
ALLOWED_VENDORS = [
    {
        'name_en': 'Elekta',
        'name_zh': '医科达',
        'search_queries': [
            'Elekta radiotherapy news',
            'Elekta radiation therapy',
            '医科达 放疗 新闻',
        ],
        'domain_keywords': ['elekta.com', 'elekta'],
    },
    {
        'name_en': 'Varian',
        'name_zh': '瓦里安',
        'search_queries': [
            'Varian radiotherapy news',
            'Varian radiation therapy',
            '瓦里安 放疗 新闻',
        ],
        'domain_keywords': ['varian.com', 'varian'],
    },
    {
        'name_en': 'RaySearch',
        'name_zh': 'RaySearch',
        'search_queries': [
            'RaySearch Laboratories radiotherapy',
            'RaySearch treatment planning',
            'RaySearch RayStation',
        ],
        'domain_keywords': ['raysearch.com', 'raysearch'],
    },
    {
        'name_en': '中核安科瑞',
        'name_zh': '中核安科瑞',
        'search_queries': [
            '中核安科瑞 放疗',
            '中核安科瑞 放射治疗',
        ],
        'domain_keywords': ['ankehigh', '中核安科瑞'],
    },
    {
        'name_en': '新华医疗',
        'name_zh': '新华医疗',
        'search_queries': [
            '新华医疗 放疗',
            '新华医疗 放射治疗',
            'Shinva radiotherapy',
        ],
        'domain_keywords': ['shinva', '新华医疗'],
    },
    {
        'name_en': 'Manteia',
        'name_zh': 'Manteia',
        'search_queries': [
            'Manteia radiotherapy',
            'Manteia treatment planning',
            'Manteia AI radiotherapy',
        ],
        'domain_keywords': ['manteia', 'manteiatech'],
    },
]


def clean_html(text: str) -> str:
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
    if not date_str:
        return ''  # 不填入当天日期，留空
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
    return ''  # 无法解析则留空


def identify_vendor(url: str, title: str, content: str) -> str:
    """识别新闻来源厂商"""
    url_lower = url.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    combined = url_lower + ' ' + title_lower + ' ' + content_lower

    for vendor in ALLOWED_VENDORS:
        for kw in vendor['domain_keywords']:
            if kw in combined:
                return vendor['name_en']
    return ''


def tavily_search(query: str, max_results: int = 10) -> List[Dict]:
    payload = json.dumps({
        'query': query,
        'max_results': max_results,
        'topic': 'news',
        'search_depth': 'advanced',
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


def collect(days_back: int = 30) -> List[Dict]:
    """采集指定厂商的放疗新闻"""
    news_items = []
    seen_urls = set()

    for vendor in ALLOWED_VENDORS:
        print(f'  📡 搜索 {vendor["name_zh"]}({vendor["name_en"]})...', file=sys.stderr)

        for query in vendor['search_queries']:
            results = tavily_search(query, max_results=10)

            for r in results:
                url = r.get('url', '')
                if url in seen_urls:
                    continue

                title = clean_html(r.get('title', ''))
                if not title:
                    continue

                content = clean_html(r.get('content', ''))

                # 验证是否确实来自该厂商
                identified_vendor = identify_vendor(url, title, content)
                if not identified_vendor:
                    print(f'  ⏭️ 跳过非目标厂商: {title[:50]}...', file=sys.stderr)
                    continue

                seen_urls.add(url)

                published = r.get('published_date', '') or ''
                date = parse_date(published)

                # 如果无法确认发布日期，不收录
                if not date:
                    print(f'  ⏭️ 跳过无日期: {title[:50]}...', file=sys.stderr)
                    continue

                news_items.append({
                    'id': make_content_id('vendor_news', str(hash(url))),
                    'title': title,
                    'content': content,
                    'summary': content[:200] + ('...' if len(content) > 200 else ''),
                    'url': url,
                    'source': identified_vendor,
                    'source_type': 'news',
                    'source_user': identified_vendor,
                    'source_verified': True,
                    'source_verified_reason': f'放疗厂商 {identified_vendor}',
                    'date': date,
                    'timestamp': datetime.strptime(date, '%Y-%m-%d').timestamp() if date else 0.0,
                    'category': 'industry_news',
                    'tags': [identified_vendor, '放疗厂商'],
                    'images': [],
                    'meta': {'vendor': identified_vendor},
                    'ai': {'score': 70, 'is_featured': False, 'recommendation_reason': ''},
                    'extra': {},
                })

    unique_news = deduplicate(news_items)
    print(f'  ✅ 共找到 {len(unique_news)} 条厂商新闻', file=sys.stderr)
    return unique_news
