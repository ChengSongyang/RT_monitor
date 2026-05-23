-- ============================================================
-- 示例数据
-- 覆盖 content 表（各数据源）+ reports 表（AI 解读报告）
-- 导入: sqlite3 data/rt_monitor.db < data/seed.sql
-- ============================================================
-- content 表字段说明：
--   flat columns: id, title, summary, content, url, source,
--                 source_type, source_user, source_verified,
--                 source_verified_reason, date, timestamp, category
--   JSON columns (存为字符串):
--     tags   - 标签数组, 如 '["论文","arXiv"]'
--     images - 图片URL数组
--     meta   - 论文/新闻元数据 (journal, pdf_url, authors, doi,
--              report_path, report_type...)
--     ai     - AI推荐信息 (score, is_featured, recommendation_reason)
--     extra  - 扩展字段 (quoted_text, quoted_author)
--
-- reports 表字段说明：
--   id / content_id  - 关联 content.id
--   file_path        - 与 meta.report_path 一致
--   md_content       - Markdown 格式的解读正文
-- ============================================================

-- 1) arXiv 论文 - AI + 放疗
INSERT INTO content (id, title, summary, content, url, source, source_type, source_user, source_verified, source_verified_reason, date, timestamp, category, tags, images, meta, ai, extra) VALUES (
  'arxiv_2405.12345',
  'Deep Learning-Based Auto-Segmentation of Organs at Risk in Head and Neck Radiotherapy',
  'A novel U-Net architecture with attention gates for automatic segmentation of 12 OARs in head and neck CT images, achieving mean Dice coefficient of 0.91 across 5 medical centers...',
  'A novel U-Net architecture with attention gates for automatic segmentation of 12 organs at risk (OARs) in head and neck CT images. The model was trained on 1,200 cases from 5 medical centers and validated on an external cohort of 200 cases. Mean Dice coefficient of 0.91 across all OARs, with 85% reduction in contouring time compared to manual delineation.',
  'https://arxiv.org/abs/2405.12345',
  'arXiv',
  'paper',
  'Wang X, Li Y, Zhang Z, Chen M, Liu H',
  1,
  '学术论文',
  '2024-05-20',
  1716172800.0,
  'paper',
  '["论文","arXiv","OAR","分割","U-Net"]',
  '[]',
  '{"authors":"Wang X, Li Y, Zhang Z, Chen M, Liu H","journal":"arXiv","pdf_url":"https://arxiv.org/pdf/2405.12345","html_url":"https://arxiv.org/html/2405.12345","doi":"","report_path":"reports/2024/05/arxiv/arxiv_2405.12345","report_type":"detailed"}',
  '{"score":85,"is_featured":true,"recommendation_reason":"多中心验证的OAR自动分割，Dice达0.91，临床实用性强，可显著缩短放疗计划时间。"}',
  '{}'
);

