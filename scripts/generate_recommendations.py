#!/usr/bin/env python3
"""
生成高质量中文推荐理由（不翻译标题，独立生成）
"""
import sqlite3
import json
from datetime import datetime

DB = 'data/rt_monitor.db'


def generate_recommendation(title: str, abstract: str, source: str, journal: str, source_type: str) -> dict:
    """生成高质量中文推荐理由"""
    text = (title + ' ' + (abstract or '')).lower()
    reasons = []
    
    # 1. 研究类型判断
    study_type = ''
    if 'meta-analysis' in text:
        study_type = '荟萃分析'
        reasons.append('本研究为荟萃分析，通过系统整合多项研究数据，证据等级高')
    elif 'systematic review' in text:
        study_type = '系统综述'
        reasons.append('系统综述，全面梳理了该领域现有证据')
    elif 'randomized' in text and ('trial' in text or 'study' in text):
        study_type = '随机对照研究'
        reasons.append('随机对照研究设计，循证等级高')
    elif 'multicenter' in text or 'multi-center' in text:
        study_type = '多中心研究'
        reasons.append('多中心合作研究，样本量大，结论更具普适性')
    elif 'retrospective' in text:
        study_type = '回顾性研究'
    elif 'prospective' in text:
        study_type = '前瞻性研究'
    elif 'review' in text:
        study_type = '综述'
        reasons.append('综述性文章，系统总结领域进展')
    elif 'first-in-human' in text or 'phase 1' in text or 'phase i' in text:
        study_type = 'I期临床试验'
        reasons.append('首次人体试验/早期临床研究，探索安全性和初步疗效')
    elif 'phase 2' in text or 'phase ii' in text:
        study_type = 'II期临床试验'
        reasons.append('II期临床试验，评估疗效和安全性')
    elif 'phase 3' in text or 'phase iii' in text:
        study_type = 'III期临床试验'
        reasons.append('III期大型临床试验，结果对临床实践具有重要指导意义')
    
    # 2. 技术方向分析
    tech_areas = []
    if any(kw in text for kw in ['deep learning', 'machine learning', 'neural network', 'cnn', 'rnn', 'lstm']):
        tech_areas.append('深度学习')
    if any(kw in text for kw in ['artificial intelligence', ' ai ', 'machine intelligence']):
        tech_areas.append('人工智能')
    if any(kw in text for kw in ['large language model', 'llm', 'gpt', 'chatgpt', 'transformer']):
        tech_areas.append('大语言模型')
    if any(kw in text for kw in ['segmentation', 'auto-segmentation', 'contouring', 'delineation']):
        tech_areas.append('自动分割/勾画')
    if any(kw in text for kw in ['treatment planning', 'plan optimization', 'dose prediction']):
        tech_areas.append('治疗计划优化')
    if any(kw in text for kw in ['adaptive', 'online adaptive']):
        tech_areas.append('自适应放疗')
    if any(kw in text for kw in ['flash', 'flash radiotherapy']):
        tech_areas.append('FLASH放疗')
    if any(kw in text for kw in ['proton', 'carbon ion', 'heavy ion']):
        tech_areas.append('粒子治疗')
    if any(kw in text for kw in ['immunotherapy', 'immune checkpoint', 'pd-1', 'pd-l1', 'car-t']):
        tech_areas.append('免疫治疗')
    if any(kw in text for kw in ['radiomics', 'radiogenomics']):
        tech_areas.append('影像组学')
    if any(kw in text for kw in ['biomarker', 'proteomics', 'genomics', 'genetic']):
        tech_areas.append('生物标志物')
    if any(kw in text for kw in ['dose', 'dosimetric', 'dosimetry']):
        tech_areas.append('剂量学')
    if any(kw in text for kw in ['image', 'imaging', 'mri', 'ct', 'pet', 'cbct']):
        tech_areas.append('影像技术')
    if any(kw in text for kw in ['robot', 'automated', 'automatic']):
        tech_areas.append('自动化/机器人')
    if any(kw in text for kw in ['real-time', 'online']):
        tech_areas.append('实时技术')
    
    if tech_areas:
        reasons.append('本研究涉及' + '、'.join(tech_areas[:3]) + '等前沿技术方向')
    
    # 3. 癌种分析
    cancer_types = []
    cancer_keywords = {
        'head and neck': '头颈部肿瘤', 'nasopharyngeal': '鼻咽癌',
        'oropharyngeal': '口咽癌', 'hypopharyngeal': '下咽癌',
        'oral': '口腔癌', 'laryngeal': '喉癌',
        'lung': '肺癌', 'nsclc': '非小细胞肺癌',
        'breast': '乳腺癌', 'prostate': '前列腺癌',
        'cervical': '宫颈癌', 'cervix': '宫颈癌',
        'esophageal': '食管癌', 'liver': '肝癌',
        'hepatocellular': '肝细胞癌', 'glioblastoma': '胶质母细胞瘤',
        'glioma': '胶质瘤', 'brain': '脑肿瘤',
        'rectal': '直肠癌', 'colorectal': '结直肠癌',
        'pancreatic': '胰腺癌', 'bladder': '膀胱癌',
        'kidney': '肾癌', 'renal': '肾癌',
        'lymphoma': '淋巴瘤', 'melanoma': '黑色素瘤',
        'sarcoma': '肉瘤', 'thyroid': '甲状腺癌',
        'gastric': '胃癌', 'stomach': '胃癌',
        'ovarian': '卵巢癌', 'endometrial': '子宫内膜癌',
        'uterine': '子宫癌', 'cervix': '宫颈癌',
    }
    for kw, cancer in cancer_keywords.items():
        if kw in text and cancer not in cancer_types:
            cancer_types.append(cancer)
    if cancer_types:
        reasons.append('研究聚焦于' + '、'.join(cancer_types[:2]) + '的诊治')
    
    # 4. 临床意义
    clinical_points = []
    if any(kw in text for kw in ['survival', 'overall survival', 'os ']):
        clinical_points.append('总生存期')
    if any(kw in text for kw in ['progression-free', 'pfs']):
        clinical_points.append('无进展生存期')
    if any(kw in text for kw in ['local control']):
        clinical_points.append('局部控制率')
    if any(kw in text for kw in ['toxicity', 'adverse event', 'side effect']):
        clinical_points.append('毒副反应')
    if any(kw in text for kw in ['quality of life']):
        clinical_points.append('生活质量')
    if any(kw in text for kw in ['dose escalation', 'dose painting']):
        clinical_points.append('剂量优化')
    if any(kw in text for kw in ['response rate', 'objective response']):
        clinical_points.append('缓解率')
    
    if clinical_points:
        reasons.append('重点关注' + '、'.join(clinical_points[:2]) + '等临床指标')
    
    # 5. 创新性
    if any(kw in text for kw in ['novel', 'first', 'new approach', 'new method', 'innovative']):
        reasons.append('提出了创新性的方法或策略')
    if any(kw in text for kw in ['outperform', 'superior', 'better', 'improved', 'significant']):
        reasons.append('结果显示优于现有方法或有显著改善')
    if any(kw in text for kw in ['validation', 'validated', 'benchmark']):
        reasons.append('经过严格验证，结果可靠')
    
    # 6. 期刊/来源权威性
    top_sources = {
        'nature': 'Nature', 'lancet': 'Lancet', 'nejm': 'NEJM',
        'cell': 'Cell', 'science': 'Science', 'jco': 'JCO',
        'radiotherapy and oncology': 'Radiotherapy and Oncology',
        'ijrobp': 'IJROBP', 'medical physics': 'Medical Physics',
        'nature medicine': 'Nature Medicine', 'lancet oncology': 'Lancet Oncology',
    }
    for kw, name in top_sources.items():
        if kw in journal.lower() or kw in source.lower():
            reasons.append(f'发表于权威期刊 {name}，影响力高')
            break
    
    # 组装推荐理由
    if not reasons:
        reasons.append(f'来自{source}的{study_type or "放射治疗领域"}研究')
    
    # 计算评分
    score = 70
    if study_type in ['荟萃分析', '系统综述', 'III期临床试验']:
        score += 15
    elif study_type in ['随机对照研究', '多中心研究', 'II期临床试验']:
        score += 10
    elif study_type in ['前瞻性研究']:
        score += 5
    
    if len(tech_areas) >= 2:
        score += 10
    elif len(tech_areas) >= 1:
        score += 5
    
    if len(cancer_types) >= 1:
        score += 5
    
    for kw in top_sources:
        if kw in journal.lower() or kw in source.lower():
            score += 10
            break
    
    if any(kw in text for kw in ['novel', 'first', 'innovative']):
        score += 5
    if any(kw in text for kw in ['significant', 'outperform', 'superior']):
        score += 5
    
    score = min(score, 98)
    
    return {
        'score': score,
        'is_featured': score >= 80,
        'recommendation_reason': '；'.join(reasons) + '。',
        'study_type': study_type,
        'tech_areas': tech_areas[:5],
        'cancer_types': cancer_types[:3],
    }


def main():
    conn = sqlite3.connect(DB, timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    
    rows = conn.execute(
        'SELECT id, title, summary, content, source, source_type, ai, meta FROM content'
    ).fetchall()
    
    updated = 0
    for row in rows:
        cid, title, summary, content, source, stype, ai_json, meta_json = row
        ai = json.loads(ai_json) if ai_json else {}
        meta = json.loads(meta_json) if meta_json else {}
        journal = meta.get('journal', source)
        
        # 生成推荐理由
        result = generate_recommendation(title, content or summary or '', source, journal, stype)
        
        # 更新 AI 字段
        ai['score'] = result['score']
        ai['is_featured'] = result['is_featured']
        ai['recommendation_reason'] = result['recommendation_reason']
        ai['study_type'] = result['study_type']
        ai['tech_areas'] = result['tech_areas']
        ai['cancer_types'] = result['cancer_types']
        
        conn.execute(
            'UPDATE content SET ai=?, updated_at=datetime("now") WHERE id=?',
            (json.dumps(ai, ensure_ascii=False), cid)
        )
        updated += 1
    
    conn.commit()
    conn.close()
    print(f'✅ 已更新 {updated} 条数据的推荐理由')


if __name__ == '__main__':
    main()
