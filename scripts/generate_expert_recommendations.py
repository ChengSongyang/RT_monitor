#!/usr/bin/env python3
"""
联影医疗放疗事业部专家视角推荐理由生成器
每条推荐理由不少于100字，从专业维度深度剖析
"""
import sqlite3
import json
import re
from datetime import datetime

DB = 'data/rt_monitor.db'


def generate_expert_recommendation(title: str, abstract: str, source: str,
                                    journal: str, source_type: str, vendor: str = '') -> dict:
    """以联影放疗专家身份生成深度推荐理由"""
    text = (title + ' ' + (abstract or '')).lower()

    # === 分析维度 ===

    # 1. 技术方向识别
    tech_analysis = []
    if any(kw in text for kw in ['deep learning', 'neural network', 'cnn', 'rnn', 'lstm']):
        tech_analysis.append(('深度学习', '深度学习模型在放疗领域的应用持续深化'))
    if any(kw in text for kw in ['large language model', 'llm', 'gpt', 'transformer']):
        tech_analysis.append(('大语言模型', '大语言模型在放疗临床决策支持和文本理解方面展现出巨大潜力'))
    if any(kw in text for kw in ['segmentation', 'auto-segmentation', 'contouring', 'auto-contouring']):
        tech_analysis.append(('自动分割/勾画', '靶区和危及器官的自动勾画是放疗AI最成熟的应用场景'))
    if any(kw in text for kw in ['treatment planning', 'plan optimization', 'dose prediction']):
        tech_analysis.append(('治疗计划优化', 'AI驱动的治疗计划优化可显著缩短计划制作时间并提升计划质量'))
    if any(kw in text for kw in ['adaptive', 'online adaptive']):
        tech_analysis.append(('自适应放疗', '自适应放疗是精准放疗的重要发展方向'))
    if any(kw in text for kw in ['flash', 'flash radiotherapy']):
        tech_analysis.append(('FLASH放疗', 'FLASH放疗作为新兴技术，有望显著降低正常组织毒性'))
    if any(kw in text for kw in ['proton', 'carbon ion', 'heavy ion']):
        tech_analysis.append(('粒子治疗', '粒子治疗因其优越的剂量分布特性，与AI结合前景广阔'))
    if any(kw in text for kw in ['radiomics', 'radiogenomics']):
        tech_analysis.append(('影像组学', '影像组学为放疗疗效预测和预后评估提供了新维度'))
    if any(kw in text for kw in ['image registration', 'image fusion']):
        tech_analysis.append(('图像配准/融合', '图像配准精度直接影响放疗靶区勾画和剂量计算的准确性'))
    if any(kw in text for kw in ['quality assurance', 'quality control', 'qa']):
        tech_analysis.append(('质量保证', 'AI辅助的质量保证体系是放疗安全的重要保障'))
    if any(kw in text for kw in ['dose calculation', 'dose distribution']):
        tech_analysis.append(('剂量计算', 'AI加速剂量计算可实现实时剂量验证'))
    if any(kw in text for kw in ['reinforcement learning']):
        tech_analysis.append(('强化学习', '强化学习在放疗策略优化中具有独特优势'))
    if any(kw in text for kw in ['agent', 'multi-agent']):
        tech_analysis.append(('智能体', '多智能体协作有望实现放疗全流程的智能化管理'))
    if any(kw in text for kw in ['federated learning']):
        tech_analysis.append(('联邦学习', '联邦学习可在保护患者隐私的前提下实现多中心模型训练'))

    # 2. 癌种识别
    cancer_types = []
    cancer_map = {
        'head and neck': '头颈部肿瘤', 'nasopharyngeal': '鼻咽癌',
        'oropharyngeal': '口咽癌', 'hypopharyngeal': '下咽癌',
        'lung': '肺癌', 'nsclc': '非小细胞肺癌',
        'breast': '乳腺癌', 'prostate': '前列腺癌',
        'cervical': '宫颈癌', 'esophageal': '食管癌',
        'liver': '肝癌', 'hepatocellular': '肝细胞癌',
        'glioblastoma': '胶质母细胞瘤', 'glioma': '胶质瘤',
        'rectal': '直肠癌', 'colorectal': '结直肠癌',
        'pancreatic': '胰腺癌', 'bladder': '膀胱癌',
    }
    for kw, cancer in cancer_map.items():
        if kw in text and cancer not in cancer_types:
            cancer_types.append(cancer)

    # 3. 研究类型
    study_type = ''
    if 'meta-analysis' in text:
        study_type = '荟萃分析'
    elif 'systematic review' in text:
        study_type = '系统综述'
    elif 'randomized' in text:
        study_type = '随机对照研究'
    elif 'multicenter' in text or 'multi-center' in text:
        study_type = '多中心研究'
    elif 'retrospective' in text:
        study_type = '回顾性研究'
    elif 'prospective' in text:
        study_type = '前瞻性研究'
    elif 'phase 3' in text or 'phase iii' in text:
        study_type = 'III期临床试验'
    elif 'phase 2' in text or 'phase ii' in text:
        study_type = 'II期临床试验'
    elif 'phase 1' in text or 'phase i' in text:
        study_type = 'I期临床试验'
    elif 'review' in text:
        study_type = '综述'

    # 4. 期刊权威性
    journal_tier = ''
    top_journals = {
        'nature': '顶刊', 'lancet': '顶刊', 'nejm': '顶刊',
        'cell': '顶刊', 'science': '顶刊',
        'radiotherapy and oncology': '放疗权威期刊',
        'ijrobp': '放疗权威期刊', 'red journal': '放疗权威期刊',
        'medical physics': '物理权威期刊',
        'jco': '肿瘤权威期刊', 'lancet oncology': '肿瘤权威期刊',
    }
    for kw, tier in top_journals.items():
        if kw in journal.lower() or kw in source.lower():
            journal_tier = tier
            break

    # === 生成推荐理由 ===
    reasons = []

    # 核心要点
    if tech_analysis:
        tech_names = [t[0] for t in tech_analysis[:3]]
        reasons.append(f"本研究聚焦{'/'.join(tech_names)}在放疗中的应用")

    if study_type:
        reasons.append(f"研究设计为{study_type}")

    if cancer_types:
        reasons.append(f"针对{'、'.join(cancer_types[:2])}等癌种")

    # 技术价值分析
    if tech_analysis:
        for tech_name, tech_desc in tech_analysis[:2]:
            reasons.append(tech_desc)

    # 临床价值
    clinical_points = []
    if any(kw in text for kw in ['survival', 'overall survival']):
        clinical_points.append('生存获益')
    if any(kw in text for kw in ['toxicity', 'adverse', 'side effect']):
        clinical_points.append('毒性管理')
    if any(kw in text for kw in ['quality of life']):
        clinical_points.append('生活质量')
    if any(kw in text for kw in ['efficacy', 'response rate']):
        clinical_points.append('疗效评估')
    if clinical_points:
        reasons.append(f"研究关注{'、'.join(clinical_points)}等关键临床指标")

    # 产业竞争格局分析（新闻类）
    if source_type == 'news' and vendor:
        vendor_insights = {
            'Elekta': '医科达作为全球放疗设备龙头企业，其技术动态值得密切关注。联影放疗在追赶国际领先水平的过程中，需要深入分析医科达在AI赋能、自适应放疗等方面的技术布局，以便在产品差异化竞争中找到突破口。',
            'Varian': '瓦里安（现属西门子医疗）在放疗领域拥有深厚积累，其在AI驱动的治疗计划和自动化工作流方面的创新对联影放疗具有重要参考价值。需重点关注其在智能化放疗全流程解决方案上的进展。',
            'RaySearch': 'RaySearch作为放疗计划软件领域的领军企业，其RayStation平台在全球占据重要市场份额。联影放疗计划系统在算法精度和用户体验上与RaySearch存在差距，需密切跟踪其在AI计划优化、多中心协同等方面的技术演进。',
            '中核安科瑞': '中核安科瑞在质子/重离子治疗设备领域具有独特优势，其技术进展对联影放疗在粒子治疗领域的布局具有参考意义。',
            '新华医疗': '新华医疗作为国内放疗设备的重要参与者，其产品策略和市场动态对国内放疗市场格局有重要影响。联影放疗需关注其在基层市场和性价比路线上的竞争策略。',
            'Manteia': 'Manteia专注于AI放疗计划和自动勾画技术，是联影放疗在AI赛道上的直接竞争对手。需重点关注其技术成熟度、临床验证进展和商业化路径。',
        }
        if vendor in vendor_insights:
            reasons.append(vendor_insights[vendor])

    # 产品战略启示
    if tech_analysis:
        tech_names = [t[0] for t in tech_analysis]
        if '自动分割/勾画' in tech_names:
            reasons.append('对联影放疗而言，自动勾画是产品差异化竞争的核心赛道，需持续投入研发以提升模型精度和泛化能力')
        elif '治疗计划优化' in tech_names:
            reasons.append('AI治疗计划优化是联影放疗重点发力方向，需关注算法创新和临床验证的最新进展')
        elif '自适应放疗' in tech_names:
            reasons.append('自适应放疗代表了精准放疗的未来方向，联影需在MR引导自适应等前沿技术上加快布局')

    # 监管与准入
    if any(kw in text for kw in ['fda', 'clearance', 'approval', 'ce mark', '注册', '获批']):
        reasons.append('涉及监管审批进展，对理解放疗AI产品的准入路径和合规要求具有参考价值')

    # 组装最终推荐理由
    if not reasons:
        if source_type == 'paper':
            reasons.append(f'来自{source}的放疗AI交叉研究，为联影放疗技术研发提供参考')
        else:
            reasons.append(f'{vendor}的最新动态，对联影放疗的市场策略制定具有参考价值')

    # 确保推荐理由不少于100字
    recommendation = '。'.join(reasons) + '。'
    if len(recommendation) < 100:
        # 补充通用分析
        padding = []
        if source_type == 'paper':
            padding.append('该研究成果对联影放疗产品线的技术升级和功能迭代具有重要参考价值')
            padding.append('建议技术团队深入研读原文，评估其在联影放疗系统中的应用潜力')
        else:
            padding.append('该动态对联影放疗的市场布局和竞争策略制定具有直接参考意义')
            padding.append('建议产品和市场团队密切关注后续发展，及时调整应对策略')
        for p in padding:
            if len(recommendation) < 100:
                recommendation = recommendation.rstrip('。') + '。' + p + '。'

    # 计算评分
    score = 70
    if study_type in ['荟萃分析', '系统综述', 'III期临床试验']:
        score += 15
    elif study_type in ['随机对照研究', '多中心研究']:
        score += 10
    if len(tech_analysis) >= 2:
        score += 10
    elif len(tech_analysis) >= 1:
        score += 5
    if journal_tier == '顶刊':
        score += 15
    elif journal_tier:
        score += 10
    if len(cancer_types) >= 1:
        score += 5
    score = min(score, 98)

    return {
        'score': score,
        'is_featured': score >= 85,
        'recommendation_reason': recommendation,
        'tech_areas': [t[0] for t in tech_analysis],
        'cancer_types': cancer_types,
        'study_type': study_type,
        'journal_tier': journal_tier,
    }


def main():
    conn = sqlite3.connect(DB, timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')

    rows = conn.execute(
        'SELECT id, title, content, summary, source, source_type, ai, meta FROM content'
    ).fetchall()

    updated = 0
    for row in rows:
        cid, title, content, summary, source, stype, ai_json, meta_json = row
        ai = json.loads(ai_json) if ai_json else {}
        meta = json.loads(meta_json) if meta_json else {}
        journal = meta.get('journal', source)
        vendor = meta.get('vendor', '')

        result = generate_expert_recommendation(
            title, content or summary or '', source, journal, stype, vendor
        )

        ai['score'] = result['score']
        ai['is_featured'] = result['is_featured']
        ai['recommendation_reason'] = result['recommendation_reason']
        ai['tech_areas'] = result['tech_areas']
        ai['cancer_types'] = result['cancer_types']
        ai['study_type'] = result['study_type']

        conn.execute(
            'UPDATE content SET ai=?, updated_at=datetime("now") WHERE id=?',
            (json.dumps(ai, ensure_ascii=False), cid)
        )
        updated += 1

    conn.commit()
    conn.close()
    print(f'✅ 已更新 {updated} 条数据的专家推荐理由')


if __name__ == '__main__':
    main()