-- 2) PubMed 论文 - 剂量学对比
INSERT INTO content (id, title, summary, content, url, source, source_type, source_user, source_verified, source_verified_reason, date, timestamp, category, tags, images, meta, ai, extra) VALUES (
  'pubmed_39876543',
  'Dosimetric comparison of VMAT vs IMRT for locally advanced nasopharyngeal carcinoma: a meta-analysis',
  'Meta-analysis of 12 studies (892 patients) comparing VMAT and IMRT for nasopharyngeal carcinoma. VMAT reduced treatment time by 42% with equivalent target coverage and OAR sparing...',
  'Objective: To compare dosimetric parameters between VMAT and IMRT for locally advanced nasopharyngeal carcinoma (NPC). Methods: Meta-analysis of 12 comparative studies involving 892 patients. Results: VMAT significantly reduced treatment time (WMD -6.8 min, P<0.001) while maintaining equivalent PTV coverage (D95: WMD 0.3 Gy, P=0.42) and comparable OAR doses. VMAT showed lower Dmax to brainstem (WMD -1.2 Gy, P=0.03) and spinal cord (WMD -0.8 Gy, P=0.02).',
  'https://pubmed.ncbi.nlm.nih.gov/39876543/',
  'Radiotherapy and Oncology',
  'paper',
  'Zhang W, Liu J, Chen K, Wang L, Huang P',
  1,
  '学术论文',
  '2024-05-18',
  1715999900.0,
  'paper',
  '["论文","PubMed","VMAT","IMRT","鼻咽癌","Meta分析"]',
  '[]',
  '{"authors":"Zhang W, Liu J, Chen K, Wang L, Huang P","journal":"Radiotherapy and Oncology","pdf_url":"https://doi.org/10.1016/j.radonc.2024.05.012","html_url":"","doi":"10.1016/j.radonc.2024.05.012","citation_count":0,"report_path":"reports/2024/05/radiotherapy_and_oncology/pubmed_39876543","report_type":"detailed"}',
  '{"score":92,"is_featured":true,"recommendation_reason":"12项研究的Meta分析，VMAT在鼻咽癌中治疗时间缩短42%且剂量学不劣于IMRT，对临床方案选择有直接指导意义。"}',
  '{"quoted_text":"VMAT组的平均治疗时间缩短了42%，而靶区覆盖和危及器官保护无统计学差异","quoted_author":"Zhang W"}'
);

-- 3) Google News - 行业动态
INSERT INTO content (id, title, summary, content, url, source, source_type, source_user, source_verified, source_verified_reason, date, timestamp, category, tags, images, meta, ai, extra) VALUES (
  'google_news_varian_truebeam_2026',
  'Varian Medical 推出新一代TrueBeam系统，升级版影像引导功能提升治疗精度',
  'Varian今日宣布TrueBeam系统重大升级，集成全新锥形束CT重建算法，软组织对比度提升约30%...',
  'Varian Medical Systems今日宣布推出TrueBeam系统重大升级版本。新版系统集成了全新的锥形束CT（CBCT）重建算法，基于深度学习的去噪技术使软组织对比度提升约30%。同时新增4D-CT引导功能，可实时追踪呼吸运动。预计今年第三季度在北美率先上市，中国市场紧随其后。',
  'https://news.example.com/varian-truebeam-2026',
  '医脉通',
  'news',
  '李医生',
  0,
  '',
  '2026-05-24',
  1748095200.0,
  'industry_news',
  '["放射治疗","设备更新","Varian","TrueBeam"]',
  '[]',
  '{}',
  '{"score":72,"is_featured":false,"recommendation_reason":""}',
  '{}'
);

-- 4) Google News - 医保政策
INSERT INTO content (id, title, summary, content, url, source, source_type, source_user, source_verified, source_verified_reason, date, timestamp, category, tags, images, meta, ai, extra) VALUES (
  'google_news_insurance_policy_2026',
  '国家医保局：质子重离子治疗有望纳入2027年医保目录',
  '国家医疗保障局在新闻发布会上透露，已将质子重离子治疗纳入下一周期医保目录调整的优先评估范围...',
  '国家医疗保障局在今日新闻发布会上透露，已将质子重离子治疗纳入下一周期医保目录调整的优先评估范围。目前全国已有5家质子重离子治疗中心投入运营，单次治疗费用约27.8万元。若纳入医保，患者自付比例有望降至30%以下。预计2027年有望实现部分病种的医保覆盖。',
  'https://www.jkb.com.cn/example-insurance',
  '健康报',
  'news',
  '王记者',
  0,
  '',
  '2026-05-24',
  1748098800.0,
  'industry_news',
  '["放射治疗","医保政策","质子治疗","重离子"]',
  '[]',
  '{}',
  '{"score":88,"is_featured":true,"recommendation_reason":"质子重离子治疗费用一直是患者的主要负担，医保覆盖将大幅降低治疗门槛，对行业格局影响深远。"}',
  '{}'
);

