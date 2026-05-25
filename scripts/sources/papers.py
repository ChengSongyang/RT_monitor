"""
论文采集器 - 必须同时涉及放射治疗 AND 人工智能
"""
import sys
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import time
from . import fetch_url, make_content_id, deduplicate

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; RTMonitor/1.0)'}

# 放疗关键词（必须至少命中一个）
RT_KEYWORDS = [
    'radiotherapy', 'radiation therapy', 'radiation oncology',
    'external beam', 'internal radiation', 'brachytherapy',
    'proton therapy', 'heavy ion therapy', 'carbon ion therapy',
    'treatment planning', 'dose calculation', 'dose prediction',
    'quality assurance', 'quality control',
    'adaptive radiotherapy', 'online adaptive',
    'image-guided radiation therapy', 'igrt',
    'intensity-modulated radiation therapy', 'imrt',
    'volumetric modulated arc therapy', 'vmat',
    'stereotactic body radiation therapy', 'sbrt',
    'stereotactic radiosurgery', 'srs',
    'flash radiotherapy', 'flash rt',
    '放射治疗', '放疗', '放射肿瘤', '放射医学',
    '放射计划', '剂量计算', '质量保证',
    '自适应放疗', '图像引导', '调强放疗',
    '立体定向', '质子治疗', '重离子治疗',
    '近距离放疗', '外照射', '内照射',
    'organs at risk', 'oar', 'target volume',
    'clinical target volume', 'planning target volume',
    'gross tumor volume', 'ctv', 'ptv', 'gtv',
    '放射性肺炎', '放射性食管炎', '口干症',
    'radiation pneumonitis', 'radiation esophagitis',
    'xerostomia', 'radiation necrosis',
]

# AI关键词（必须至少命中一个）
AI_KEYWORDS = [
    'artificial intelligence', 'machine learning', 'deep learning',
    'neural network', 'convolutional neural network', 'cnn', 'rnn', 'lstm',
    'transformer', 'attention mechanism',
    'large language model', 'llm', 'gpt', 'chatgpt', 'bert',
    'foundation model', 'vision language model',
    'reinforcement learning', 'rl', 'deep reinforcement learning',
    'generative adversarial network', 'gan',
    'autoencoder', 'vae', 'diffusion model',
    'segmentation model', 'object detection', 'classification model',
    'regression model', 'random forest', 'xgboost', 'gradient boosting',
    'support vector machine', 'svm', 'k-nearest neighbor',
    'ensemble learning', 'transfer learning', 'few-shot learning',
    'self-supervised learning', 'unsupervised learning', 'semi-supervised',
    'federated learning', 'meta-learning',
    'radiomics', 'radiogenomics',
    'image registration', 'image fusion', 'image segmentation',
    'auto-segmentation', 'auto-contouring',
    'natural language processing', 'nlp',
    'knowledge graph', 'graph neural network', 'gnn',
    'ai', 'ai-based', 'ai-driven', 'machine intelligence',
    '人工智能', '机器学习', '深度学习', '神经网络',
    '大语言模型', '大模型', '基础模型',
    '强化学习', '影像组学', '影像基因组学',
    '自然语言处理', '知识图谱',
    '自动分割', '自动勾画', '智能体',
    'agent', 'multi-agent',
]


def has_rt_keyword(text: str) -> bool:
    """检查是否包含放疗关键词"""
    text_lower = text.lower()
    return any(kw in text_lower for kw in RT_KEYWORDS)


def has_ai_keyword(text: str) -> bool:
    """检查是否包含AI关键词"""
    text_lower = text.lower()
    return any(kw in text_lower for kw in AI_KEYWORDS)


def is_rt_ai_paper(title: str, abstract: str) -> bool:
    """检查是否同时涉及放疗和AI"""
    combined = title + ' ' + abstract
    return has_rt_keyword(combined) and has_ai_keyword(combined)


