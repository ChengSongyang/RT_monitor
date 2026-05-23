#!/usr/bin/env python3
"""
Radiotherapy + AI/LLM Paper Monitor
Monitor papers from multiple sources including journals and conferences
Output: JSON format for agent processing
"""
import sys
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; HermesAgent/1.0)'}


def fetch_url(url: str, timeout: int = 30) -> bytes:
    """Fetch URL with error handling"""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return b""


def search_arxiv(days_back: int = 7, max_results: int = 50) -> List[Dict]:
    """Search arXiv for radiotherapy + AI papers"""
    papers = []
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    
    queries = [
        # Radiotherapy + AI
        'all:radiotherapy+AND+all:large+language+model',
        'all:radiotherapy+AND+all:LLM',
        'all:radiotherapy+AND+all:AI+agent',
        'all:radiotherapy+AND+all:deep+learning',
        'all:radiation+therapy+AND+all:transformer',
        'all:radiation+oncology+AND+all:artificial+intelligence',
        'all:radiotherapy+AND+all:foundation+model',
        'all:radiotherapy+AND+all:GPT',
        # Medical image + radiotherapy
        'all:radiotherapy+AND+all:segmentation+AND+cat:cs.CV',
        'all:radiation+therapy+AND+all:image+registration',
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
                    'source': 'arXiv',
                    'id': base_id,
                    'title': title,
                    'authors': authors,
                    'date': published,
                    'abstract': summary,
                    'url': f"https://arxiv.org/abs/{base_id}",
                    'pdf_url': f"https://arxiv.org/pdf/{base_id}",
                    'categories': cats,
                    'html_url': f"https://arxiv.org/html/{base_id}",
                    'journal': 'arXiv'
                })
        except Exception as e:
            print(f"  [WARN] Parse error for arXiv: {e}", file=sys.stderr)
        
        time.sleep(4)
    
    return papers


def search_pubmed(days_back: int = 7, max_results: int = 50) -> List[Dict]:
    """Search PubMed for radiotherapy + AI papers (includes IJROBP, Radiotherapy and Oncology)"""
    papers = []
    
    queries = [
        # General radiotherapy + AI
        '"radiotherapy"[Title/Abstract] AND ("large language model"[Title/Abstract] OR "LLM"[Title/Abstract])',
        '"radiation therapy"[Title/Abstract] AND ("artificial intelligence"[Title/Abstract] OR "AI agent"[Title/Abstract])',
        '"radiation oncology"[Title/Abstract] AND ("deep learning"[Title/Abstract] OR "transformer"[Title/Abstract])',
        '"radiotherapy"[Title/Abstract] AND ("foundation model"[Title/Abstract] OR "GPT"[Title/Abstract])',
        # IJROBP specific
        '"Int J Radiat Oncol Biol Phys"[Journal] AND ("artificial intelligence"[Title/Abstract] OR "deep learning"[Title/Abstract] OR "machine learning"[Title/Abstract])',
        # Radiotherapy and Oncology specific
        '"Radiother Oncol"[Journal] AND ("artificial intelligence"[Title/Abstract] OR "deep learning"[Title/Abstract] OR "machine learning"[Title/Abstract] OR "LLM"[Title/Abstract])',
    ]
    
    seen_ids = set()
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    date_to = datetime.now().strftime('%Y/%m/%d')
    
    for query in queries:
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
                
                # Get abstract
                abstract_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={uid}&retmode=xml"
                abs_data = fetch_url(abstract_url)
                abstract = ""
                if abs_data:
                    try:
                        abs_root = ET.fromstring(abs_data)
                        abs_elem = abs_root.find('.//AbstractText')
                        if abs_elem is not None:
                            abstract = abs_elem.text or ""
                    except:
                        pass
                
                # Get DOI
                doi = ""
                for aid in item.get('articleids', []):
                    if aid.get('idtype') == 'doi':
                        doi = aid.get('value', '')
                        break
                
                # Determine source label
                source_label = 'PubMed'
                if 'Int J Radiat Oncol' in journal or 'IJROBP' in journal:
                    source_label = 'IJROBP'
                elif 'Radiother Oncol' in journal:
                    source_label = 'Radiotherapy and Oncology'
                
                papers.append({
                    'source': source_label,
                    'id': uid,
                    'title': title,
                    'authors': authors,
                    'date': pub_date,
                    'abstract': abstract,
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    'pdf_url': f"https://doi.org/{doi}" if doi else '',
                    'categories': 'Medicine',
                    'html_url': '',
                    'journal': journal
                })
        except Exception as e:
            print(f"  [WARN] Parse error for PubMed: {e}", file=sys.stderr)
        
        time.sleep(2)
    
    return papers


def search_semantic_scholar(days_back: int = 7, max_results: int = 50) -> List[Dict]:
    """Search Semantic Scholar for radiotherapy + AI papers"""
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
                    # Map known venues
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
                    'source': source_label,
                    'id': paper_id[:20],
                    'title': item.get('title', ''),
                    'authors': authors,
                    'date': pub_date or str(item.get('year', '')),
                    'abstract': item.get('abstract') or '',
                    'url': source_url,
                    'pdf_url': pdf_url,
                    'categories': f"Citations: {item.get('citationCount', 0)}",
                    'html_url': '',
                    'journal': venue
                })
        except Exception as e:
            print(f"  [WARN] Parse error for Semantic Scholar: {e}", file=sys.stderr)
        
        time.sleep(2)
    
    return papers