-- 5) Semantic Scholar - 会议论文 (MICCAI)
INSERT INTO content (id, title, summary, content, url, source, source_type, source_user, source_verified, source_verified_reason, date, timestamp, category, tags, images, meta, ai, extra) VALUES (
  'semantic_scholar_miccai_2024_seg',
  'Self-Supervised 3D Medical Image Segmentation for Radiation Therapy Planning',
  'A self-supervised learning framework that achieves competitive performance with only 10% labeled data for 3D medical image segmentation in radiation therapy...',
  'We propose a self-supervised pre-training framework for 3D medical image segmentation tailored to radiation therapy planning. By combining contrastive learning with masked image modeling on unlabeled CT/MRI scans, our method achieves 94% of fully-supervised performance using only 10% labeled data. Evaluated on multi-organ and head & neck segmentation benchmarks.',
  'https://doi.org/10.1007/978-3-031-72364-1_15',
  'MICCAI',
  'paper',
  'Kim S, Park J, Lee H, Tanaka T',
  1,
  '学术论文',
  '2024-05-15',
  1715740800.0,
  'paper',
  '["论文","SemanticScholar","MICCAI","自监督学习","医学图像分割"]',
  '[]',
  '{"authors":"Kim S, Park J, Lee H, Tanaka T","journal":"MICCAI","pdf_url":"","html_url":"","doi":"10.1007/978-3-031-72364-1_15","citation_count":3}',
  '{"score":78,"is_featured":false,"recommendation_reason":""}',
  '{}'
);

-- 6) Google News - 学术会议报道 (带图片)
INSERT INTO content (id, title, summary, content, url, source, source_type, source_user, source_verified, source_verified_reason, date, timestamp, category, tags, images, meta, ai, extra) VALUES (
  'google_news_estro2026_sbrt',
  'ESTRO 2026｜大分割SBRT在寡转移中的3年生存率数据首次公布',
  'ESTRO 2026大会口头报告环节公布SABR-COMET-3试验3年随访结果：SBRT组总生存率73.2% vs 标准治疗组54.8%...',
  '在ESTRO 2026大会口头报告环节，来自荷兰阿姆斯特丹大学医学中心的van Tienhoven教授公布了SABR-COMET-3试验的3年随访结果。该试验纳入121例寡转移（1-5个转移灶）患者，随机分为SBRT组（n=61）和标准治疗组（n=60）。主要终点为3年总生存率。',
  'https://estro2026.org/abstract/sbrt-comet-3',
  'ESTRO 2026',
  'news',
  '李明',
  0,
  '',
  '2026-05-24',
  1748108400.0,
  'conference',
  '["学术会议","ESTRO","SBRT","寡转移","生存率"]',
  '["https://picsum.photos/seed/sbrt1/400/300","https://picsum.photos/seed/sbrt2/400/300","https://picsum.photos/seed/sbrt3/400/300"]',
  '{}',
  '{"score":96,"is_featured":true,"recommendation_reason":"改变实践的重磅数据，SBRT在寡转移中的生存获益首次在大规模RCT中得到证实，可能改变寡转移的标准治疗范式。"}',
  '{"quoted_text":"3年总生存率：SBRT组73.2% vs 标准治疗组54.8%，HR=0.58，P=0.002","quoted_author":"van Tienhoven"}'
);

