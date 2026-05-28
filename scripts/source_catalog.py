"""
信源目录与信源归一化工具。

AIHOT 的体验不是只展示一段 source 字符串，而是把来源当成可解释对象：
来源类型、采集方式、可信度、主页、是否启用。这里为后端补上同一层语义。
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse


SOURCE_KIND_LABELS: Dict[str, str] = {
    'academic': '论文数据库',
    'journal': '期刊/出版方',
    'vendor_official': '厂商官网',
    'professional_society': '学会/协会',
    'regulatory': '监管/临床',
    'industry_news': '行业媒体',
    'search': '搜索聚合',
    'discovered': '自动识别',
}


SOURCE_CATALOG: List[Dict[str, Any]] = [
    {
        'id': 'pubmed',
        'name': 'PubMed',
        'short_name': 'PubMed',
        'kind': 'academic',
        'source_type': 'paper',
        'homepage': 'https://pubmed.ncbi.nlm.nih.gov/',
        'domain_patterns': ['pubmed.ncbi.nlm.nih.gov', 'ncbi.nlm.nih.gov'],
        'aliases': ['NCBI', 'Medline'],
        'collection_method': 'NCBI/PubMed 检索',
        'trust_level': 'high',
        'description': '生物医学文献数据库，是放疗论文与临床研究的主干信源。',
        'enabled': True,
    },
    {
        'id': 'arxiv',
        'name': 'arXiv',
        'short_name': 'arXiv',
        'kind': 'academic',
        'source_type': 'paper',
        'homepage': 'https://arxiv.org/',
        'domain_patterns': ['arxiv.org'],
        'aliases': ['arXiv.org'],
        'collection_method': 'arXiv API 关键词检索',
        'trust_level': 'medium',
        'description': 'AI、医学影像、自动勾画与治疗计划相关预印本。',
        'enabled': True,
    },
    {
        'id': 'semantic-scholar',
        'name': 'Semantic Scholar',
        'short_name': 'S2',
        'kind': 'academic',
        'source_type': 'paper',
        'homepage': 'https://www.semanticscholar.org/',
        'domain_patterns': ['semanticscholar.org'],
        'aliases': ['SemanticScholar', 'Semantic Scholar API'],
        'collection_method': 'Semantic Scholar API 检索与引用补充',
        'trust_level': 'medium',
        'description': '用于补充论文检索、引用量与开放访问链接。',
        'enabled': True,
    },
    {
        'id': 'nature',
        'name': 'Nature',
        'short_name': 'Nature',
        'kind': 'journal',
        'source_type': 'mixed',
        'homepage': 'https://www.nature.com/',
        'domain_patterns': ['nature.com'],
        'aliases': ['Nature Portfolio'],
        'collection_method': '行业搜索/论文链接识别',
        'trust_level': 'high',
        'description': '高影响力出版方，常出现医学 AI、肿瘤与放疗研究。',
        'enabled': True,
    },
    {
        'id': 'thelancet',
        'name': 'The Lancet',
        'short_name': 'Lancet',
        'kind': 'journal',
        'source_type': 'mixed',
        'homepage': 'https://www.thelancet.com/',
        'domain_patterns': ['thelancet.com'],
        'aliases': ['Lancet'],
        'collection_method': '行业搜索/论文链接识别',
        'trust_level': 'high',
        'description': '肿瘤、临床试验和医学政策相关高影响力出版方。',
        'enabled': True,
    },
    {
        'id': 'ijrobp',
        'name': 'International Journal of Radiation Oncology Biology Physics',
        'short_name': 'Red Journal',
        'kind': 'journal',
        'source_type': 'paper',
        'homepage': 'https://www.redjournal.org/',
        'domain_patterns': ['redjournal.org'],
        'aliases': ['IJROBP', 'Red Journal'],
        'collection_method': '论文检索/期刊域名识别',
        'trust_level': 'high',
        'description': '放射肿瘤学核心期刊。',
        'enabled': True,
    },
    {
        'id': 'radiotherapy-oncology',
        'name': 'Radiotherapy and Oncology',
        'short_name': 'Green Journal',
        'kind': 'journal',
        'source_type': 'paper',
        'homepage': 'https://www.thegreenjournal.com/',
        'domain_patterns': ['thegreenjournal.com'],
        'aliases': ['Green Journal'],
        'collection_method': '论文检索/期刊域名识别',
        'trust_level': 'high',
        'description': 'ESTRO 相关放疗期刊。',
        'enabled': True,
    },
    {
        'id': 'astro',
        'name': 'ASTRO',
        'short_name': 'ASTRO',
        'kind': 'professional_society',
        'source_type': 'news',
        'homepage': 'https://www.astro.org/',
        'domain_patterns': ['astro.org'],
        'aliases': ['American Society for Radiation Oncology'],
        'collection_method': '行业搜索/官网域名识别',
        'trust_level': 'high',
        'description': '美国放射肿瘤学会，指南、会议和行业政策的重要来源。',
        'enabled': True,
    },
    {
        'id': 'estro',
        'name': 'ESTRO',
        'short_name': 'ESTRO',
        'kind': 'professional_society',
        'source_type': 'news',
        'homepage': 'https://www.estro.org/',
        'domain_patterns': ['estro.org'],
        'aliases': ['European Society for Radiotherapy and Oncology'],
        'collection_method': '行业搜索/官网域名识别',
        'trust_level': 'high',
        'description': '欧洲放射治疗与肿瘤学会，会议、指南与教育资源来源。',
        'enabled': True,
    },
    {
        'id': 'nccn',
        'name': 'NCCN',
        'short_name': 'NCCN',
        'kind': 'professional_society',
        'source_type': 'news',
        'homepage': 'https://www.nccn.org/guidelines/category_1',
        'domain_patterns': ['nccn.org'],
        'aliases': ['National Comprehensive Cancer Network'],
        'collection_method': '人工维护指南入口/Tavily 行业搜索',
        'trust_level': 'high',
        'description': 'NCCN 肿瘤临床实践指南入口，覆盖常见癌种综合治疗与放疗建议。',
        'enabled': True,
    },
    {
        'id': 'asco',
        'name': 'ASCO',
        'short_name': 'ASCO',
        'kind': 'professional_society',
        'source_type': 'news',
        'homepage': 'https://www.asco.org/guidelines',
        'domain_patterns': ['asco.org'],
        'aliases': ['American Society of Clinical Oncology'],
        'collection_method': '人工维护指南入口/Tavily 行业搜索',
        'trust_level': 'high',
        'description': 'ASCO 临床指南与肿瘤综合治疗建议来源。',
        'enabled': True,
    },
    {
        'id': 'esmo',
        'name': 'ESMO',
        'short_name': 'ESMO',
        'kind': 'professional_society',
        'source_type': 'news',
        'homepage': 'https://www.esmo.org/guidelines',
        'domain_patterns': ['esmo.org'],
        'aliases': ['European Society for Medical Oncology'],
        'collection_method': '人工维护指南入口/Tavily 行业搜索',
        'trust_level': 'high',
        'description': 'ESMO 临床实践指南，适合与放疗和多学科治疗策略联动参考。',
        'enabled': True,
    },
    {
        'id': 'csco',
        'name': 'CSCO',
        'short_name': 'CSCO',
        'kind': 'professional_society',
        'source_type': 'news',
        'homepage': 'https://www.csco.org.cn/cn/index.aspx',
        'domain_patterns': ['csco.org.cn'],
        'aliases': ['Chinese Society of Clinical Oncology', '中国临床肿瘤学会'],
        'collection_method': '人工维护指南入口',
        'trust_level': 'high',
        'description': '中国临床肿瘤学会指南入口，适合结合国内诊疗路径和可及性参考。',
        'enabled': True,
    },
    {
        'id': 'aapm',
        'name': 'AAPM',
        'short_name': 'AAPM',
        'kind': 'professional_society',
        'source_type': 'news',
        'homepage': 'https://www.aapm.org/',
        'domain_patterns': ['aapm.org'],
        'aliases': ['American Association of Physicists in Medicine'],
        'collection_method': '行业搜索/官网域名识别',
        'trust_level': 'high',
        'description': '医学物理和质控相关的重要专业组织。',
        'enabled': True,
    },
    {
        'id': 'nci',
        'name': 'National Cancer Institute',
        'short_name': 'NCI',
        'kind': 'regulatory',
        'source_type': 'news',
        'homepage': 'https://www.cancer.gov/',
        'domain_patterns': ['cancer.gov'],
        'aliases': ['NCI', 'Cancer.gov'],
        'collection_method': '行业搜索/官网域名识别',
        'trust_level': 'high',
        'description': '美国国家癌症研究所，癌种、临床研究和患者信息来源。',
        'enabled': True,
    },
    {
        'id': 'fda',
        'name': 'FDA',
        'short_name': 'FDA',
        'kind': 'regulatory',
        'source_type': 'news',
        'homepage': 'https://www.fda.gov/',
        'domain_patterns': ['fda.gov'],
        'aliases': ['U.S. Food and Drug Administration'],
        'collection_method': '监管搜索/官网域名识别',
        'trust_level': 'high',
        'description': '医疗器械审批、510(k)、软件和 AI/ML 医疗器械监管动态。',
        'enabled': True,
    },
    {
        'id': 'clinicaltrials',
        'name': 'ClinicalTrials.gov',
        'short_name': 'Trials',
        'kind': 'regulatory',
        'source_type': 'mixed',
        'homepage': 'https://clinicaltrials.gov/',
        'domain_patterns': ['clinicaltrials.gov'],
        'aliases': ['ClinicalTrials'],
        'collection_method': '临床试验注册库识别',
        'trust_level': 'high',
        'description': '临床试验注册与状态追踪来源。',
        'enabled': True,
    },
    {
        'id': 'varian',
        'name': 'Varian',
        'short_name': 'Varian',
        'kind': 'vendor_official',
        'source_type': 'news',
        'homepage': 'https://www.varian.com/',
        'domain_patterns': ['varian.com', 'siemens-healthineers.com'],
        'aliases': ['瓦里安'],
        'collection_method': 'Tavily 官网域名限定搜索',
        'trust_level': 'official',
        'description': '瓦里安/西门子医疗放疗产品、合作和监管动态。',
        'enabled': True,
    },
    {
        'id': 'elekta',
        'name': 'Elekta',
        'short_name': 'Elekta',
        'kind': 'vendor_official',
        'source_type': 'news',
        'homepage': 'https://www.elekta.com/',
        'domain_patterns': ['elekta.com'],
        'aliases': ['医科达'],
        'collection_method': 'Tavily 官网域名限定搜索',
        'trust_level': 'official',
        'description': '医科达放疗设备、软件、临床合作与财报动态。',
        'enabled': True,
    },
    {
        'id': 'raysearch',
        'name': 'RaySearch',
        'short_name': 'RaySearch',
        'kind': 'vendor_official',
        'source_type': 'news',
        'homepage': 'https://www.raysearchlabs.com/',
        'domain_patterns': ['raysearchlabs.com', 'raysearch.com'],
        'aliases': ['RaySearch Laboratories', 'RayStation'],
        'collection_method': 'Tavily 官网域名限定搜索',
        'trust_level': 'official',
        'description': 'RayStation、RayCare 等治疗计划和肿瘤信息系统动态。',
        'enabled': True,
    },
    {
        'id': 'siemens-healthineers',
        'name': 'Siemens Healthineers',
        'short_name': 'Siemens',
        'kind': 'vendor_official',
        'source_type': 'news',
        'homepage': 'https://www.siemens-healthineers.com/',
        'domain_patterns': ['siemens-healthineers.com'],
        'aliases': ['西门子医疗'],
        'collection_method': 'Tavily 官网域名限定搜索',
        'trust_level': 'official',
        'description': '影像、放疗生态与 Varian 相关公司新闻。',
        'enabled': True,
    },
    {
        'id': 'accuray',
        'name': 'Accuray',
        'short_name': 'Accuray',
        'kind': 'vendor_official',
        'source_type': 'news',
        'homepage': 'https://www.accuray.com/',
        'domain_patterns': ['accuray.com'],
        'aliases': ['CyberKnife', 'TomoTherapy'],
        'collection_method': 'Tavily 官网域名限定搜索',
        'trust_level': 'official',
        'description': '射波刀、TomoTherapy、自适应放疗相关厂商动态。',
        'enabled': True,
    },
    {
        'id': 'shinva',
        'name': '新华医疗',
        'short_name': '新华',
        'kind': 'vendor_official',
        'source_type': 'news',
        'homepage': 'https://www.shinva.net/',
        'domain_patterns': ['shinva.net', 'shinva.com'],
        'aliases': ['Shinva'],
        'collection_method': 'Tavily 官网域名限定搜索',
        'trust_level': 'official',
        'description': '国产医疗装备与放疗相关产品动态。',
        'enabled': True,
    },
    {
        'id': 'manteia',
        'name': 'Manteia',
        'short_name': 'Manteia',
        'kind': 'vendor_official',
        'source_type': 'news',
        'homepage': 'https://www.manteiatech.com/',
        'domain_patterns': ['manteiatech.com'],
        'aliases': ['Manteia Tech'],
        'collection_method': 'Tavily 官网域名限定搜索',
        'trust_level': 'official',
        'description': '治疗计划、AI 自动勾画等软件厂商动态。',
        'enabled': True,
    },
    {
        'id': 'ankehigh',
        'name': '中核安科瑞',
        'short_name': '安科锐',
        'kind': 'vendor_official',
        'source_type': 'news',
        'homepage': 'https://www.ankehigh.com/',
        'domain_patterns': ['ankehigh.com'],
        'aliases': ['中核安科瑞', 'Anke High'],
        'collection_method': 'Tavily 官网域名限定搜索',
        'trust_level': 'official',
        'description': '国产放疗设备与相关解决方案厂商动态。',
        'enabled': True,
    },
    {
        'id': 'medical-xpress',
        'name': 'Medical Xpress',
        'short_name': 'MedXpress',
        'kind': 'industry_news',
        'source_type': 'news',
        'homepage': 'https://medicalxpress.com/',
        'domain_patterns': ['medicalxpress.com'],
        'aliases': [],
        'collection_method': 'Tavily 行业搜索',
        'trust_level': 'medium',
        'description': '医学科研与临床进展媒体。',
        'enabled': True,
    },
    {
        'id': 'medscape',
        'name': 'Medscape',
        'short_name': 'Medscape',
        'kind': 'industry_news',
        'source_type': 'news',
        'homepage': 'https://www.medscape.com/',
        'domain_patterns': ['medscape.com'],
        'aliases': [],
        'collection_method': 'Tavily 行业搜索',
        'trust_level': 'medium',
        'description': '临床医学新闻与专家观点来源。',
        'enabled': True,
    },
    {
        'id': 'biospace',
        'name': 'BioSpace',
        'short_name': 'BioSpace',
        'kind': 'industry_news',
        'source_type': 'news',
        'homepage': 'https://www.biospace.com/',
        'domain_patterns': ['biospace.com'],
        'aliases': [],
        'collection_method': 'Tavily 行业搜索',
        'trust_level': 'medium',
        'description': '生物医药公司、监管和商业动态。',
        'enabled': True,
    },
    {
        'id': 'tavily-search',
        'name': 'Tavily Search',
        'short_name': 'Tavily',
        'kind': 'search',
        'source_type': 'news',
        'homepage': 'https://www.tavily.com/',
        'domain_patterns': [],
        'aliases': ['Tavily'],
        'collection_method': 'Tavily News Search 聚合检索',
        'trust_level': 'aggregator',
        'description': '用于发现行业新闻，最终展示时会尽量归因到真实原文域名。',
        'enabled': True,
    },
]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r'^www\.', '', value)
    value = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '-', value)
    return re.sub(r'-+', '-', value).strip('-') or 'unknown'


def get_host(url: str) -> str:
    if not url:
        return ''
    try:
        host = urlparse(url).hostname or ''
        return re.sub(r'^www\.', '', host.lower())
    except Exception:
        return ''


def host_label(host: str) -> str:
    if not host:
        return 'Unknown'
    known = {
        'pubmed.ncbi.nlm.nih.gov': 'PubMed',
        'arxiv.org': 'arXiv',
        'nature.com': 'Nature',
        'thelancet.com': 'The Lancet',
        'medicalxpress.com': 'Medical Xpress',
    }
    if host in known:
        return known[host]
    parts = host.split('.')
    base = parts[-2] if len(parts) >= 2 else host
    return base.replace('-', ' ').title()


def _names_for(source: Dict[str, Any]) -> List[str]:
    values = [source.get('id', ''), source.get('name', ''), source.get('short_name', '')]
    values.extend(source.get('aliases', []))
    return [v for v in values if v]


def _matches_text(source: Dict[str, Any], text: str) -> bool:
    text_norm = text.strip().lower()
    if not text_norm:
        return False
    return any(text_norm == name.lower() for name in _names_for(source))


def _matches_host(source: Dict[str, Any], host: str) -> bool:
    if not host:
        return False
    return any(pattern.lower() in host for pattern in source.get('domain_patterns', []))


def get_source(source_id: str) -> Optional[Dict[str, Any]]:
    source_id_norm = slugify(source_id)
    for source in SOURCE_CATALOG:
        if slugify(source['id']) == source_id_norm:
            return dict(source)
    return None


def find_source_by_name(name: str) -> Optional[Dict[str, Any]]:
    for source in SOURCE_CATALOG:
        if _matches_text(source, name):
            return dict(source)
    return None


def find_source_by_host(host: str) -> Optional[Dict[str, Any]]:
    for source in SOURCE_CATALOG:
        if _matches_host(source, host):
            return dict(source)
    return None


def iter_sources_by_kind(kind: str) -> Iterable[Dict[str, Any]]:
    for source in SOURCE_CATALOG:
        if source.get('kind') == kind:
            yield dict(source)


def source_filter_terms(source: Dict[str, Any]) -> Dict[str, List[str]]:
    names = sorted(set(_names_for(source)))
    domains = sorted(set(source.get('domain_patterns', [])))
    return {'names': names, 'domains': domains}


def make_discovered_source(name: str, host: str = '') -> Dict[str, Any]:
    label = name or host_label(host)
    source_id = f"discovered-{slugify(host or label)}"
    return {
        'id': source_id,
        'name': label,
        'short_name': label,
        'kind': 'discovered',
        'source_type': 'mixed',
        'homepage': f"https://{host}" if host else '',
        'domain_patterns': [host] if host else [],
        'aliases': [],
        'collection_method': '由历史数据自动识别',
        'trust_level': 'unknown',
        'description': '数据库中已有内容的原始来源，尚未加入人工维护信源目录。',
        'enabled': False,
    }


def infer_source(item: Dict[str, Any]) -> Dict[str, Any]:
    meta = item.get('meta') or {}
    source_text = (item.get('source') or '').strip()
    url = item.get('url') or ''
    host = get_host(url)

    by_meta = get_source(str(meta.get('source_id', ''))) if meta.get('source_id') else None
    by_name = find_source_by_name(source_text)
    by_host = find_source_by_host(host)

    primary = by_meta or by_name or by_host
    mentioned_source = None
    note = ''

    if by_name and by_name.get('kind') == 'vendor_official' and host:
        host_matches_vendor = _matches_host(by_name, host)
        if not host_matches_vendor:
            primary = by_host or make_discovered_source(host_label(host), host)
            mentioned_source = by_name
            note = f"原文来自 {primary['name']}，由 {by_name['name']} 相关检索发现。"

    if not primary and source_text:
        primary = make_discovered_source(source_text, host)
    elif not primary:
        primary = make_discovered_source(host_label(host), host)

    result = dict(primary)
    result['kind_label'] = SOURCE_KIND_LABELS.get(result.get('kind', ''), result.get('kind', '来源'))
    result['origin_host'] = host
    result['origin_url'] = url
    result['note'] = note
    if mentioned_source:
        result['mentioned_source'] = {
            'id': mentioned_source['id'],
            'name': mentioned_source['name'],
            'kind': mentioned_source['kind'],
            'kind_label': SOURCE_KIND_LABELS.get(mentioned_source['kind'], mentioned_source['kind']),
        }
    return result


def source_catalog_summary() -> Dict[str, Any]:
    kinds: Dict[str, int] = {}
    for source in SOURCE_CATALOG:
        kind = source.get('kind', 'unknown')
        kinds[kind] = kinds.get(kind, 0) + 1
    return {
        'total_configured': len(SOURCE_CATALOG),
        'kind_labels': SOURCE_KIND_LABELS,
        'configured_kinds': kinds,
    }
