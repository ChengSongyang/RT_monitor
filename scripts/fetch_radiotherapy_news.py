#!/usr/bin/env python3
"""
放射治疗领域新闻监控 - Tavily搜索版本
使用Tavily Search API获取放射治疗相关资讯
"""
import sys
import json
import urllib.request
import re
from datetime import datetime
from typing import List, Dict

TAVILY_API_KEY = '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'
TAVILY_API_URL = 'https://api.tavily.com/search'

# 搜索查询列表
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
    # 尝试常见格式
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
    # 尝试提取前10个字符作为日期
    if len(date_str) >= 10:
        return date_str[:10]
    return datetime.now().strftime('%Y-%m-%d')


def extract_source(url: str) -> str:
    """从URL提取来源名称"""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ''
        # 去掉 www. 前缀
        host = re.sub(r'^www\.', '', host)
        # 常见域名映射
        domain_map = {
            'nature.com': 'Nature',
            'pubmed.ncbi.nlm.nih.gov': 'PubMed',
            'arxiv.org': 'arXiv',
            'news.google.com': 'Google News',
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
        # 返回域名主体
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


def fetch_all_news() -> List[Dict]:
    """获取所有放射治疗相关新闻"""
    all_items = []
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

            # 判断相关性
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

            all_items.append({
                'id': f'tavily_{hash(url)}',
                'title': title,
                'content': content,
                'summary': content[:200] + ('...' if len(content) > 200 else ''),
                'source': source,
                'source_user': source,
                'source_verified': False,
                'source_verified_reason': '',
                'date': date,
                'timestamp': datetime.now().timestamp(),
                'url': url,
                'image_urls': [],
                'hot_score': hot_score,
                'content_type': 'industry_news',
                'tags': tags,
                'category': 'industry_news',
            })

    return all_items


def deduplicate(items: List[Dict]) -> List[Dict]:
    """去重"""
    seen = set()
    unique = []
    for item in items:
        key = item['title'][:50].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def main():
    print('🔍 Tavily搜索放射治疗领域新闻...', file=sys.stderr)

    all_news = fetch_all_news()
    unique_news = deduplicate(all_news)
    unique_news.sort(key=lambda x: x.get('hot_score', 0), reverse=True)

    print(f'  ✅ 共找到 {len(unique_news)} 条不重复新闻', file=sys.stderr)
    print(json.dumps(unique_news, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