-- 7) PubMed 论文 - FLASH放疗
INSERT INTO content (id, title, summary, content, url, source, source_type, source_user, source_verified, source_verified_reason, date, timestamp, category, tags, images, meta, ai, extra) VALUES (
  'pubmed_flash_heart_2024',
  'FLASH radiotherapy reduces cardiac toxicity in a murine model while maintaining anti-tumor efficacy',
  'Ultra-high dose rate (FLASH) irradiation significantly reduces cardiac toxicity in mice while preserving tumor control, mediated by reduced reactive oxygen species damage...',
  'Background: FLASH radiotherapy (ultra-high dose rate >40 Gy/s) has shown the potential to spare normal tissues while maintaining tumor control (FLASH effect). We investigated the cardiac protective effects of FLASH vs conventional radiotherapy in a mouse model. Methods: C57BL/6 mice (n=60) received cardiac irradiation (16 Gy) at either 10 Gy/s (FLASH) or 0.05 Gy/s (conventional). Results: FLASH irradiation reduced cardiac fibrosis by 60% (P<0.001), preserved ejection fraction (62% vs 48%, P=0.01), and reduced inflammatory markers. Tumor-bearing cohort showed equivalent tumor control (78% vs 82%, P=0.41).',
  'https://pubmed.ncbi.nlm.nih.gov/flash_heart_2024',
  'Nature Medicine',
  'paper',
  'Chen R, Mueller K, Loo BW, Timmerman R',
  1,
  '顶级期刊',
  '2026-05-23',
  1747983600.0,
  'paper',
  '["论文","PubMed","FLASH放疗","心脏毒性","Nature Medicine"]',
  '[]',
  '{"authors":"Chen R, Mueller K, Loo BW, Timmerman R","journal":"Nature Medicine","pdf_url":"https://doi.org/10.1038/nm.2024.0523","html_url":"","doi":"10.1038/nm.2024.0523","citation_count":0,"report_path":"reports/2026/05/nature_medicine/pubmed_flash_heart_2024","report_type":"detailed"}',
  '{"score":91,"is_featured":true,"recommendation_reason":"FLASH放疗从基础走向临床的关键一步，心脏保护机制的阐明对后续临床试验设计有重要指导意义。Nature Medicine级别，影响力大。"}',
  '{}'
);

-- 8) Google News - 设备更新 (简单新闻)
INSERT INTO content (id, title, summary, content, url, source, source_type, source_user, source_verified, source_verified_reason, date, timestamp, category, tags, images, meta, ai, extra) VALUES (
  'google_news_elekta_update_2026',
  'Elekta Unity磁共振引导放疗系统获FDA批准新适应症',
  'Elekta宣布Unity系统获FDA批准用于前列腺癌在线自适应放疗，成为首个获批该适应症的MR-linac系统...',
  'Elekta今日宣布其Unity磁共振引导放射治疗（MRgRT）系统获得美国FDA批准新适应症，可用于前列腺癌的在线自适应放射治疗（online adaptive RT）。这是首个获得前列腺癌在线自适应放疗适应症的MR-linac系统。临床试验显示，前列腺癌患者的3年无生化复发生存率达94%。',
  'https://news.example.com/elekta-unity-fda',
  'Medscape',
  'news',
  '赵主任',
  0,
  '',
  '2026-05-22',
  1747897200.0,
  'industry_news',
  '["放射治疗","设备更新","Elekta","MR-linac","FDA"]',
  '[]',
  '{}',
  '{"score":75,"is_featured":false,"recommendation_reason":""}',
  '{}'
);

-- 9) arXiv 论文 - 大语言模型 + 放疗
INSERT INTO content (id, title, summary, content, url, source, source_type, source_user, source_verified, source_verified_reason, date, timestamp, category, tags, images, meta, ai, extra) VALUES (
  'arxiv_llm_rt_decision_2024',
  'LLM-Assisted Clinical Decision Support for Radiation Therapy Prescription Generation',
  'We present an LLM-based clinical decision support system that generates radiation therapy prescriptions with 91% concordance with expert decisions...',
  'We present RadPlanGPT, an LLM-based clinical decision support system for radiation therapy prescription generation. Fine-tuned on 15,000 de-identified treatment plans from 3 academic medical centers, RadPlanGPT generates prescriptions with 91% concordance with expert decisions across 6 common cancer sites. The system provides rationale for dose selection and flags potential OAR constraint violations.',
  'https://arxiv.org/abs/2405.67890',
  'arXiv',
  'paper',
  'Li M, Patel S, Ratanatharaphorn V, Martinez A',
  1,
  '学术论文',
  '2024-05-21',
  1716259200.0,
  'paper',
  '["论文","arXiv","大语言模型","放疗计划","临床决策支持"]',
  '[]',
  '{"authors":"Li M, Patel S, Ratanatharaphorn V, Martinez A","journal":"arXiv","pdf_url":"https://arxiv.org/pdf/2405.67890","html_url":"https://arxiv.org/html/2405.67890","doi":"","report_path":"reports/2024/05/arxiv/arxiv_llm_rt_decision_2024","report_type":"detailed"}',
  '{"score":88,"is_featured":true,"recommendation_reason":"LLM在放疗计划中的首个大规模验证研究，91%的专家一致性说明临床可行性，对放疗AI应用方向有重要启示。"}',
  '{"quoted_text":"RadPlanGPT生成的处方与专家决策的一致性达到91%","quoted_author":"Li M"}'
);

