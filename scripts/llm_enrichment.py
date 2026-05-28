#!/usr/bin/env python3
"""OpenAI-compatible enrichment for RT Monitor content.

The crawler stores original source text, while the UI should read Chinese
editorial fields from ``ai`` and paper reports from ``reports``.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_BASE_URL = 'https://token-plan-cn.xiaomimimo.com/v1'
DEFAULT_MODEL = 'mimo-v2.5'


def _load_local_env() -> None:
    root = os.path.dirname(os.path.dirname(__file__))
    for filename in ('.env.local', '.env'):
        path = os.path.join(root, filename)
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped or stripped.startswith('#') or '=' not in stripped:
                    continue
                key, value = stripped.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value


_load_local_env()


def _has_chinese(text: str) -> bool:
    return any('\u4e00' <= char <= '\u9fff' for char in text or '')


def _truncate(text: str, limit: int) -> str:
    text = re.sub(r'\s+', ' ', text or '').strip()
    return text[:limit]


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError('No JSON object found in model response')


def _api_key() -> str:
    return (
        os.environ.get('TOKEN_PLAN_API_KEY')
        or os.environ.get('XIAOMI_TOKEN_PLAN_API_KEY')
        or os.environ.get('OPENAI_API_KEY')
        or ''
    )


def _base_url() -> str:
    return (
        os.environ.get('TOKEN_PLAN_BASE_URL')
        or os.environ.get('OPENAI_BASE_URL')
        or DEFAULT_BASE_URL
    ).rstrip('/')


def _model() -> str:
    return os.environ.get('TOKEN_PLAN_MODEL') or os.environ.get('OPENAI_MODEL') or DEFAULT_MODEL


def _chat_json(messages: List[Dict[str, str]], max_tokens: int) -> Dict[str, Any]:
    key = _api_key()
    if not key:
        raise RuntimeError('TOKEN_PLAN_API_KEY is not configured')

    payload = {
        'model': _model(),
        'messages': messages,
        'temperature': 0.2,
        'max_tokens': max_tokens,
        'response_format': {'type': 'json_object'},
    }
    req = urllib.request.Request(
        f'{_base_url()}/chat/completions',
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}',
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    content = data['choices'][0]['message']['content']
    return _extract_json(content)


def _fallback_translate(text: str) -> str:
    if not text or _has_chinese(text):
        return text or ''
    try:
        from translate_to_chinese import translate_terms
        translated = translate_terms(text)
        return translated
    except Exception:
        return text


def _fallback_reason(item: Dict[str, Any]) -> Dict[str, Any]:
    ai = dict(item.get('ai') or {})
    title = item.get('title', '')
    body = item.get('content') or item.get('summary') or ''
    source = item.get('source', '')
    meta = item.get('meta') or {}
    journal = item.get('journal') or meta.get('journal') or source
    source_type = item.get('source_type', 'news')

    try:
        from generate_expert_recommendations import generate_expert_recommendation
        result = generate_expert_recommendation(
            title,
            body,
            source,
            journal,
            source_type,
            meta.get('vendor') or meta.get('mentioned_vendor') or '',
        )
    except Exception:
        result = {
            'score': ai.get('score', 70),
            'is_featured': ai.get('is_featured', False),
            'recommendation_reason': ai.get('recommendation_reason')
            or f'来自{source or "该来源"}的放疗相关内容，建议结合原文进一步评估其临床、技术或产业价值。',
        }

    return {
        'title_cn': _fallback_translate(title),
        'summary_cn': _fallback_translate(body)[:220],
        'recommendation_reason': result.get('recommendation_reason', ''),
        'score': int(result.get('score') or ai.get('score') or 70),
        'is_featured': bool(result.get('is_featured') or ai.get('is_featured') or False),
        'tags_cn': [],
    }


def _fallback_report(item: Dict[str, Any], enrichment: Dict[str, Any]) -> str:
    title_cn = enrichment.get('title_cn') or item.get('title', '未命名论文')
    summary_cn = enrichment.get('summary_cn') or item.get('content') or item.get('summary') or '暂无摘要信息。'
    reason = enrichment.get('recommendation_reason', '')
    meta = item.get('meta') or {}
    source = item.get('source', '')
    journal = item.get('journal') or meta.get('journal') or source
    authors = item.get('source_user') or item.get('authors') or meta.get('authors') or '未标注'
    url = item.get('url', '')

    return f"""# {title_cn}

## 研究概要
- 来源：{source}
- 期刊：{journal}
- 作者：{authors}

## 中文摘要
{summary_cn}

## 推荐理由
{reason or '该研究与放射治疗实践相关，建议阅读全文后结合本地业务场景评估。'}

## 临床与产品启示
这篇论文可作为放疗技术、临床流程或产品策略评估的输入。重点关注其研究对象、数据规模、主要终点、验证方式以及是否具备跨中心泛化能力。

## 原文链接
- [查看原文]({url})

---
本解读由 AI 自动生成，仅供内部信息筛选参考。
"""


def _build_messages(item: Dict[str, Any], include_report: bool) -> List[Dict[str, str]]:
    meta = item.get('meta') or {}
    title = _truncate(item.get('title', ''), 500)
    body = _truncate(item.get('content') or item.get('summary') or '', 3200)
    source = item.get('source', '')
    source_type = item.get('source_type', 'news')
    category = item.get('category', '')
    journal = item.get('journal') or meta.get('journal') or ''
    url = item.get('url', '')
    vendor = meta.get('vendor') or meta.get('mentioned_vendor') or item.get('mentioned_vendor') or ''

    report_instruction = ''
    if include_report:
        report_instruction = """
