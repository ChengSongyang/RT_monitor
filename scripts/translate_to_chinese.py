#!/usr/bin/env python3
"""
将数据库中的英文内容翻译/转换为中文
- 生成中文标题
- 生成中文摘要
- 生成详细的中文推荐理由
"""
import sqlite3
import json
import re
from datetime import datetime

DB = 'data/rt_monitor.db'

# 放疗领域术语映射
TERM_MAP = {
    'deep learning': '深度学习',
    'machine learning': '机器学习',
    'artificial intelligence': '人工智能',
    'AI': 'AI',
    'large language model': '大语言模型',
    'LLM': '大语言模型',
    'foundation model': '基础模型',
    'transformer': 'Transformer模型',
    'auto-segmentation': '自动分割',
    'segmentation': '分割',
    'treatment planning': '治疗计划',
    'dose prediction': '剂量预测',
    'dose-volume histogram': '剂量体积直方图',
    'DVH': 'DVH',
    'organs at risk': '危及器官',
    'OAR': '危及器官',
    'clinical target volume': '临床靶区',
    'CTV': '临床靶区',
    'planning target volume': '计划靶区',
    'PTV': '计划靶区',
    'gross tumor volume': '大体肿瘤体积',
    'GTV': '大体肿瘤体积',
    'radiotherapy': '放射治疗',
    'radiation therapy': '放射治疗',
    'radiation oncology': '放射肿瘤学',
    'intensity-modulated radiation therapy': '调强放射治疗',
    'IMRT': '调强放疗',
    'volumetric modulated arc therapy': '容积旋转调强放疗',
    'VMAT': 'VMAT放疗',
    'stereotactic body radiation therapy': '立体定向体部放疗',
    'SBRT': 'SBRT',
    'stereotactic radiosurgery': '立体定向放射外科',
    'SRS': 'SRS',
    'image-guided radiation therapy': '图像引导放射治疗',
    'IGRT': 'IGRT',
    'adaptive radiation therapy': '自适应放射治疗',
    'FLASH radiotherapy': 'FLASH放疗',
    'FLASH': 'FLASH放疗',
    'proton therapy': '质子治疗',
    'proton': '质子',
    'carbon ion therapy': '碳离子治疗',
    'carbon ion': '碳离子',
    'head and neck': '头颈部',
    'head and neck cancer': '头颈部肿瘤',
    'HNC': '头颈部肿瘤',
    'nasopharyngeal carcinoma': '鼻咽癌',
    'NPC': '鼻咽癌',
    'non-small cell lung cancer': '非小细胞肺癌',
    'NSCLC': '非小细胞肺癌',
    'lung cancer': '肺癌',
    'breast cancer': '乳腺癌',
    'prostate cancer': '前列腺癌',
    'cervical cancer': '宫颈癌',
    'esophageal cancer': '食管癌',
    'hepatocellular carcinoma': '肝细胞癌',
    'HCC': '肝细胞癌',
    'glioblastoma': '胶质母细胞瘤',
    'GBM': '胶质母细胞瘤',
    'rectal cancer': '直肠癌',
    'colorectal cancer': '结直肠癌',
    'pancreatic cancer': '胰腺癌',
    'liver cancer': '肝癌',
    'kidney cancer': '肾癌',
    'bladder cancer': '膀胱癌',
    'lymphoma': '淋巴瘤',
    'melanoma': '黑色素瘤',
    'sarcoma': '肉瘤',
    'clinical trial': '临床试验',
    'randomized controlled trial': '随机对照试验',
    'RCT': '随机对照试验',
    'meta-analysis': '荟萃分析',
    'systematic review': '系统综述',
    'retrospective study': '回顾性研究',
    'prospective study': '前瞻性研究',
    'multicenter': '多中心',
    'multi-center': '多中心',
    'overall survival': '总生存期',
    'OS': '总生存期',
    'progression-free survival': '无进展生存期',
    'PFS': '无进展生存期',
    'local control': '局部控制率',
    'disease-free survival': '无病生存期',
    'DFS': '无病生存期',
    'toxicity': '毒性反应',
    'adverse event': '不良事件',
    'side effect': '副作用',
    'radiation pneumonitis': '放射性肺炎',
    'radiation esophagitis': '放射性食管炎',
    'xerostomia': '口干症',
    'dysphagia': '吞咽困难',
    'dermatitis': '皮炎',
    'linear accelerator': '直线加速器',
    'LINAC': '直线加速器',
    'gamma knife': '伽马刀',
    'cyberknife': '射波刀',
    'tomotherapy': '螺旋断层放疗',
    'TOMO': 'TOMO放疗',
    'cone-beam CT': '锥形束CT',
    'CBCT': 'CBCT',
    'MRI-guided': 'MRI引导',
    'MR-Linac': 'MR加速器',
    'PET/CT': 'PET/CT',
    'immunotherapy': '免疫治疗',
    'checkpoint inhibitor': '免疫检查点抑制剂',
    'PD-1': 'PD-1',
    'PD-L1': 'PD-L1',
    'combination therapy': '联合治疗',
    'concurrent chemoradiotherapy': '同步放化疗',
    'CCRT': '同步放化疗',
    'neoadjuvant': '新辅助',
    'adjuvant': '辅助治疗',
    'recurrence': '复发',
    'metastasis': '转移',
    'lymph node': '淋巴结',
    'survival': '生存',
    'prognosis': '预后',
    'biomarker': '生物标志物',
    'radiomics': '影像组学',
    'radiogenomics': '影像基因组学',
    'dose': '剂量',
    'dosimetric': '剂量学',
    'dosimetry': '剂量学',
    'quality of life': '生活质量',
    'QoL': '生活质量',
    'performance status': '体能状态',
    'ECOG': 'ECOG',
    'Karnofsky': 'KPS',
    'pathological complete response': '病理完全缓解',
    'pCR': '病理完全缓解',
    'objective response rate': '客观缓解率',
    'ORR': '客观缓解率',
    'complete response': '完全缓解',
    'CR': '完全缓解',
    'partial response': '部分缓解',
    'PR': '部分缓解',
    'stable disease': '疾病稳定',
    'SD': '疾病稳定',
    'progressive disease': '疾病进展',
    'PD': '疾病进展',
    'FDA': 'FDA',
    'FDA clearance': 'FDA批准',
    'FDA approval': 'FDA批准',
    'phase 1': 'I期',
    'phase 2': 'II期',
    'phase 3': 'III期',
    'phase I': 'I期',
    'phase II': 'II期',
    'phase III': 'III期',
    'first-in-human': '首次人体试验',
    'FIH': '首次人体试验',
    'dose escalation': '剂量递增',
    'dose-response': '剂量-效应',
    'hypofractionation': '大分割',
    'conventional fractionation': '常规分割',
    'ultra-hypofractionation': '超大分割',
    'radiosurgery': '放射外科',
    'brachytherapy': '近距离放疗',
    'external beam': '外照射',
    'intensity modulation': '调强',
    'volumetric arc': '容积旋转',
    'image guidance': '图像引导',
    'online adaptive': '在线自适应',
    'offline adaptive': '离线自适应',
    'tumor': '肿瘤',
    'cancer': '癌',
    'oncology': '肿瘤学',
    'metastatic': '转移性',
    'locally advanced': '局部晚期',
    'early stage': '早期',
    'advanced': '晚期',
    'palliative': '姑息',
    'curative': '根治',
    'neoplasm': '肿瘤',
    'malignant': '恶性',
    'benign': '良性',
    'squamous cell carcinoma': '鳞状细胞癌',
    'adenocarcinoma': '腺癌',
    'neuroendocrine': '神经内分泌',
    'angiogenesis': '血管生成',
    'apoptosis': '凋亡',
    'proliferation': '增殖',
    'invasion': '侵袭',
    'epithelial-mesenchymal transition': '上皮间质转化',
    'EMT': '上皮间质转化',
    'tumor microenvironment': '肿瘤微环境',
    'TME': '肿瘤微环境',
    'immune checkpoint': '免疫检查点',
    'T cell': 'T细胞',
    'CD8': 'CD8',
    'NK cell': 'NK细胞',
    'macrophage': '巨噬细胞',
    'cytokine': '细胞因子',
    'interferon': '干扰素',
    'interleukin': '白介素',
    'radiation induced': '放射诱导',
    'radiation injury': '放射损伤',
    'radiation necrosis': '放射性坏死',
    'fibrosis': '纤维化',
    'edema': '水肿',
    'inflammation': '炎症',
    'DNA damage': 'DNA损伤',
    'DNA repair': 'DNA修复',
    'oxidative stress': '氧化应激',
    'reactive oxygen species': '活性氧',
    'ROS': '活性氧',
    'hypoxia': '乏氧',
    'reoxygenation': '再氧合',
    'cell cycle': '细胞周期',
    'radiosensitivity': '放射敏感性',
    'radioresistance': '放射抵抗',
    'dose painting': '剂量雕刻',
    'dose escalation': '剂量递增',
    'dose de-escalation': '剂量降阶梯',
    'target volume': '靶区',
    'margin': '外扩',
    'registration': '配准',
    'fusion': '融合',
    'contouring': '勾画',
    'delineation': '勾画',
    'auto-contouring': '自动勾画',
    'knowledge-based': '基于知识的',
    'model-based': '基于模型的',
    'data-driven': '数据驱动的',
    'end-to-end': '端到端',
    'real-time': '实时',
    'prediction': '预测',
    'classification': '分类',
    'detection': '检测',
    'recognition': '识别',
    'diagnosis': '诊断',
    'prognostic': '预后',
    'predictive': '预测性',
    'validation': '验证',
    'benchmark': '基准',
    'comparison': '对比',
    'evaluation': '评估',
    'assessment': '评估',
    'analysis': '分析',
    'outcomes': '结局',
    'results': '结果',
    'efficacy': '疗效',
    'safety': '安全性',
    'tolerability': '耐受性',
    'compliance': '依从性',
    'adherence': '依从性',
    'cost-effectiveness': '成本效益',
    'quality assurance': '质量保证',
    'QA': '质量保证',
    'quality control': '质量控制',
    'QC': '质量控制',
    'treatment plan': '治疗计划',
    'plan optimization': '计划优化',
    'inverse planning': '逆向计划',
    'forward planning': '正向计划',
    'fluence': '通量',
    'beam angle': '射束角度',
    'gantry angle': '机架角度',
    'collimator': '准直器',
    'MLC': '多叶准直器',
    'multi-leaf collimator': '多叶准直器',
}