def _parse_timestamp(date_str: str) -> float:
    """将日期字符串解析为 timestamp"""
    if not date_str:
        return 0.0
    for fmt in ('%Y-%m-%d', '%Y-%m', '%Y', '%Y %b %d', '%Y %B %d',
                '%b %d, %Y', '%B %d, %Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(date_str[:len(fmt)+5], fmt).timestamp()
        except (ValueError, IndexError):
            continue
    # fallback: try extracting year
    try:
        return datetime.strptime(date_str[:4] + '-01-01', '%Y-%m-%d').timestamp()
    except:
        return 0.0


def search_arxiv(days_back: int = 14, max_results: int = 50) -> List[Dict]:
    """搜索arXiv：放疗+AI论文"""
    papers = []
    ns = {'a': 'http://www.w3.org/2005/Atom'}

    queries = [
        'all:radiotherapy+AND+all:deep+learning',
        'all:radiotherapy+AND+all:machine+learning',
        'all:radiotherapy+AND+all:artificial+intelligence',
        'all:radiotherapy+AND+all:large+language+model',
        'all:radiation+therapy+AND+all:deep+learning',
        'all:radiation+therapy+AND+all:transformer',
        'all:radiation+oncology+AND+all:artificial+intelligence',
        'all:radiotherapy+AND+all:segmentation+AND+cat:cs.CV',
        'all:radiation+therapy+AND+all:image+registration',
        'all:radiotherapy+AND+all:foundation+model',
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

                # 严格过滤：必须同时涉及放疗和AI
                if not is_rt_ai_paper(title, summary):
                    continue

                authors = ', '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns)[:5])
                cats = ', '.join(c.get('term') for c in entry.findall('a:category', ns))

                papers.append({
                    'source': 'arXiv',
                    'source_type': 'paper',
                    'category': 'paper',
                    'id': base_id,
                    'title': title,
                    'authors': authors,
                    'date': published,
                    'timestamp': _parse_timestamp(published),
                    'content': summary,
                    'url': f"https://arxiv.org/abs/{base_id}",
                    'pdf_url': f"https://arxiv.org/pdf/{base_id}",
                    'categories': cats,
                    'html_url': f"https://arxiv.org/html/{base_id}",
                    'journal': 'arXiv',
                })
        except Exception as e:
            print(f"  [WARN] Parse error for arXiv: {e}", file=sys.stderr)

        time.sleep(3)

    return papers


def search_pubmed(days_back: int = 14, max_results: int = 50) -> List[Dict]:
    """搜索PubMed：放疗+AI论文"""
    papers = []

    queries = [
        'radiotherapy AND deep learning',
        'radiotherapy AND machine learning',
        'radiotherapy AND artificial intelligence',
        'radiation therapy AND neural network',
        'radiation oncology AND AI',
        'radiotherapy AND large language model',
        'radiotherapy AND segmentation AND deep learning',
        'treatment planning AND machine learning',
    ]

    seen_ids = set()
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    date_to = datetime.now().strftime('%Y/%m/%d')

    for query in queries:
        search_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={urllib.parse.quote(query)}"
            f"&mindate={date_from}&maxdate={date_to}"
            f"&retmax={max_results}&sort=relevance&retmode=json"
        )

        data = fetch_url(search_url)
        if not data:
            continue

        try:
            result = json.loads(data)
            ids = result.get('esearchresult', {}).get('idlist', [])

            for pmid in ids:
                if pmid in seen_ids:
                    continue
                seen_ids.add(pmid)

                # 获取详情
                detail_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
                detail_data = fetch_url(detail_url)
                if not detail_data:
                    continue

                try:
                    root = ET.fromstring(detail_data)
                    article = root.find('.//PubmedArticle')
                    if article is None:
                        continue

                    medline = article.find('.//MedlineCitation')
                    art = medline.find('.//Article')

                    title = art.find('.//ArticleTitle').text or ''
                    abstract_elem = art.find('.//Abstract/AbstractText')
                    abstract = abstract_elem.text if abstract_elem is not None else ''

                    # 严格过滤：必须同时涉及放疗和AI
                    if not is_rt_ai_paper(title, abstract):
                        continue

                    # 作者
                    authors_list = []
                    for author in art.findall('.//AuthorList/Author')[:5]:
                        last = author.find('LastName')
                        first = author.find('ForeName')
                        if last is not None and first is not None:
                            authors_list.append(f"{last.text} {first.text}")
                    authors = ', '.join(authors_list)

                    # 日期
                    pub_date = art.find('.//ArticleDate')
                    if pub_date is not None:
                        y = pub_date.find('Year')
                        m = pub_date.find('Month')
                        d = pub_date.find('Day')
                        date_str = f"{y.text}-{m.text.zfill(2)}-{d.text.zfill(2)}" if y is not None else ''
                    else:
                        date_str = ''

                    # 期刊
                    journal_elem = art.find('.//Journal/Title')
                    journal = journal_elem.text if journal_elem is not None else 'PubMed'

                    papers.append({
                        'source': 'PubMed',
                        'source_type': 'paper',
                        'category': 'paper',
                        'id': pmid,
                        'title': title,
                        'authors': authors,
                        'date': date_str,
                        'timestamp': _parse_timestamp(date_str),
                        'content': abstract,
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'pdf_url': '',
                        'categories': '',
                        'html_url': '',
                        'journal': journal,
                    })

                    time.sleep(0.5)

                except Exception as e:
                    print(f"  [WARN] Parse error for PubMed {pmid}: {e}", file=sys.stderr)

        except Exception as e:
            print(f"  [WARN] Search error for PubMed: {e}", file=sys.stderr)

        time.sleep(3)

    return papers


