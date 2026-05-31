"""RSS/Atom subscription source catalog for paper discovery."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

RSS_SOURCES: List[Dict[str, Any]] = [
    {
        'id': 'arxiv-radiotherapy-ai',
        'name': 'arXiv 放疗 + AI',
        'short_name': 'arXiv RT+AI',
        'kind': 'academic',
        'kind_label': '预印本',
        'source': 'arXiv',
        'source_type': 'paper',
        'category': 'paper',
        'feed_url': 'https://export.arxiv.org/api/query?search_query=all:radiotherapy+AND+all:%22artificial+intelligence%22&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending',
        'homepage': 'https://arxiv.org/',
        'enabled': True,
        'trust_level': 'medium',
        'collection_method': 'arXiv Atom 检索源',
        'description': 'arXiv 中 radiotherapy 与 artificial intelligence 相关的最新预印本。',
        'base_score': 70,
        'tags': ['arXiv', '预印本', '放疗', 'AI'],
    },
    {
        'id': 'ijrobp-red-journal',
        'name': 'International Journal of Radiation Oncology•Biology•Physics',
        'short_name': 'Red Journal',
        'kind': 'journal',
        'kind_label': '放疗期刊',
        'source': 'IJROBP',
        'source_type': 'paper',
        'category': 'paper',
        'feed_url': 'https://rss.sciencedirect.com/publication/science/03603016',
        'homepage': 'https://www.sciencedirect.com/journal/international-journal-of-radiation-oncology-biology-physics',
        'enabled': True,
        'trust_level': 'high',
        'collection_method': 'ScienceDirect RSS 订阅',
        'description': '红皮期刊 International Journal of Radiation Oncology•Biology•Physics 最新论文 RSS。',
        'base_score': 85,
        'tags': ['Red Journal', 'IJROBP', '放疗期刊'],
    },
    {
        'id': 'radonc-green-journal',
        'name': 'Radiotherapy and Oncology',
        'short_name': 'Green Journal',
        'kind': 'journal',
        'kind_label': '放疗期刊',
        'source': 'Radiotherapy and Oncology',
        'source_type': 'paper',
        'category': 'paper',
        'feed_url': 'https://rss.sciencedirect.com/publication/science/01678140',
        'homepage': 'https://www.sciencedirect.com/journal/radiotherapy-and-oncology',
        'enabled': True,
        'trust_level': 'high',
        'collection_method': 'ScienceDirect RSS 订阅',
        'description': '绿皮期刊 Radiotherapy and Oncology 最新论文 RSS。',
        'base_score': 85,
        'tags': ['Green Journal', 'Radiotherapy and Oncology', '放疗期刊'],
    },
]


def enabled_rss_sources() -> List[Dict[str, Any]]:
    return [dict(source) for source in RSS_SOURCES if source.get('enabled')]


def get_rss_source(source_id: str) -> Optional[Dict[str, Any]]:
    for source in RSS_SOURCES:
        if source['id'] == source_id:
            return dict(source)
    return None