# 常见标题模式翻译
TITLE_PATTERNS = [
    (r'^(.+?)\s*(?:in|for|of)\s+(.+?)$', r'\1在\2中的应用'),
    (r'^(.+?)\s*:\s*(.+)$', r'\1：\2'),
    (r'^A\s+(.+?)$', r'一种\1'),
    (r'^An?\s+(.+?)\s+(?:study|analysis|review|investigation|evaluation)$', r'\1研究'),
    (r'^(.+?)\s+(?:based on|using|via|with)\s+(.+)$', r'基于\2的\1'),
]


def translate_terms(text: str) -> str:
    """翻译常见术语"""
    result = text
    # 按长度排序，先替换长的
    sorted_terms = sorted(TERM_MAP.items(), key=lambda x: len(x[0]), reverse=True)
    for en, zh in sorted_terms:
        # 大小写不敏感替换
        pattern = re.compile(re.escape(en), re.IGNORECASE)
        result = pattern.sub(zh, result)
    return result


def generate_chinese_title(title: str, source_type: str) -> str:
    """生成中文标题"""
    if not title:
        return '未知标题'
    
    # 检查是否已经有中文
    if any('\u4e00' <= c <= '\u9fff' for c in title):
        return title
    
    # 翻译术语
    zh_title = translate_terms(title)
    
    # 如果翻译后还是大部分英文，尝试模式匹配
    chinese_ratio = sum(1 for c in zh_title if '\u4e00' <= c <= '\u9fff') / max(len(zh_title), 1)
    if chinese_ratio < 0.1:
        # 尝试模式匹配
        for pattern, replacement in TITLE_PATTERNS:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    zh_title = replacement.format(*groups)
                    zh_title = translate_terms(zh_title)
                    break
                except:
                    pass
    
    return zh_title


