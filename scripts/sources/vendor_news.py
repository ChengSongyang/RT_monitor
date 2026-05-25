"""
新闻采集器 - 仅限指定放疗厂商
允许的厂商：Elekta, Varian, RaySearch Laboratories, 中核安科瑞, 新华医疗, Manteia
"""
import sys
import re
import json
import urllib.request
from datetime import datetime, timedelta
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
            'Elekta radiation therapy latest',
        ],
        'domain_keywords': ['elekta.com', 'elekta'],
        'search_domains': ['elekta.com'],
    },
    {
        'name_en': 'Varian',
        'name_zh': '瓦里安',
        'search_queries': [
            'Varian radiotherapy news',
            'Varian radiation therapy latest',
        ],
        'domain_keywords': ['varian.com', 'varian'],
        'search_domains': ['varian.com', 'siemens-healthineers.com'],
    },
    {
        'name_en': 'RaySearch',
        'name_zh': 'RaySearch',
        'search_queries': [
            'RaySearch Laboratories news',
            'RaySearch RayStation treatment planning',
        ],
        'domain_keywords': ['raysearch.com', 'raysearch'],
        'search_domains': ['raysearch.com'],
    },
    {
        'name_en': '中核安科瑞',
        'name_zh': '中核安科瑞',
        'search_queries': [
            '中核安科瑞 放疗',
            '中核安科瑞 放射治疗',
            'ankehigh radiotherapy',
        ],
        'domain_keywords': ['ankehigh', '中核安科瑞'],
        'search_domains': ['ankehigh.com'],
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
        'search_domains': ['shinva.com'],
    },
    {
        'name_en': 'Manteia',
        'name_zh': 'Manteia',
        'search_queries': [
            'Manteia radiotherapy AI',
            'Manteia treatment planning',
        ],
        'domain_keywords': ['manteia', 'manteiatech'],
        'search_domains': ['manteiatech.com'],
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


def _generate_recommendation(vendor: str, title: str, content: str) -> dict:
    """基于新闻元数据生成上榜理由和评分"""
    text = f"{title} {content}".lower()
    score = 70
    reasons = []

    # 放疗技术关键词
    tech_keywords = {
        'artificial intelligence': 'AI/人工智能', 'machine learning': '机器学习',
        'deep learning': '深度学习', 'adaptive': '自适应放疗',
        'mr-linac': 'MR-Linac', 'mr guided': 'MR引导放疗',
        'treatment planning': '治疗计划', 'dose prediction': '剂量预测',
        'auto-segmentation': '自动分割', 'auto-contouring': '自动勾画',
        'vmat': 'VMAT', 'imrt': 'IMRT', 'sbrt': 'SBRT',
        'proton': '质子治疗', 'flash': 'FLASH放疗',
        'quality assurance': '质量保证', 'commissioning': '设备验收',
        'image-guided': '图像引导', 'igrt': 'IGRT',
        'brachytherapy': '近距离放疗', 'robotic': '机器人放疗',
    }
    matched_tech = []
    for kw, label in tech_keywords.items():
        if kw in text and label not in matched_tech:
            matched_tech.append(label)
    if matched_tech:
        score += min(len(matched_tech) * 3, 15)
        reasons.append(f'涉及{"/".join(matched_tech[:3])}等放疗技术')

    # 肿瘤类型
    cancer_keywords = {
        'lung cancer': '肺癌', 'breast cancer': '乳腺癌',
        'prostate': '前列腺癌', 'head and neck': '头颈部肿瘤',
        'nasopharyngeal': '鼻咽癌', 'cervical': '宫颈癌',
        'liver': '肝癌', 'brain': '脑肿瘤', 'pancreatic': '胰腺癌',
        'endometrial': '子宫内膜癌', 'esophageal': '食管癌',
    }
    matched_cancer = []
    for kw, label in cancer_keywords.items():
        if kw in text and label not in matched_cancer:
            matched_cancer.append(label)
    if matched_cancer:
        reasons.append(f'针对{"、".join(matched_cancer[:2])}等癌种')

    # 学术会议加分
    conferences = ['estro', 'astro', 'rsna', 'aacr', 'asco', 'aacr', 'iccr', 'aapm']
    for conf in conferences:
        if conf in text:
            score += 10
            reasons.append(f'来自{conf.upper()}学术会议')
            break

    # 临床试验/研究
    if any(kw in text for kw in ['clinical trial', 'fda clearance', 'ce mark', '510(k)', 'regulatory']):
        score += 8
        reasons.append('涉及监管审批/临床试验')
    if any(kw in text for kw in ['study', 'research', 'publication', 'peer-reviewed']):
        score += 5
        reasons.append('有学术研究支撑')

    score = min(score, 98)

    if reasons:
        reason = f'{vendor}（现属西门子医疗）' if vendor == 'Varian' else vendor
        reason += '：' + '；'.join(reasons) + '。'
    else:
        reason = f'{vendor}的放疗行业动态。'

    return {'score': score, 'is_featured': score >= 80, 'recommendation_reason': reason}


def tavily_search(query: str, max_results: int = 10, include_domains: list = None) -> List[Dict]:
    body = {
        'query': query,
        'max_results': max_results,
        'topic': 'news',
        'search_depth': 'advanced',
        'include_answer': False,
    }
    if include_domains:
        body['include_domains'] = include_domains

    payload = json.dumps(body).encode('utf-8')

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
    cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

    for vendor in ALLOWED_VENDORS:
        print(f'  📡 搜索 {vendor["name_zh"]}({vendor["name_en"]})...', file=sys.stderr)
        search_domains = vendor.get('search_domains', [])

        for query in vendor['search_queries']:
            # 第一轮：限定官网域名搜索（精准）
            if search_domains:
                results = tavily_search(query, max_results=10, include_domains=search_domains)
                for r in results:
                    url = r.get('url', '')
                    if url in seen_urls:
                        continue
                    title = clean_html(r.get('title', ''))
                    if not title:
                        continue
                    content = clean_html(r.get('content', ''))
                    seen_urls.add(url)
                    published = r.get('published_date', '') or ''
                    date = parse_date(published)
                    if not date or date < cutoff:
                        continue
                    news_items.append({
                        'id': make_content_id('vendor_news', str(hash(url))),
                        'title': title,
                        'content': content,
                        'summary': content[:200] + ('...' if len(content) > 200 else ''),
                        'url': url,
                        'source': vendor['name_en'],
                        'source_type': 'news',
                        'source_user': vendor['name_en'],
                        'source_verified': True,
                        'source_verified_reason': f'放疗厂商 {vendor["name_en"]}',
                        'date': date,
                        'timestamp': datetime.strptime(date, '%Y-%m-%d').timestamp() if date else 0.0,
                        'category': 'industry_news',
                        'tags': [vendor['name_en'], '放疗厂商'],
                        'images': [],
                        'meta': {'vendor': vendor['name_en']},
                        'ai': _generate_recommendation(vendor['name_en'], title, content),
                        'extra': {},
                    })

            # 第二轮：开放搜索 + identify_vendor 过滤（广搜）
            results = tavily_search(query, max_results=10)
            for r in results:
                url = r.get('url', '')
                if url in seen_urls:
                    continue
                title = clean_html(r.get('title', ''))
                if not title:
                    continue
                content = clean_html(r.get('content', ''))
                identified_vendor = identify_vendor(url, title, content)
                if not identified_vendor:
                    continue
                seen_urls.add(url)
                published = r.get('published_date', '') or ''
                date = parse_date(published)
                if not date or date < cutoff:
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
                    'ai': _generate_recommendation(identified_vendor, title, content),
                    'extra': {},
                })

    unique_news = deduplicate(news_items)
    print(f'  ✅ 共找到 {len(unique_news)} 条厂商新闻', file=sys.stderr)
    return unique_news
