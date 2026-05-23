"""Google News 数据源采集器"""
import sys
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import time
from . import fetch_url, make_content_id, deduplicate


def parse_rss_date(date_str: str) -> datetime:
    """解析RSS日期格式"""
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue

    return datetime.now()


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


def collect(days_back: int = 7) -> List[Dict]:
    news_items = []

    queries = [
        '放射治疗',
        '放疗 科技',
        '放射治疗 AI',
        'radiation therapy news',
        'radiotherapy technology',
    ]

    seen_titles = set()

    for query in queries:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"

        data = fetch_url(url)
        if not data:
            continue

        try:
            root = ET.fromstring(data)
            items = root.findall('.//item')

            for item in items:
                title_elem = item.find('title')
                if title_elem is None or not title_elem.text:
                    continue

                title = clean_html(title_elem.text)

                title_lower = title.lower()
                has_rt = any(kw in title_lower for kw in ['放射治疗', '放疗', 'radiation therapy', 'radiotherapy'])

                if not has_rt:
                    continue

                link_elem = item.find('link')
                item_url = link_elem.text if link_elem is not None else ''

                desc_elem = item.find('description')
                content = ''
                if desc_elem is not None and desc_elem.text:
                    content = clean_html(desc_elem.text)

                pub_date_elem = item.find('pubDate')
                pub_date = datetime.now()
                if pub_date_elem is not None and pub_date_elem.text:
                    pub_date = parse_rss_date(pub_date_elem.text)

                if pub_date < datetime.now() - timedelta(days=days_back):
                    continue

                title_key = title[:50].lower()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                source_elem = item.find('source')
                source = source_elem.text if source_elem is not None else 'Google News'

                has_ai = any(kw in title_lower or kw in content.lower()
                           for kw in ['ai', '人工智能', '深度学习', '机器学习', 'artificial intelligence'])

                tags = ['放射治疗']
                if has_ai:
                    tags.append('AI')

                news_items.append({
                    'id': make_content_id('google_news', str(hash(title))),
                    'title': title,
                    'content': content,
                    'summary': content[:200] + ('...' if len(content) > 200 else ''),
                    'url': item_url,
                    'source': source,
                    'source_type': 'news',
                    'source_user': source,
                    'source_verified': False,
                    'source_verified_reason': '',
                    'date': pub_date.strftime('%Y-%m-%d'),
                    'timestamp': pub_date.timestamp(),
                    'category': 'industry_news',
                    'tags': tags,
                    'images': [],
                    'meta': {},
                    'ai': {'score': 70 if has_ai else 50, 'is_featured': False, 'recommendation_reason': ''},
                    'extra': {},
                })

        except Exception as e:
            print(f"  [WARN] Parse error for Google News: {e}", file=sys.stderr)

        time.sleep(2)

    return deduplicate(news_items)
