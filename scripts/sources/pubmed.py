"""PubMed 数据源采集器"""
import sys
import json
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import time
from . import fetch_url, make_content_id, deduplicate


def collect(days_back: int = 7, max_results: int = 50) -> List[Dict]:
    papers = []

    queries = [
        '"radiotherapy"[Title/Abstract] AND ("large language model"[Title/Abstract] OR "LLM"[Title/Abstract])',
        '"radiation therapy"[Title/Abstract] AND ("artificial intelligence"[Title/Abstract] OR "AI agent"[Title/Abstract])',
        '"radiation oncology"[Title/Abstract] AND ("deep learning"[Title/Abstract] OR "transformer"[Title/Abstract])',
        '"radiotherapy"[Title/Abstract] AND ("foundation model"[Title/Abstract] OR "GPT"[Title/Abstract])',
        '"Int J Radiat Oncol Biol Phys"[Journal] AND ("artificial intelligence"[Title/Abstract] OR "deep learning"[Title/Abstract] OR "machine learning"[Title/Abstract])',
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
                    'id': make_content_id('pubmed', uid),
                    'title': title,
                    'summary': abstract[:200] + ('...' if len(abstract) > 200 else ''),
                    'content': abstract,
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    'source': source_label,
                    'source_type': 'paper',
                    'source_user': authors,
                    'source_verified': True,
                    'source_verified_reason': '学术论文',
                    'date': pub_date,
                    'timestamp': datetime.now().timestamp(),
                    'category': 'paper',
                    'tags': ['论文', 'PubMed', journal],
                    'images': [],
                    'meta': {
                        'authors': authors,
                        'journal': journal,
                        'pdf_url': f"https://doi.org/{doi}" if doi else '',
                        'html_url': '',
                        'doi': doi,
                    },
                    'ai': {'score': 70, 'is_featured': False, 'recommendation_reason': ''},
                    'extra': {},
                })
        except Exception as e:
            print(f"  [WARN] Parse error for PubMed: {e}", file=sys.stderr)

        time.sleep(2)

    return deduplicate(papers)
