"""RSS/Atom feed parser and collector for configured RSS sources."""
from __future__ import annotations

import hashlib
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

from . import deduplicate, fetch_url, make_content_id

try:
    from ..rss_source_catalog import enabled_rss_sources
except ImportError:
    from rss_source_catalog import enabled_rss_sources


AI_TERMS = (
    'artificial intelligence', ' ai ', 'deep learning', 'machine learning',
    'neural network', 'radiomics', 'auto-contouring', 'autocontouring',
    'segmentation', 'large language model', ' llm', 'transformer',
    'foundation model', 'gpt', 'automation', 'knowledge-based planning',
    'dose prediction', 'adaptive planning',
)

RADIOTHERAPY_TERMS = (
    'radiotherapy', 'radiation therapy', 'radiation oncology',
    'radiation treatment', 'sbrt', 'stereotactic body', 'imrt', 'vmat',
    'brachytherapy', 'proton therapy', 'treatment planning',
    'auto-contouring', 'autocontouring', 'contouring', 'organ at risk',
    'target volume', 'dose distribution', 'dose prediction',
)

REGULATORY_TERMS = (
    'fda', 'medwatch', 'recall', 'safety alert', 'warning letter',
    'adverse event', 'medical device', '510(k)', 'clearance',
    'clinical trial', 'device correction', 'device removal',
)

DOI_RE = re.compile(r'\b(?:doi:\s*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[^\s<>"]+)', re.IGNORECASE)
ARXIV_RE = re.compile(r'(?:arxiv:\s*|arxiv\.org/(?:abs|pdf)/)(\d{4}\.\d{4,5})(?:v\d+)?', re.IGNORECASE)
TAG_RE = re.compile(r'<[^>]+>')
WHITESPACE_RE = re.compile(r'\s+')


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ''
    text = TAG_RE.sub(' ', value)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return WHITESPACE_RE.sub(' ', text).strip()


def _child_text(element: ET.Element, names: List[str]) -> str:
    for child in list(element):
        local_name = child.tag.rsplit('}', 1)[-1].lower()
        if local_name in names:
            return _clean_text(''.join(child.itertext()))
    return ''


def _children(element: ET.Element, name: str) -> List[ET.Element]:
    return [child for child in list(element) if child.tag.rsplit('}', 1)[-1].lower() == name]


def _first_link(element: ET.Element) -> str:
    links = _children(element, 'link')
    for rel in ('alternate', ''):
        for link in links:
            link_rel = (link.get('rel') or '').lower()
            href = link.get('href') or _clean_text(link.text)
            if href and (rel == '' or link_rel == rel):
                return href.strip()
    return ''


def _authors(element: ET.Element) -> str:
    names: List[str] = []
    for author in _children(element, 'author'):
        name = _child_text(author, ['name']) or _clean_text(''.join(author.itertext()))
        if name:
            names.append(name)
    if names:
        return ', '.join(names[:8])

    creator_names = []
    for child in list(element):
        local_name = child.tag.rsplit('}', 1)[-1].lower()
        if local_name in ('creator', 'author'):
            value = _clean_text(''.join(child.itertext()))
            if value:
                creator_names.append(value)
    return ', '.join(creator_names[:8])


def _extract_doi(*values: str) -> str:
    for value in values:
        match = DOI_RE.search(value or '')
        if match:
            return match.group(1).rstrip(').,;').lower()
    return ''


def _extract_arxiv_id(*values: str) -> str:
    for value in values:
        match = ARXIV_RE.search(value or '')
        if match:
            return match.group(1)
    return ''


def _entry_date(element: ET.Element) -> str:
    return (
        _child_text(element, ['published'])
        or _child_text(element, ['updated'])
        or _child_text(element, ['pubdate'])
        or _child_text(element, ['date'])
        or _child_text(element, ['dc:date'])
    )


def parse_feed(data: bytes) -> List[Dict[str, str]]:
    """Parse Atom 1.0 or RSS 2.0 data into normalized string fields."""
    if not data:
        return []

    root = ET.fromstring(data)
    root_name = root.tag.rsplit('}', 1)[-1].lower()
    if root_name == 'feed':
        raw_entries = _children(root, 'entry')
    elif root_name == 'rss':
        channel = next(iter(_children(root, 'channel')), root)
        raw_entries = _children(channel, 'item')
    else:
        raw_entries = _children(root, 'entry') or _children(root, 'item')

    entries: List[Dict[str, str]] = []
    for raw in raw_entries:
        title = _child_text(raw, ['title'])
        link = _first_link(raw) or _child_text(raw, ['link']) or _child_text(raw, ['id'])
        summary = _child_text(raw, ['summary']) or _child_text(raw, ['description'])
        content = _child_text(raw, ['content', 'encoded']) or summary
        entry_id = _child_text(raw, ['id', 'guid']) or link
        published = _entry_date(raw)
        authors = _authors(raw)
        doi_text = _child_text(raw, ['doi'])
        combined = ' '.join([doi_text, entry_id, title, link, summary, content])
        entries.append({
            'id': entry_id,
            'title': title,
            'link': link,
            'summary': summary,
            'content': content,
            'published': published,
            'authors': authors,
            'doi': _extract_doi(combined),
            'arxiv_id': _extract_arxiv_id(combined),
        })
    return entries