-- 10) Semantic Scholar - CVPR 论文
INSERT INTO content (id, title, summary, content, url, source, source_type, source_user, source_verified, source_verified_reason, date, timestamp, category, tags, images, meta, ai, extra) VALUES (
  'semantic_scholar_cvpr_2024_diffusion',
  'Diffusion Models for Medical Image Synthesis in Radiation Therapy',
  'A conditional diffusion model that generates high-fidelity synthetic CT and MRI pairs for radiotherapy treatment planning data augmentation...',
  'We propose MedDiffusion, a conditional diffusion model for generating synthetic medical image pairs (CT-MRI) for radiotherapy treatment planning. Trained on 8,000 paired scans, MedDiffusion generates images with FID score of 12.3 (vs 45.7 for GANs). Downstream segmentation models trained with augmented data show 8-15% Dice improvement on rare tumor types.',
  'https://doi.org/10.1109/CVPR52729.2024.00635',
  'CVPR',
  'paper',
  'Zhao Q, Yang X, Chen J, Frazer C',
  1,
  '学术论文',
  '2024-05-19',
  1716086400.0,
  'paper',
  '["论文","SemanticScholar","CVPR","扩散模型","数据增强","医学图像合成"]',
  '[]',
  '{"authors":"Zhao Q, Yang X, Chen J, Frazer C","journal":"CVPR","pdf_url":"","html_url":"","doi":"10.1109/CVPR52729.2024.00635","citation_count":5}',
  '{"score":80,"is_featured":false,"recommendation_reason":""}',
  '{}'
);


-- ============================================================
-- reports 表 - AI 生成的解读报告
-- ============================================================
-- 每条 report 通过 content_id 关联 content 表
-- content 表中 meta.report_path 指向路由路径
-- API: GET /api/reports/{content_id} → 返回 reports 表中的 md_content
-- 前端: /reports/{year}/{month}/{source}/{id} → react-markdown 渲染
-- ============================================================

-- 1) OAR 自动分割 - 解读报告
INSERT INTO reports (id, content_id, report_type, file_path, year, month, source, md_content) VALUES (
  'arxiv_2405.12345',
  'arxiv_2405.12345',
  'ai_analysis',
  'reports/2024/05/arxiv/arxiv_2405.12345',
  2024, 5, 'arxiv',
  '# 头颈部放疗 OAR 自动分割：多中心深度学习模型解读

## 研究背景

头颈部放疗危及器官（OAR）勾画是计划制定中最耗时的环节之一，单例需 1-2 小时。
本研究提出一种带注意力门控的 U-Net 架构，在 5 个医疗中心的 1200 例数据上训练，
实现 12 个 OAR 的自动分割。

## 核心结果

### 分割精度（Dice 系数）

| OAR | Dice (均值) | 95% CI |
|-----|-----------|--------|
| 脑干 | 0.93 | 0.91-0.95 |
| 脊髓 | 0.91 | 0.89-0.93 |
| 左腮腺 | 0.89 | 0.86-0.92 |
| 右腮腺 | 0.88 | 0.85-0.91 |
| 左颌下腺 | 0.85 | 0.82-0.88 |
| 咽缩肌 | 0.82 | 0.78-0.86 |
| **整体均值** | **0.91** | - |

### 效率提升
- 自动勾画 vs 手动勾画：**时间缩短 85%**（从 90 分钟降至 14 分钟）
- 物理师仅需微调，平均修正时间 8 分钟

## 模型架构

```
输入 CT → Encoder (ResNet-34) → Attention Gate → Decoder → 12 OAR Mask
              ↓                      ↑
         多尺度特征              跳跃连接 + 注意力权重
```

关键创新：注意力门控机制自动聚焦于 OAR 边界区域，减少背景干扰。

## 临床价值

1. **效率革命**：将 OAR 勾画从 1-2 小时缩短至 15 分钟
2. **一致性提升**：消除不同物理师间的勾画差异
3. **多中心验证**：跨 5 个中心的泛化能力已证实

## 局限性

- 咽缩肌等小器官 Dice 仍偏低（0.82），需人工复核
- 未纳入放疗后复发患者的变形解剖
- 仅支持 CT 模态，MRI/CT 融合场景未验证

> **推荐理由：** 多中心验证的 OAR 自动分割模型，Dice 达 0.91，临床实用性强，
> 可显著缩短放疗计划时间，对科室数字化转型有直接推动作用。'
);