def search_semantic_scholar(days_back: int = 14) -> List[Dict]:
    """搜索Semantic Scholar：放疗+AI论文"""
    papers = []

    queries = [
        'radiotherapy deep learning',
        'radiotherapy machine learning',
        'radiation therapy artificial intelligence',
        'radiation oncology AI',
        'radiotherapy large language model',
        'treatment planning machine learning',
        'radiotherapy segmentation neural network',
    ]

    seen_ids = set()

    for query in queries:
        url = (
            f"https://api.semanticscholar.org/graph/v1/paper/search"
            f"?query={urllib.parse.quote(query)}"
            f"&limit=50"
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

                title = item.get('title', '')
                abstract = item.get('abstract') or ''

                # 严格过滤：必须同时涉及放疗和AI
                if not is_rt_ai_paper(title, abstract):
                    continue

                # 日期
                pub_date = item.get('publicationDate') or ''
                if pub_date:
                    try:
                        dt = datetime.strptime(pub_date[:10], '%Y-%m-%d')
                        if dt < datetime.now() - timedelta(days=days_back):
                            continue
                    except:
                        pass

                # 作者
                authors_list = [a.get('name', '') for a in (item.get('authors') or [])[:5]]
                authors = ', '.join(authors_list)

                # 来源URL
                ext_ids = item.get('externalIds') or {}
                doi = ext_ids.get('DOI', '')
                source_url = f"https://doi.org/{doi}" if doi else item.get('url', '')

                # PDF
                pdf_url = ''
                oa = item.get('openAccessPdf')
                if oa:
                    pdf_url = oa.get('url', '')

                # 期刊/会议
                venue = item.get('venue', '')
                source_label = 'SemanticScholar'
                if venue:
                    venue_lower = venue.lower()
                    if 'nature' in venue_lower:
                        source_label = 'Nature'
                    elif 'lancet' in venue_lower:
                        source_label = 'Lancet'
                    elif 'radiotherapy' in venue_lower:
                        source_label = 'Radiotherapy and Oncology'
                    elif 'ijrobp' in venue_lower:
                        source_label = 'IJROBP'

                papers.append({
                    'source': source_label,
                    'source_type': 'paper',
                    'category': 'paper',
                    'id': paper_id[:20],
                    'title': title,
                    'authors': authors,
                    'date': pub_date[:10] if pub_date else str(item.get('year', '')),
                    'timestamp': _parse_timestamp(pub_date[:10] if pub_date else str(item.get('year', ''))),
                    'content': abstract,
                    'url': source_url,
                    'pdf_url': pdf_url,
                    'categories': f"Citations: {item.get('citationCount', 0)}",
                    'html_url': '',
                    'journal': venue or source_label,
                })
        except Exception as e:
            print(f"  [WARN] Parse error for Semantic Scholar: {e}", file=sys.stderr)

        time.sleep(3)

    return papers


def collect(days_back: int = 14) -> List[Dict]:
    """采集放疗+AI论文"""
    print(f"  🔍 搜索放射治疗+AI相关论文 (过去{days_back}天)...", file=sys.stderr)

    all_papers = []

    print("  📡 arXiv...", file=sys.stderr)
    all_papers.extend(search_arxiv(days_back=days_back))

    print("  📡 PubMed...", file=sys.stderr)
    all_papers.extend(search_pubmed(days_back=days_back))

    print("  📡 Semantic Scholar...", file=sys.stderr)
    all_papers.extend(search_semantic_scholar(days_back=days_back))

    unique_papers = deduplicate(all_papers)
    print(f"  ✅ 共找到 {len(unique_papers)} 篇放疗+AI论文", file=sys.stderr)

    return unique_papers
