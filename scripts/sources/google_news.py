"""Tavily Search 数据源采集器（替代Google News RSS）— 中文优先，严格过滤"""
import sys
import re
import json
import urllib.request
from datetime import datetime
from typing import List, Dict
from . import make_content_id, deduplicate

TAVILY_API_KEY = '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'
TAVILY_API_URL = 'https://api.tavily.com/search'

# 以中文查询为主，确保返回中文结果
SEARCH_QUERIES = [
    '放射治疗 最新技术 进展 2026',
    '放疗 人工智能 AI 应用',
    '放射肿瘤学 临床试验 最新',
    '头颈部放疗 鼻咽癌 肺癌 乳腺癌',
    '放射治疗 新设备 新技术',
    'radiation oncology AI deep learning latest',
    'radiotherapy clinical trial results 2026',
]

# 严格的相关性关键词
RT_KEYWORDS_STRICT = [
    '放射治疗', '放疗', '放射肿瘤', '放射科', '放射医学',
    'radiotherapy', 'radiation therapy', 'radiation oncology',
    '放疗计划', '放疗设备', '放疗技术', '调强放疗', '立体定向',
    'IMRT', 'VMAT', 'SBRT', 'SRS', '质子治疗', '重离子',
    'FLASH放疗', 'FLASH radiotherapy',
    '头颈部肿瘤', '鼻咽癌', '肺癌放疗', '乳腺癌放疗', '宫颈癌放疗',
    '前列腺癌放疗', '食管癌放疗', '脑肿瘤放疗',
    '直线加速器', '伽马刀', '射波刀', 'TOMO',
    '危及器官', '靶区勾画', '剂量学', '治疗计划',
    'IGRT', 'CBCT', '自适应放疗',
]

# 排除关键词 — 与放疗无关的
EXCLUDE_KEYWORDS = [
    'rpet', 'plastic', 'recycl', 'beauty device', 'cosmetic',
    'alzheimer', 'visual acuity', 'diabetes type 1',
    'graduation', 'greeting card', 'weather forecast',
    'stock market', 'cryptocurrency', 'bitcoin',
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
            'thelancet.com': 'Lancet',
            'nejm.org': 'NEJM',
            'jco.org': 'JCO',
            'rpor.pl': 'Reports of Practical Oncology',
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


def is_relevant(title: str, content: str) -> bool:
    """检查是否与放射治疗/肿瘤相关"""
    text_lower = (title + ' ' + content).lower()

    # 排除无关内容
    if any(kw in text_lower for kw in EXCLUDE_KEYWORDS):
        return False

    # 非英语/中文内容排除
    cyrillic = sum(1 for c in title + content if '\u0400' <= c <= '\u04ff')
    if cyrillic > 5:
        return False

    # 放疗/肿瘤相关关键词（放宽，加入肿瘤/癌症通用词）
    rt_broad = RT_KEYWORDS_STRICT + [
        'cancer', 'oncology', 'tumor', 'tumour', 'neoplasm',
        'chemotherapy', 'immunotherapy', 'targeted therapy',
        'ASCO', 'ESTRO', 'ASTRO', 'clinical trial',
        'FDA clearance', 'FDA approval', 'phase 1', 'phase 2', 'phase 3',
        'survival', 'metastasis', 'recurrence',
        '放射', '放疗', '肿瘤', '癌症', '化疗', '免疫治疗',
    ]
    return any(kw.lower() in text_lower for kw in rt_broad)


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


def collect(days_back: int = 7) -> List[Dict]:
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

            # 严格过滤：必须与放疗相关
            if not is_relevant(title, content):
                print(f'  ⏭️ 跳过不相关内容: {title[:50]}...', file=sys.stderr)
                continue

            text_lower = (title + ' ' + content).lower()
            has_rt = any(kw.lower() in text_lower for kw in RT_KEYWORDS_STRICT[:10])

            hot_score = 50
            if has_rt:
                hot_score += 15

            tags = ['放射治疗']
            if any(kw.lower() in text_lower for kw in ['ai', '人工智能', 'deep learning', 'machine learning']):
                tags.append('AI')
            if any(kw in text_lower for kw in ['临床试验', 'clinical trial']):
                tags.append('临床试验')
            if any(kw in text_lower for kw in ['新设备', '新技', '设备', '技术']):
                tags.append('技术创新')

            # 判断分类
            if any(kw in text_lower for kw in ['论文', '研究', 'study', 'analysis', 'trial', 'randomized']):
                category = 'paper'
            else:
                category = 'industry_news'

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
                'category': category,
                'tags': tags,
                'images': [],
                'meta': {},
                'ai': {'score': hot_score, 'is_featured': False, 'recommendation_reason': ''},
                'extra': {},
            })

    return deduplicate(news_items)