-- 2) VMAT vs IMRT Meta分析 - 解读报告
INSERT INTO reports (id, content_id, report_type, file_path, year, month, source, md_content) VALUES (
  'pubmed_39876543',
  'pubmed_39876543',
  'ai_analysis',
  'reports/2024/05/radiotherapy_and_oncology/pubmed_39876543',
  2024, 5, 'radiotherapy_and_oncology',
  '# VMAT vs IMRT 在鼻咽癌中的剂量学对比：Meta分析解读

## 研究背景

调强放疗（IMRT）是局部晚期鼻咽癌的标准放疗技术。容积旋转调强放疗（VMAT）作为
新一代技术，理论上可缩短治疗时间，但与IMRT的剂量学优劣尚存争议。

## 核心发现

### 1. 治疗效率
- **VMAT治疗时间平均缩短42%**（WMD -6.8 min，P<0.001）
- 单次治疗从约12分钟降至约7分钟

### 2. 靶区覆盖
- PTV D95无统计学差异（WMD 0.3 Gy，P=0.42）
- 两种技术均能满足处方剂量要求

### 3. 危及器官保护
| 器官 | VMAT vs IMRT | P值 |
|------|-------------|-----|
| 脑干 Dmax | -1.2 Gy | 0.03 |
| 脊髓 Dmax | -0.8 Gy | 0.02 |
| 腮腺 Dmean | 无显著差异 | 0.18 |

## 临床意义

1. **优先选择VMAT**：在保证剂量学等效的前提下，显著缩短治疗时间
2. **患者舒适度提升**：治疗时间缩短意味着体位固定相关误差减少
3. **设备周转率提高**：单位时间可治疗更多患者

## 局限性

- 纳入研究以回顾性为主，缺乏前瞻性RCT证据
- 不同中心的处方剂量和计划优化策略存在差异
- 未评估远期生存和毒性结局

> **推荐理由：** 该Meta分析为VMAT在鼻咽癌中的应用提供了高质量剂量学证据，
> 对放疗科主任在设备采购和方案选择中有直接参考价值。'
);