def generate_chinese_summary(title: str, abstract: str, source_type: str) -> str:
    """生成中文摘要"""
    if not abstract:
        return ''
    
    # 检查是否已经有中文
    if any('\u4e00' <= c <= '\u9fff' for c in abstract[:100]):
        return abstract
    
    # 翻译术语
    zh_abstract = translate_terms(abstract)
    
    # 截取前200字
    if len(zh_abstract) > 200:
        zh_abstract = zh_abstract[:200] + '...'
    
    return zh_abstract


def generate_detailed_reason(title: str, abstract: str, source: str, journal: str, source_type: str) -> str:
    """生成详细的中文推荐理由"""
    text = (title + ' ' + abstract).lower()
    reasons = []
    
    # 1. 来源权威性
    top_journals = {
        'nature': 'Nature', 'lancet': 'Lancet', 'nejm': 'NEJM',
        'cell': 'Cell', 'science': 'Science', 'jco': 'JCO',
        'radiotherapy and oncology': 'Radiotherapy and Oncology',
        'ijrobp': 'IJROBP', 'green journal': 'Green Journal',
        'medical physics': 'Medical Physics', 'radiotherapy': 'Radiotherapy',
        'oncology': 'Oncology', 'nature medicine': 'Nature Medicine',
        'nature communications': 'Nature Communications',
        'lancet oncology': 'Lancet Oncology',
        'international journal of radiation oncology': 'IJROBP',
    }
    for keyword, journal_name in top_journals.items():
        if keyword in journal.lower() or keyword in source.lower():
            reasons.append(f'来自权威期刊 {journal_name}')
            break
    
    # 2. 研究类型
    if 'meta-analysis' in text or '荟萃分析' in text:
        reasons.append('荟萃分析，证据等级高')
    elif 'systematic review' in text or '系统综述' in text:
        reasons.append('系统综述，全面总结现有证据')
    elif 'randomized' in text or '随机' in text:
        reasons.append('随机对照研究，循证等级高')
    elif 'multicenter' in text or 'multi-center' in text or '多中心' in text:
        reasons.append('多中心研究，样本量大，结论可靠')
    elif 'retrospective' in text:
        reasons.append('回顾性研究')
    elif 'prospective' in text:
        reasons.append('前瞻性研究')
    elif 'review' in text:
        reasons.append('综述性文章')
    
    # 3. 热点方向
    hot_topics = []
    if any(kw in text for kw in ['deep learning', 'machine learning', 'artificial intelligence', 'ai', '人工智能', '深度学习']):
        hot_topics.append('AI/深度学习')
    if any(kw in text for kw in ['large language model', 'llm', '大语言模型', 'gpt', 'chatgpt']):
        hot_topics.append('大语言模型')
    if any(kw in text for kw in ['segmentation', 'auto-segmentation', '自动分割', '分割']):
        hot_topics.append('自动分割')
    if any(kw in text for kw in ['treatment planning', 'dose prediction', '治疗计划', '剂量预测']):
        hot_topics.append('治疗计划优化')
    if any(kw in text for kw in ['adaptive', '自适应']):
        hot_topics.append('自适应放疗')
    if any(kw in text for kw in ['flash', 'flash放疗']):
        hot_topics.append('FLASH放疗')
    if any(kw in text for kw in ['proton', 'carbon ion', '质子', '碳离子']):
        hot_topics.append('粒子治疗')
    if any(kw in text for kw in ['immunotherapy', 'immune', '免疫']):
        hot_topics.append('免疫治疗')
    if any(kw in text for kw in ['radiomics', '影像组学']):
        hot_topics.append('影像组学')
    if any(kw in text for kw in ['biomarker', '生物标志物']):
        hot_topics.append('生物标志物')
    if any(kw in text for kw in ['clinical trial', 'phase', '临床试验']):
        hot_topics.append('临床试验')
    if any(kw in text for kw in ['survival', 'outcome', '生存', '预后']):
        hot_topics.append('生存结局')
    if any(kw in text for kw in ['toxicity', 'adverse', 'side effect', '毒性', '不良反应']):
        hot_topics.append('毒副反应')
    if any(kw in text for kw in ['dose', 'dosimetric', '剂量']):
        hot_topics.append('剂量学')
    if any(kw in text for kw in ['image', 'imaging', 'mri', 'ct', 'pet', '影像']):
        hot_topics.append('影像技术')
    
    if hot_topics:
        reasons.append(f'涉及热点方向：{"、".join(hot_topics[:4])}')
    
    # 4. 癌种
    cancer_types = []
    cancer_map = {
        'head and neck': '头颈部肿瘤', 'nasopharyngeal': '鼻咽癌',
        'lung': '肺癌', 'breast': '乳腺癌', 'prostate': '前列腺癌',
        'cervical': '宫颈癌', 'esophageal': '食管癌', 'liver': '肝癌',
        'hepatocellular': '肝细胞癌', 'glioblastoma': '胶质母细胞瘤',
        'rectal': '直肠癌', 'colorectal': '结直肠癌', 'pancreatic': '胰腺癌',
        'bladder': '膀胱癌', 'kidney': '肾癌', 'lymphoma': '淋巴瘤',
        'melanoma': '黑色素瘤', 'sarcoma': '肉瘤', 'thyroid': '甲状腺癌',
        'oral': '口腔癌', 'oropharyngeal': '口咽癌', 'laryngeal': '喉癌',
        'gastric': '胃癌', 'ovarian': '卵巢癌', 'endometrial': '子宫内膜癌',
    }
    for kw, cancer in cancer_map.items():
        if kw in text and cancer not in cancer_types:
            cancer_types.append(cancer)
    if cancer_types:
        reasons.append(f'针对{"、".join(cancer_types[:2])}')
    
    # 5. 技术亮点
    tech_highlights = []
    if any(kw in text for kw in ['novel', 'new', 'first', '创新', '首次', '新型']):
        tech_highlights.append('具有创新性')
    if any(kw in text for kw in ['real-time', '实时']):
        tech_highlights.append('实时技术')
    if any(kw in text for kw in ['automated', 'automatic', '自动']):
        tech_highlights.append('自动化流程')
    if any(kw in text for kw in ['validation', 'validated', '验证']):
        tech_highlights.append('经过验证')
    if any(kw in text for kw in ['benchmark', '基准']):
        tech_highlights.append('提供基准评估')
    if tech_highlights:
        reasons.append('、'.join(tech_highlights))
    
    # 6. 临床意义
    if any(kw in text for kw in ['significant', 'improved', 'better', 'superior', '显著', '改善', '优于']):
        reasons.append('显示显著临床获益')
    if any(kw in text for kw in ['survival', 'overall survival', '生存']):
        reasons.append('关注生存获益')
    if any(kw in text for kw in ['quality of life', '生活质量']):
        reasons.append('关注生活质量')
    
    # 组装推荐理由
    if reasons:
        return '；'.join(reasons) + '。'
    else:
        return f'来自{source}的放射治疗领域研究。'


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
        
        # 1. 翻译标题
        zh_title = generate_chinese_title(title, stype)
        
        # 2. 翻译摘要
        zh_summary = generate_chinese_summary(title, summary or content or '', stype)
        
        # 3. 生成详细推荐理由
        reason = generate_detailed_reason(title, content or summary or '', source, journal, stype)
        ai['recommendation_reason'] = reason
        
        # 4. 重新计算评分
        score = 70
        text = (title + ' ' + (content or '')).lower()
        
        # 权威期刊加分
        top_j = ['nature', 'lancet', 'nejm', 'cell', 'science', 'jco',
                 'radiotherapy and oncology', 'ijrobp', 'medical physics']
        if any(j in journal.lower() or j in source.lower() for j in top_j):
            score += 15
        
        # 热点方向加分
        hot_count = 0
        for kw in ['deep learning', 'ai', 'machine learning', 'large language model',
                    'segmentation', 'treatment planning', 'adaptive', 'flash',
                    'proton', 'immunotherapy', 'clinical trial', 'radiomics']:
            if kw in text:
                hot_count += 1
        score += min(hot_count * 3, 15)
        
        # 研究类型加分
        if any(kw in text for kw in ['meta-analysis', 'systematic review', 'randomized']):
            score += 10
        elif any(kw in text for kw in ['multicenter', 'multi-center']):
            score += 8
        
        score = min(score, 98)
        ai['score'] = score
        ai['is_featured'] = score >= 80
        
        # 更新数据库
        conn.execute(
            '''UPDATE content SET 
            title=?, summary=?, ai=?, updated_at=datetime('now')
            WHERE id=?''',
            (zh_title, zh_summary, json.dumps(ai, ensure_ascii=False), cid)
        )
        updated += 1
    
    conn.commit()
    conn.close()
    print(f'✅ 已更新 {updated} 条数据的中文标题、摘要和推荐理由')


if __name__ == '__main__':
    main()