如 source_type=paper，请额外输出 report_md：Markdown 格式论文解读，包含以下小节：
研究背景、方法与数据、关键发现、临床/产品启示、局限与注意、原文链接。
不要编造样本量、结果数值或结论；原文没有给出的内容写“摘要未提供”。"""

    system = (
        '你是联影放疗事业部的信息分析编辑，熟悉放射肿瘤学、医学物理、'
        '放疗设备、AI自动勾画、治疗计划、自适应放疗和行业竞争格局。'
        '你必须输出严格 JSON，不要 Markdown 包裹。'
    )
    user = f"""
请将这条信息加工成前端可直接展示的中文内容。

要求：
1. title_cn：简洁中文标题，保留必要英文缩写和专有名词。
2. summary_cn：80-180字中文摘要，说明事件/研究对象、方法或场景、关键结论；信息不足时不要脑补。
3. recommendation_reason：60-140字中文推荐理由，必须具体说明为什么值得放疗团队关注；论文看方法/证据/临床转化，新闻看产业/监管/竞品/产品启示，指南看癌种/协会/临床使用价值。避免“具有重要参考价值”这类空话单独成句。
4. score：0-100整数；核心放疗期刊、指南、监管审批、临床试验、AI放疗产品进展可加分。
5. is_featured：score>=85 时为 true。
6. tags_cn：3-6个中文标签。
{report_instruction}

输出 JSON 字段：
{{
  "title_cn": "...",
  "summary_cn": "...",
  "recommendation_reason": "...",
  "score": 0,
  "is_featured": false,
  "tags_cn": ["..."],
  "report_md": "..."
}}

原始信息：
- source_type: {source_type}
- category: {category}
- source: {source}
- journal: {journal}
- vendor: {vendor}
- url: {url}
- title: {title}
- content: {body}
"""
    return [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]


def enrich_item(item: Dict[str, Any], include_report: Optional[bool] = None, force: bool = False) -> Dict[str, Any]:
    """Return a copy enriched with ai.title_cn, ai.summary_cn and optional report_md."""
    enriched_item = dict(item)
    ai = dict(enriched_item.get('ai') or {})
    source_type = enriched_item.get('source_type', 'news')
    should_report = source_type == 'paper' if include_report is None else include_report

    has_core_fields = all(
        ai.get(key)
        for key in ('title_cn', 'summary_cn', 'recommendation_reason')
    )
    has_report = bool(enriched_item.get('report_md') or (enriched_item.get('meta') or {}).get('report_path'))
    if not force and has_core_fields and (not should_report or has_report):
        return enriched_item

    result: Dict[str, Any]
    try:
        result = _chat_json(
            _build_messages(enriched_item, include_report=should_report),
            max_tokens=1800 if should_report else 800,
        )
    except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as exc:
        print(f"  [WARN] AI enrichment fallback for {enriched_item.get('id', '')}: {exc}", file=sys.stderr)
        result = _fallback_reason(enriched_item)
        if should_report:
            result['report_md'] = _fallback_report(enriched_item, result)

    title_cn = str(result.get('title_cn') or ai.get('title_cn') or _fallback_translate(enriched_item.get('title', ''))).strip()
    summary_source = enriched_item.get('content') or enriched_item.get('summary') or ''
    summary_cn = str(result.get('summary_cn') or ai.get('summary_cn') or _fallback_translate(summary_source)[:220]).strip()
    recommendation_reason = str(
        result.get('recommendation_reason')
        or ai.get('recommendation_reason')
        or _fallback_reason(enriched_item).get('recommendation_reason')
    ).strip()

    score_value = result.get('score', ai.get('score', 70))
    try:
        score = max(0, min(100, int(round(float(score_value)))))
    except Exception:
        score = 70

    ai.update({
        'title_cn': title_cn,
        'summary_cn': summary_cn,
        'recommendation_reason': recommendation_reason,
        'score': score,
        'is_featured': bool(result.get('is_featured', score >= 85)),
    })

    tags_cn = result.get('tags_cn') or []
    if isinstance(tags_cn, list):
        current_tags = list(enriched_item.get('tags') or [])
        for tag in tags_cn:
            tag_text = str(tag).strip()
            if tag_text and tag_text not in current_tags:
                current_tags.append(tag_text)
        enriched_item['tags'] = current_tags[:10]

    enriched_item['ai'] = ai

    report_md = str(result.get('report_md') or '').strip()
    if should_report and not report_md:
        report_md = _fallback_report(enriched_item, ai)
    if should_report and report_md:
        enriched_item['report_md'] = report_md

    return enriched_item


def enrich_items(items: Iterable[Dict[str, Any]], source_name: str = '') -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for index, item in enumerate(items, 1):
        label = item.get('title') or item.get('id') or f'item {index}'
        print(f"  🧠 中文化/点评 {source_name} {index}: {label[:56]}", file=sys.stderr)
        enriched.append(enrich_item(item))
    return enriched
