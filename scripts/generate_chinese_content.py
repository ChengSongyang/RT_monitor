#!/usr/bin/env python3
"""为数据库中的内容生成中文推荐理由和论文解读报告"""
import sqlite3
import json
from datetime import datetime

DB = 'data/rt_monitor.db'
conn = sqlite3.connect(DB, timeout=30)
conn.execute('PRAGMA journal_mode=WAL')

TERM_MAP = {
    'deep learning': '深度学习', 'machine learning': '机器学习',
    'artificial intelligence': '人工智能', 'large language model': '大语言模型',
    'foundation model': '基础模型', 'transformer': 'Transformer',
    'auto-segmentation': '自动分割', 'segmentation': '分割',
    'treatment planning': '治疗计划', 'dose prediction': '剂量预测',
    'organs at risk': '危及器官', 'radiotherapy': '放射治疗',
    'radiation therapy': '放射治疗', 'radiation oncology': '放射肿瘤学',
    'intensity-modulated': '调强放射治疗', 'volumetric modulated': '容积旋转调强放疗',
    'stereotactic': '立体定向放疗', 'image-guided': '图像引导放射治疗',
    'adaptive': '自适应放射治疗', 'proton': '质子治疗',
    'clinical trial': '临床试验', 'meta-analysis': '荟萃分析',
    'systematic review': '系统综述', 'overall survival': '总生存期',
    'toxicity': '毒性反应', 'immunotherapy': '免疫治疗', 'radiomics': '影像组学',
    'head and neck': '头颈部', 'nasopharyngeal': '鼻咽癌',
    'lung cancer': '肺癌', 'breast cancer': '乳腺癌',
    'prostate': '前列腺癌', 'glioblastoma': '胶质母细胞瘤',
    'dose': '剂量学', 'linear accelerator': '直线加速器',
}

rows = conn.execute(
    'SELECT id, title, content, summary, source, source_type, url, date, ai, meta FROM content'
).fetchall()

updated = 0
reports_gen = 0

