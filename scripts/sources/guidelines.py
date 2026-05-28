"""Curated radiotherapy guideline entry points.

Guidelines are not crawled like news: most societies maintain living guideline
collections and gated PDFs. These records give clinicians a stable starting
point by disease site and association.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from . import make_content_id


GUIDELINE_SOURCES: List[Dict] = [
    {
        'association': 'ASTRO',
        'disease_site': '乳腺癌',
        'title': 'ASTRO 乳腺癌放疗指南入口',
        'summary': '覆盖全乳照射、部分乳照射、低分割和复发风险分层等乳腺癌放疗相关指南与实践建议。',
        'url': 'https://www.astro.org/provider-resources/guidelines/clinical-practice-guidelines#breast-cancer',
        'tags': ['乳腺癌', 'ASTRO', '低分割', '部分乳照射'],
    },
    {
        'association': 'ASTRO',
        'disease_site': '前列腺癌',
        'title': 'ASTRO 前列腺癌放疗指南入口',
        'summary': '用于追踪前列腺癌外照射、SBRT、术后/挽救放疗和综合治疗相关的 ASTRO 指南资源。',
        'url': 'https://www.astro.org/provider-resources/guidelines/clinical-practice-guidelines#prostate-cancer',
        'tags': ['前列腺癌', 'ASTRO', 'SBRT', '挽救放疗'],
    },
    {
        'association': 'NCCN',
        'disease_site': '肺癌',
        'title': 'NCCN 肺癌放疗相关指南入口',
        'summary': 'NCCN 肿瘤指南可按 NSCLC/SCLC 检索，适合查看分期、同步放化疗、SBRT 与姑息照射建议。',
        'url': 'https://www.nccn.org/guidelines/category_1#lung-cancer',
        'tags': ['肺癌', 'NCCN', 'NSCLC', 'SBRT'],
    },
    {
        'association': 'ESTRO',
        'disease_site': '宫颈癌/妇科肿瘤',
        'title': 'ESTRO 妇科肿瘤放疗指南入口',
        'summary': 'ESTRO 指南页可检索宫颈癌、子宫内膜癌等妇科肿瘤外照射、近距离放疗和靶区勾画建议。',
        'url': 'https://www.estro.org/Guidelines#gynecologic-cancer',
        'tags': ['宫颈癌', '妇科肿瘤', 'ESTRO', '近距离放疗'],
    },
    {
        'association': 'ASTRO',
        'disease_site': '脑转移瘤',
        'title': 'ASTRO 脑转移瘤放疗指南入口',
        'summary': '用于跟踪 SRS、全脑放疗、术后照射和系统治疗联合时机等脑转移瘤放疗指南。',
        'url': 'https://www.astro.org/provider-resources/guidelines/clinical-practice-guidelines#brain-metastases',
        'tags': ['脑转移瘤', 'ASTRO', 'SRS', '全脑放疗'],
    },
    {
        'association': 'ASTRO',
        'disease_site': '骨转移/姑息放疗',
        'title': 'ASTRO 骨转移与姑息放疗指南入口',
        'summary': '适合快速查阅骨转移疼痛控制、再照射、分割方案和姑息放疗适应证相关建议。',
        'url': 'https://www.astro.org/provider-resources/guidelines/clinical-practice-guidelines#bone-metastases',
        'tags': ['骨转移', '姑息放疗', 'ASTRO', '再照射'],
    },
    {
        'association': 'ESMO',
        'disease_site': '头颈部肿瘤',
        'title': 'ESMO 头颈部肿瘤综合治疗指南入口',
        'summary': '用于检索头颈部鳞癌、鼻咽癌等病种的综合治疗建议，并与放疗靶区和剂量策略联动参考。',
        'url': 'https://www.esmo.org/guidelines#head-and-neck-cancer',
        'tags': ['头颈部肿瘤', '鼻咽癌', 'ESMO', '同步放化疗'],
    },
    {
        'association': 'ASCO',
        'disease_site': '直肠癌/胃肠道肿瘤',
        'title': 'ASCO 胃肠道肿瘤放疗相关指南入口',
        'summary': '用于跟踪直肠癌新辅助放化疗、短程放疗、器官保留和多学科治疗相关指南。',
        'url': 'https://www.asco.org/guidelines#gastrointestinal-cancer',
        'tags': ['直肠癌', '胃肠道肿瘤', 'ASCO', '新辅助放疗'],
    },
    {
        'association': 'CSCO',
        'disease_site': '中国常见癌种',
        'title': 'CSCO 中国肿瘤诊疗指南入口',
        'summary': '适合结合中国临床路径、药物可及性和放疗资源配置，查看肺癌、乳腺癌、鼻咽癌等常见癌种指南。',
        'url': 'https://www.csco.org.cn/cn/index.aspx#guidelines',
        'tags': ['CSCO', '中国指南', '肺癌', '鼻咽癌'],
    },
]


def collect(days_back: int = 365) -> List[Dict]:
    del days_back
    today = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().timestamp()
    items: List[Dict] = []

    for source in GUIDELINE_SOURCES:
        raw_id = f"{source['association']}_{source['disease_site']}"
        recommendation = (
            f"{source['association']} 的{source['disease_site']}指南入口可作为临床方案、"
            '靶区剂量、分割方式和多学科讨论的基础参考；建议定期核对协会页面的更新日期和正式 PDF。'
        )
        items.append({
            'id': make_content_id('guideline', raw_id),
            'title': source['title'],
            'summary': source['summary'],
            'content': source['summary'],
            'url': source['url'],
            'source': source['association'],
            'source_type': 'news',
            'source_user': source['association'],
            'source_verified': True,
            'source_verified_reason': '指南/协会',
            'date': today,
            'timestamp': timestamp,
            'category': 'guideline',
            'tags': ['指南共识', *source['tags']],
            'images': [],
            'meta': {
                'association': source['association'],
                'disease_site': source['disease_site'],
                'collection_method': '人工维护指南入口',
            },
            'ai': {
                'title_cn': source['title'],
                'summary_cn': source['summary'],
                'score': 86,
                'is_featured': True,
                'recommendation_reason': recommendation,
            },
            'extra': {},
        })

    return items
