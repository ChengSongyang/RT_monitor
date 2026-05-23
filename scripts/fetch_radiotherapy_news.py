#!/usr/bin/env python3
"""
放射治疗领域新闻监控 - RSS源版本
使用RSS订阅源获取放射治疗相关资讯
"""
import sys
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timedelta
from typing import List, Dict
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
}


def fetch_url(url: str, timeout: int = 30) -> bytes:
    """Fetch URL with error handling"""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return b""


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


def search_google_news_rss(days_back: int = 7) -> List[Dict]:
    """
    从Google News RSS获取放射治疗相关新闻
    """
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
        print(f"  📡 Google News: {query}...", file=sys.stderr)
        
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
                url = link_elem.text if link_elem is not None else ''
                
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
                
                hot_score = 70 if has_ai else 50
                
                tags = ['放射治疗']
                if has_ai:
                    tags.append('AI')
                
                news_items.append({
                    'id': f'google_news_{hash(title)}',
                    'title': title,
                    'content': content,
                    'summary': content[:200] + ('...' if len(content) > 200 else ''),
                    'source': source,
                    'source_user': source,
                    'source_verified': False,
                    'source_verified_reason': '',
                    'date': pub_date.strftime('%Y-%m-%d'),
                    'timestamp': pub_date.timestamp(),
                    'url': url,
                    'image_urls': [],
                    'hot_score': hot_score,
                    'content_type': 'industry_news',
                    'tags': tags,
                    'category': 'industry_news',
                })
                
        except Exception as e:
            print(f"  [WARN] Parse error for Google News: {e}", file=sys.stderr)
        
        time.sleep(2)
    
    return news_items


def search_pubmed_news(days_back: int = 7, max_results: int = 20) -> List[Dict]:
    """
    从PubMed获取放射治疗相关的新闻和评论文章
    """
    news_items = []
    
    queries = [
        '"radiotherapy"[Title/Abstract] AND ("news"[Publication Type] OR "comment"[Publication Type])',
        '"radiation therapy"[Title/Abstract] AND ("news"[Publication Type] OR "editorial"[Publication Type])',
    ]
    
    seen_ids = set()
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    date_to = datetime.now().strftime('%Y/%m/%d')
    
    for query in queries:
        print(f"  📡 PubMed新闻...", file=sys.stderr)
        
        search_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
            f"db=pubmed&term={urllib.parse.quote(query)}"
            f"&mindate={date_from}&maxdate={date_to}&datetype=edat"
            f"&retmax={max_results}&retmode=json&sort=relevance"
        )
        
        data = fetch_url(search_url)
        if not data:
            continue
        
        try:
            result = json.loads(data)
            ids = result.get('esearchresult', {}).get('idlist', [])
            
            if not ids:
                continue
            
            ids_str = ','.join(ids)
            fetch_url_str = (
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
                f"db=pubmed&id={ids_str}&retmode=json"
            )
            
            summary_data = fetch_url(fetch_url_str)
            if not summary_data:
                continue
            
            summary_result = json.loads(summary_data)
            result_list = summary_result.get('result', {})
            
            for uid in ids:
                if uid in seen_ids or uid not in result_list:
                    continue
                seen_ids.add(uid)
                
                item = result_list[uid]
                title = item.get('title', '')
                pub_date = item.get('pubdate', '')
                authors_list = item.get('authors', [])
                authors = ', '.join(a.get('name', '') for a in authors_list[:5])
                journal = item.get('fulljournalname', '') or item.get('source', '')
                
                has_ai = any(kw in title.lower() 
                           for kw in ['ai', 'artificial intelligence', 'deep learning', 'machine learning', 'llm'])
                
                hot_score = 70 if has_ai else 50
                
                tags = ['放射治疗', '学术新闻']
                if has_ai:
                    tags.append('AI')
                
                news_items.append({
                    'id': f'pubmed_news_{uid}',
                    'title': title,
                    'content': '',
                    'summary': '',
                    'source': 'PubMed',
                    'source_user': authors,
                    'source_verified': True,
                    'source_verified_reason': '学术数据库',
                    'date': pub_date,
                    'timestamp': datetime.now().timestamp(),
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    'image_urls': [],
                    'hot_score': hot_score,
                    'content_type': 'research',
                    'tags': tags,
                    'category': 'industry_news',
                })
                
        except Exception as e:
            print(f"  [WARN] Parse error for PubMed: {e}", file=sys.stderr)
        
        time.sleep(2)
    
    return news_items


def deduplicate_news(news_items: List[Dict]) -> List[Dict]:
    """去除重复新闻"""
    seen_titles = set()
    unique_items = []
    
    for item in news_items:
        title_key = item['title'][:50].lower().strip()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_items.append(item)
    
    return unique_items


def main():
    days_back = 1
    
    print(f"🔍 搜索放射治疗领域新闻 (过去{days_back}天)...", file=sys.stderr)
    print(f"📡 数据源: Google News, PubMed", file=sys.stderr)
    
    all_news = []
    
    print("  📡 Google News...", file=sys.stderr)
    all_news.extend(search_google_news_rss(days_back=days_back))
    
    print("  📡 PubMed新闻...", file=sys.stderr)
    all_news.extend(search_pubmed_news(days_back=days_back))
    
    unique_news = deduplicate_news(all_news)
    unique_news.sort(key=lambda x: x.get('hot_score', 0), reverse=True)
    
    print(f"  ✅ 共找到 {len(unique_news)} 条不重复新闻", file=sys.stderr)
    
    print(json.dumps(unique_news, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