for row in rows:
    cid, title, content, summary, source, stype, url, date_str, ai_json, meta_json = row
    ai = json.loads(ai_json) if ai_json else {}
    meta = json.loads(meta_json) if meta_json else {}
    journal = meta.get('journal', source)
    text_lower = ((title or '') + ' ' + (content or '')).lower()

    # --- Generate Chinese recommendation reason ---
    score = 70
    reasons = []
    top_j = ['nature', 'lancet', 'nejm', 'cell', 'science', 'jco',
             'radiotherapy and oncology', 'ijrobp', 'medical physics']
    if any(j in journal.lower() or j in source.lower() for j in top_j):
        score += 15
        reasons.append('来自权威来源 ' + source)

    hot = {'deep learning': '深度学习', 'ai': '人工智能', 'machine learning': '机器学习',
           'large language model': '大语言模型', 'segmentation': '自动分割',
           'treatment planning': '治疗计划', 'adaptive': '自适应放疗',
           'flash': 'FLASH放疗', 'proton': '质子治疗', 'immunotherapy': '免疫治疗',
           'clinical trial': '临床试验', 'radiomics': '影像组学'}
    matched = []
    for kw, lb in hot.items():
        if kw in text_lower and lb not in matched:
            matched.append(lb)
    if matched:
        score += min(len(matched) * 3, 15)
        reasons.append('涉及热点方向：' + '、'.join(matched[:3]))

    if any(kw in text_lower for kw in ['multicenter', 'meta-analysis', 'systematic review', 'randomized']):
        score += 8
        reasons.append('高质量循证研究')

    score = min(score, 98)
    reason = '；'.join(reasons) + '。' if reasons else '来自' + source + '的放疗领域研究。'

    ai['score'] = score
    ai['recommendation_reason'] = reason
    ai['is_featured'] = score >= 80

    # --- Generate Chinese summary for papers ---
    if stype == 'paper' and summary:
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in summary)
        if not has_chinese:
            topics = []
            for en, zh in TERM_MAP.items():
                if en.lower() in text_lower and zh not in topics:
                    topics.append(zh)
            if topics:
                summary = '本研究涉及' + '、'.join(topics[:5]) + '等领域。' + (content or '')[:150]

    conn.execute(
        'UPDATE content SET ai=?, summary=?, updated_at=datetime("now") WHERE id=?',
        (json.dumps(ai, ensure_ascii=False), summary, cid)
    )
    updated += 1

    # --- Generate report for papers ---
    if stype == 'paper':
        existing = conn.execute('SELECT id FROM reports WHERE content_id=?', (cid,)).fetchone()
        if not existing:
            topics = []
            for en, zh in TERM_MAP.items():
                if en.lower() in text_lower and zh not in topics:
                    topics.append(zh)

            study_type = '研究'
            if 'meta-analysis' in text_lower:
                study_type = '荟萃分析'
            elif 'systematic review' in text_lower:
                study_type = '系统综述'
            elif 'randomized' in text_lower:
                study_type = '随机对照试验'
            elif 'deep learning' in text_lower or 'machine learning' in text_lower:
                study_type = 'AI/深度学习研究'
            elif 'review' in text_lower:
                study_type = '综述'

            authors = meta.get('authors', '')

            findings = []
            if any(kw in text_lower for kw in ['survival', 'overall survival']):
                findings.append('- 关注**总生存期**等关键生存指标')
            if any(kw in text_lower for kw in ['toxicity', 'adverse']):
                findings.append('- 评估了**毒副反应**和安全性')
            if any(kw in text_lower for kw in ['deep learning', 'ai', 'artificial intelligence']):
                findings.append('- 利用**AI/深度学习**提升放疗精准度')
            if 'segmentation' in text_lower:
                findings.append('- 实现**自动靶区/器官分割**')
            if any(kw in text_lower for kw in ['dose', 'dosimetric']):
                findings.append('- 进行**剂量学分析**')
            if any(kw in text_lower for kw in ['clinical trial', 'randomized', 'phase']):
                findings.append('- 基于**临床试验**数据')
            if 'immunotherapy' in text_lower:
                findings.append('- 探索**免疫治疗联合放疗**')
            if not findings:
                findings.append('- 为放射治疗领域提供新见解')

            findings_text = '\n'.join(findings)
            topics_text = '、'.join(topics[:6]) if topics else '放射治疗'
            cl_topics = '涉及的' + '、'.join(topics[:3]) + '等方向' if topics else '研究结果'

            report = f'''# {title}

## 📋 研究概要
- **来源**: {source}
- **期刊**: {journal}
- **作者**: {authors[:100] if authors else '未标注'}
- **研究类型**: {study_type}
- **涉及领域**: {topics_text}

## 🔬 研究背景
{content[:500] if content else '暂无摘要信息。'}

## 💡 核心发现
{findings_text}

## 🏥 临床意义
本{study_type}为放射治疗临床实践提供了参考依据。{cl_topics}对优化治疗策略具有指导价值。

## 📎 原文链接
- [查看原文]({url})

---
*本解读由 AI 自动生成，仅供参考。*
'''
            year = str(datetime.now().year)
            month = f'{datetime.now().month:02d}'
            if date_str:
                if len(date_str) >= 4 and date_str[:4].isdigit():
                    year = date_str[:4]
                if len(date_str) >= 7 and date_str[5:7].isdigit():
                    month = date_str[5:7]
                elif 'May' in date_str: month = '05'
                elif 'Jun' in date_str: month = '06'
                elif 'Jan' in date_str: month = '01'
                elif 'Feb' in date_str: month = '02'
                elif 'Mar' in date_str: month = '03'
                elif 'Apr' in date_str: month = '04'
                elif 'Jul' in date_str: month = '07'
                elif 'Aug' in date_str: month = '08'
                elif 'Sep' in date_str: month = '09'
                elif 'Oct' in date_str: month = '10'
                elif 'Nov' in date_str: month = '11'
                elif 'Dec' in date_str: month = '12'
            src_dir = source.replace(' ', '_')
            rpath = 'reports/{}/{}/{}/{}'.format(year, month, src_dir, cid)

            conn.execute(
                '''INSERT OR REPLACE INTO reports
                (id, content_id, report_type, file_path, year, month, source, md_content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (cid, cid, 'ai_analysis', rpath, int(year), int(month), source, report)
            )
            reports_gen += 1

conn.commit()
conn.close()
print('✅ 更新推荐理由: {} 条'.format(updated))
print('✅ 生成论文解读: {} 条'.format(reports_gen))