-- 2) FLASH放疗心脏保护 - 解读报告
INSERT INTO reports (id, content_id, report_type, file_path, year, month, source, md_content) VALUES (
  'pubmed_flash_heart_2024',
  'pubmed_flash_heart_2024',
  'ai_analysis',
  'reports/2026/05/nature_medicine/pubmed_flash_heart_2024',
  2026, 5, 'nature_medicine',
  '# FLASH放疗心脏保护效应解读

## 研究背景

FLASH放疗（超高剂量率 >40 Gy/s）是放射治疗领域的前沿方向。此前已有研究显示
FLASH可减少皮肤、肺等正常组织损伤，但心脏保护效应尚属首次系统性研究。

## 核心发现

### 心脏保护指标
| 指标 | FLASH组 | 常规组 | P值 |
|------|---------|--------|-----|
| 心脏纤维化面积 | 12% | 30% | <0.001 |
| 射血分数（3个月） | 62% | 48% | 0.01 |
| 炎症因子IL-6 | 显著降低 | - | 0.008 |

### 肿瘤控制
- FLASH组肿瘤控制率：78%
- 常规组肿瘤控制率：82%
- **差异无统计学意义（P=0.41）**

## 机制假说

FLASH的心脏保护效应主要通过以下机制实现：

1. **氧消耗假说**：超高剂量率下，脉冲间歇不足以恢复氧浓度，导致自由基
   产生减少
2. **ROS减少**：FLASH照射产生的活性氧（ROS）显著低于常规照射
3. **微血管保护**：FLASH对心脏微血管内皮细胞的损伤更小

## 临床转化展望

1. **心脏毒性高风险患者**：左乳放疗、纵隔淋巴瘤放疗患者可能优先受益
2. **设备发展**：需要专用FLASH加速器或电子线FLASH设备
3. **临床试验**：预计2-3年内将有首批心脏保护相关的FLASH临床试验启动

## 局限性

- 小鼠模型与人体存在差异，心脏解剖和放疗敏感性不同
- FLASH效应的剂量率阈值尚不明确
- 长期心脏安全性数据（>1年）缺失

> **推荐理由：** Nature Medicine级别研究，首次系统证明FLASH的心脏保护效应，
> 对放疗设备发展方向和高风险患者治疗策略有重要启示。'
);

-- 3) LLM辅助放疗计划 - 解读报告
INSERT INTO reports (id, content_id, report_type, file_path, year, month, source, md_content) VALUES (
  'arxiv_llm_rt_decision_2024',
  'arxiv_llm_rt_decision_2024',
  'ai_analysis',
  'reports/2024/05/arxiv/arxiv_llm_rt_decision_2024',
  2024, 5, 'arxiv',
  '# LLM辅助放疗处方生成：RadPlanGPT 解读

## 研究背景

放疗计划的制定依赖物理师和医生的经验，耗时且存在中心间差异。本研究探索
利用大语言模型（LLM）辅助生成放疗处方，以提高计划效率和一致性。

## RadPlanGPT 架构

```
患者信息 → [结构化输入] → Fine-tuned LLM → [处方输出]
   │                          │                    │
   ├─ 诊断/分期               ├─ 15,000例训练      ├─ 靶区剂量
   ├─ 影像特征                ├─ 3个学术中心       ├─ 分割方案
   └─ 既往治疗                └─ 6个癌种          └─ OAR约束
```

## 核心结果

### 整体一致性
- **91%的处方与专家决策一致**（6个癌种综合）
- 一致性最高：乳腺癌（95%）、前列腺癌（93%）
- 一致性较低：头颈部（86%，因解剖复杂）

### 各癌种表现
| 癌种 | 一致性 | 样本数 |
|------|--------|--------|
| 乳腺 | 95% | 420 |
| 前列腺 | 93% | 380 |
| 肺 | 91% | 350 |
| 直肠 | 89% | 280 |
| 宫颈 | 88% | 250 |
| 头颈 | 86% | 320 |

### OAR约束违规检测
- RadPlanGPT自动检测出12例潜在OAR约束违规
- 其中8例经物理师复核确认为真阳性（敏感性67%）

## 临床价值

1. **初稿生成**：为物理师提供计划初稿，减少从零开始的时间
2. **质控辅助**：自动检测OAR约束违规，作为二级审核工具
3. **教学培训**：为住院医师提供标准化的处方参考

## 局限性

- 仅覆盖6个常见癌种，罕见肿瘤未验证
- 训练数据来自3个北美中心，中国放疗实践可能存在差异
- 未与实际计划系统集成，端到端验证缺失

> **推荐理由：** LLM在放疗计划中的首个大规模验证研究，91%的专家一致性
> 说明临床可行性。对放疗AI应用方向和科室数字化转型有重要参考价值。'
);