def _parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip()
    try:
        parsed = parsedate_to_datetime(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        pass

    normalized = text.replace('Z', '+00:00')
    for candidate in (normalized, normalized[:10]):
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def _source_id(source: Dict[str, object]) -> str:
    return str(source.get('id') or source.get('name') or 'rss')


def _source_name(source: Dict[str, object]) -> str:
    return str(source.get('short_name') or source.get('name') or _source_id(source))


def _content_source(source: Dict[str, object]) -> str:
    return str(source.get('source') or _source_name(source))


def _source_type(source: Dict[str, object]) -> str:
    return str(source.get('source_type') or 'news')


def _source_category(source: Dict[str, object]) -> str:
    configured = str(source.get('category') or '')
    if configured:
        return configured
    return 'paper' if _source_type(source) == 'paper' else 'industry_news'


def _source_limit(source: Dict[str, object]) -> int:
    try:
        return max(0, int(source.get('max_items_per_run') or 0))
    except (TypeError, ValueError):
        return 0


def _verified_reason(source: Dict[str, object]) -> str:
    configured = str(source.get('verified_reason') or '')
    if configured:
        return configured
    if _source_type(source) == 'paper':
        return 'RSS 论文信源'
    if _source_category(source) == 'regulatory':
        return 'RSS 监管/安全信源'
    return 'RSS 新闻信源'


def _is_arxiv_source(source: Dict[str, object]) -> bool:
    source_id = _source_id(source).lower()
    name = _source_name(source).lower()
    feed_url = str(source.get('feed_url') or source.get('url') or '').lower()
    return 'arxiv' in source_id or 'arxiv' in name or 'arxiv.org' in feed_url


def _is_relevant_arxiv(entry: Dict[str, str]) -> bool:
    text = f" {entry.get('title', '')} {entry.get('summary', '')} {entry.get('content', '')} ".lower()
    has_radiotherapy = any(term in text for term in RADIOTHERAPY_TERMS)
    has_ai = any(term in text for term in AI_TERMS)
    return has_radiotherapy and has_ai


def score_entry(source: Dict[str, object], entry: Dict[str, str]) -> int:
    """Score a feed entry for recommendation ranking."""
    score = int(source.get('base_score') or 70)
    text = f" {entry.get('title', '')} {entry.get('summary', '')} {entry.get('content', '')} ".lower()

    if any(term in text for term in RADIOTHERAPY_TERMS):
        score += 8
    if any(term in text for term in AI_TERMS):
        score += 8
    if any(term in text for term in REGULATORY_TERMS):
        score += 6
    if entry.get('doi'):
        score += 3
    if entry.get('arxiv_id'):
        score += 3
    if str(source.get('trust_level') or '').lower() in ('high', 'official'):
        score += 2

    return max(0, min(score, 100))


def _score_reason(source: Dict[str, object], entry: Dict[str, str], score: int) -> str:
    reasons = []
    if _is_arxiv_source(source):
        reasons.append('arXiv 放疗 AI 相关预印本')
    elif _source_category(source) == 'regulatory':
        reasons.append(f"{_source_name(source)} 监管/安全警报")
    elif _source_type(source) == 'paper':
        reasons.append(f"{_source_name(source)} 最新论文条目")
    else:
        reasons.append(f"{_source_name(source)} 最新新闻/研究动态")
    if entry.get('doi'):
        reasons.append('含 DOI')
    if entry.get('arxiv_id'):
        reasons.append('含 arXiv ID')
    return '；'.join(reasons) + f"；AIHOT 评分 {score}"


def _entry_unique_id(source: Dict[str, object], entry: Dict[str, str]) -> str:
    arxiv_id = entry.get('arxiv_id', '')
    doi = entry.get('doi', '')
    if _is_arxiv_source(source) and arxiv_id:
        return make_content_id('arxiv', arxiv_id)
    if doi:
        raw = doi
    elif entry.get('id'):
        raw = entry['id']
    elif entry.get('link'):
        raw = entry['link']
    else:
        raw = hashlib.sha1(entry.get('title', '').encode('utf-8')).hexdigest()[:16]
    safe_source = _source_id(source).replace('-rss', '')
    safe_raw = re.sub(r'[^a-zA-Z0-9_.-]+', '_', raw).strip('_') or 'entry'
    return make_content_id(safe_source, safe_raw)


def _content_item(source: Dict[str, object], entry: Dict[str, str]) -> Dict[str, object]:
    published_dt = _parse_date(entry.get('published', ''))
    date = published_dt.date().isoformat() if published_dt else entry.get('published', '')[:10]
    timestamp = published_dt.timestamp() if published_dt else datetime.now(timezone.utc).timestamp()
    score = score_entry(source, entry)
    source_name = _source_name(source)
    display_source = _content_source(source)
    source_type = _source_type(source)
    category = _source_category(source)
    journal = str(source.get('name') or display_source) if source_type == 'paper' else ''
    summary = entry.get('summary') or entry.get('content') or ''
    content = entry.get('content') or summary
    arxiv_id = entry.get('arxiv_id', '')
    doi = entry.get('doi', '')
    link = entry.get('link') or entry.get('id') or ''
    if _is_arxiv_source(source) and arxiv_id:
        link = f'https://arxiv.org/abs/{arxiv_id}'

    base_tag = '论文' if source_type == 'paper' else '新闻'
    tags = [base_tag, 'RSS', source_name, category]
    configured_tags = source.get('tags') or []
    if isinstance(configured_tags, list):
        tags.extend(str(tag) for tag in configured_tags if tag)
    if _is_arxiv_source(source):
        tags.append('arXiv')
    if doi:
        tags.append('DOI')
    deduped_tags = []
    for tag in tags:
        if tag and tag not in deduped_tags:
            deduped_tags.append(tag)

    pdf_url = ''
    html_url = ''
    if _is_arxiv_source(source) and arxiv_id:
        html_url = f'https://arxiv.org/abs/{arxiv_id}'
        pdf_url = f'https://arxiv.org/pdf/{arxiv_id}'
    elif doi:
        html_url = f'https://doi.org/{doi}'

    return {
        'id': _entry_unique_id(source, entry),
        'title': entry.get('title') or 'Untitled RSS entry',
        'summary': summary[:240] + ('...' if len(summary) > 240 else ''),
        'content': content,
        'url': link or html_url,
        'source': display_source,
        'source_type': source_type,
        'source_user': entry.get('authors', ''),
        'source_verified': True,
        'source_verified_reason': _verified_reason(source),
        'date': date,
        'timestamp': timestamp,
        'category': category,
        'tags': deduped_tags[:12],
        'images': [],
        'meta': {
            'authors': entry.get('authors', ''),
            'journal': journal,
            'pdf_url': pdf_url,
            'html_url': html_url,
            'doi': doi,
            'arxiv_id': arxiv_id,
            'source_id': _source_id(source),
            'source_kind': source.get('kind', 'journal'),
            'source_kind_label': source.get('kind_label', ''),
            'feed_url': source.get('feed_url') or source.get('url') or '',
            'rss_feed_url': source.get('feed_url') or source.get('url') or '',
        },
        'ai': {
            'score': score,
            'is_featured': score >= 85,
            'recommendation_reason': _score_reason(source, entry, score),
        },
        'extra': {},
    }


def collect_source(source: Dict[str, object], days_back: int = 14) -> List[Dict[str, object]]:
    """Collect one RSS/Atom source and return upsert_content-shaped items."""
    feed_url = str(source.get('feed_url') or source.get('url') or '')
    if not feed_url:
        return []

    data = fetch_url(feed_url, max_retries=4 if _is_arxiv_source(source) else 3)
    if not data:
        raise ValueError('Feed request returned empty response')

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    items: List[Dict[str, object]] = []
    max_items = _source_limit(source)
    for entry in parse_feed(data):
        published_dt = _parse_date(entry.get('published', ''))
        if published_dt and published_dt < cutoff:
            continue
        if _is_arxiv_source(source) and not _is_relevant_arxiv(entry):
            continue
        items.append(_content_item(source, entry))
        if max_items and len(items) >= max_items:
            break
    return deduplicate(items)


def collect_by_source(days_back: int = 14) -> List[Dict[str, object]]:
    """Collect all enabled RSS sources and preserve per-source errors."""
    results: List[Dict[str, object]] = []
    for source in enabled_rss_sources():
        try:
            items = collect_source(source, days_back=days_back)
            error = ''
        except Exception as exc:  # Keep one bad feed from breaking all feeds.
            print(f"  [WARN] RSS feed failed for {_source_id(source)}: {exc}", file=sys.stderr)
            items = []
            error = str(exc)
        results.append({'source': source, 'items': items, 'error': error})
    return results


def collect(days_back: int = 14) -> List[Dict[str, object]]:
    """Collect and flatten all enabled RSS feed items."""
    items: List[Dict[str, object]] = []
    for result in collect_by_source(days_back=days_back):
        if not result.get('error'):
            items.extend(result.get('items', []))
    return deduplicate(items)