def search_cv_conferences(days_back: int = 7, max_results: int = 50) -> List[Dict]:
    """Search CV conferences (CVPR, ICCV, ECCV, MICCAI) for radiotherapy/medical imaging + AI"""
    papers = []
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    
    # arXiv queries targeting CV + medical/radiotherapy
    queries = [
        'cat:cs.CV+AND+all:radiotherapy',
        'cat:cs.CV+AND+all:radiation+therapy',
        'cat:cs.CV+AND+all:medical+image+segmentation+AND+all:cancer',
        'cat:cs.CV+AND+all:tumor+segmentation+AND+all:deep+learning',
        'cat:cs.CV+AND+all:CT+segmentation+AND+all:radiotherapy',
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
                    'source': 'arXiv-CV',
                    'id': base_id,
                    'title': title,
                    'authors': authors,
                    'date': published,
                    'abstract': summary,
                    'url': f"https://arxiv.org/abs/{base_id}",
                    'pdf_url': f"https://arxiv.org/pdf/{base_id}",
                    'categories': cats,
                    'html_url': f"https://arxiv.org/html/{base_id}",
                    'journal': 'arXiv (cs.CV)'
                })
        except Exception as e:
            print(f"  [WARN] Parse error for CV conferences: {e}", file=sys.stderr)
        
        time.sleep(4)
    
    return papers


def search_biorxiv(days_back: int = 7, max_results: int = 30) -> List[Dict]:
    """Search bioRxiv/medRxiv for radiotherapy + AI papers"""
    papers = []
    
    servers = ['biorxiv', 'medrxiv']
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    seen_ids = set()
    
    for server in servers:
        url = f"https://api.biorxiv.org/details/{server}/{date_from}/{date_to}/0/100"
        data = fetch_url(url)
        if not data:
            continue
        
        try:
            result = json.loads(data)
            for item in result.get('collection', []):
                title = item.get('title', '').lower()
                abstract = item.get('abstract', '').lower()
                
                rt_keywords = ['radiotherapy', 'radiation therapy', 'radiation oncology']
                ai_keywords = ['llm', 'large language model', 'ai agent', 'deep learning', 
                              'transformer', 'artificial intelligence', 'foundation model', 'gpt']
                
                has_rt = any(kw in title or kw in abstract for kw in rt_keywords)
                has_ai = any(kw in title or kw in abstract for kw in ai_keywords)
                
                if not (has_rt and has_ai):
                    continue
                
                doi = item.get('doi', '')
                if doi in seen_ids:
                    continue
                seen_ids.add(doi)
                
                papers.append({
                    'source': server.capitalize(),
                    'id': doi.split('/')[-1] if doi else '',
                    'title': item.get('title', ''),
                    'authors': item.get('authors', ''),
                    'date': item.get('date', ''),
                    'abstract': item.get('abstract', ''),
                    'url': f"https://doi.org/{doi}" if doi else '',
                    'pdf_url': item.get('pdf_url', ''),
                    'categories': 'Preprint',
                    'html_url': '',
                    'journal': server.capitalize()
                })
        except Exception as e:
            print(f"  [WARN] Parse error for {server}: {e}", file=sys.stderr)
        
        time.sleep(1)
    
    return papers


def deduplicate(papers: List[Dict]) -> List[Dict]:
    """Remove duplicate papers by title similarity"""
    seen_titles = set()
    unique_papers = []
    for p in papers:
        title_key = p['title'].lower().strip()[:100]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_papers.append(p)
    return unique_papers


def main():
    days_back = 1
    
    print(f"🔍 搜索放射治疗+AI/大模型相关论文 (过去{days_back}天)...", file=sys.stderr)
    print(f"📡 数据源: arXiv, PubMed, Semantic Scholar, bioRxiv/medRxiv, CV顶会", file=sys.stderr)
    print(f"📚 重点关注: IJROBP, Radiotherapy and Oncology, CVPR/ICCV/ECCV/MICCAI", file=sys.stderr)
    
    all_papers = []
    
    print("  📡 arXiv...", file=sys.stderr)
    all_papers.extend(search_arxiv(days_back=days_back))
    
    print("  📡 PubMed (含IJROBP, Radiotherapy and Oncology)...", file=sys.stderr)
    all_papers.extend(search_pubmed(days_back=days_back))
    
    print("  📡 Semantic Scholar...", file=sys.stderr)
    all_papers.extend(search_semantic_scholar(days_back=days_back))
    
    print("  📡 CV顶会相关...", file=sys.stderr)
    all_papers.extend(search_cv_conferences(days_back=days_back))
    
    print("  📡 bioRxiv/medRxiv...", file=sys.stderr)
    all_papers.extend(search_biorxiv(days_back=days_back))
    
    unique_papers = deduplicate(all_papers)
    
    print(f"  ✅ 共找到 {len(unique_papers)} 篇不重复论文", file=sys.stderr)
    
    # Output as JSON
    print(json.dumps(unique_papers, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
