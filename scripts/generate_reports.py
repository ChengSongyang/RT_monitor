#!/usr/bin/env python3
"""
使用 MiMo API 为每篇论文生成深度解读报告
"""
import sqlite3
import json
import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

DB = 'data/rt_monitor.db'
API_BASE = os.environ.get('XIAOMI_BASE_URL', 'https://token-plan-cn.xiaomimimo.com/v1')
API_KEY = os.environ.get('XIAOMI_API_KEY', '')
MODEL = 'mimo-v2.5-pro'

REPORT_PROMPT = """你是一位在放射治疗领域拥有博士学位的资深研究员，正在对一篇学术论文进行深度审阅。你的任务是输出一份完整的**论文深度解读报告**。

请严格遵循以下结构和要求，保持批判性、建设性和学术严谨性：

## 解读报告结构

### 1. 核心信息速览
- **论文标题、作者、年份、出处**。
- **一句话核心贡献**：用一句话概括这篇论文到底为领域带来了什么新东西。
- **1-3 个关键词**：你认为最能代表本文研究内核的关键词。

### 2. 动机与问题定义
- 本文试图解决什么**根本问题**？这个问题为什么重要？
- 现有工作（SOTA）在解决该问题上的**主要瓶颈或盲区**是什么？作者是如何论证这一缺口的？
- 本文的**研究假设**和**范围限定**是什么？有没有隐含的前提条件？

### 3. 方法与技术路线（最重要的批判部分）
- 用通俗易懂的"黑话翻译"和清晰的逻辑流，分步骤解释**核心方法**（如果涉及公式，解释其直觉含义，不要只罗列符号）。
- **创新机制**：方法中哪一部分是真正的首创？与现有方法相比，最本质的区别是什么？请用对比的方式说清。
- **范式归类**：该方法在宏观上属于哪一类技术路线（如"基于XX的XX范式"），它颠覆了旧范式还是在旧范式上做了关键改进？

### 4. 实验论证与合理性检验
- **实验设计逻辑**：作者是如何证明自己方法的有效性、鲁棒性和可解释性的？实验回答了几个层次的问题（性能、消融、可视化、案例研究等）？
- **关键结果复述**：最重要的1-2个实验结论是什么？请不要堆砌数字，而是说清"这个数字说明什么"。
- **对标与公平性**：对比的基线方法是否足够强且合理？有无占优嫌疑？评估指标是否真正反映了问题本质？

### 5. 贡献与价值评价
- **显性贡献**：论文自己声称的贡献有哪些？
- **隐性贡献**：有没有作者没明说但你认为很有价值的启发？例如一个巧妙的工程技巧、一种失败思路的排除、一个有趣的数据洞察。
- **思想的可迁移性**：该方法或思想，能否迁移到别的问题、别的数据、别的场景中？代价是什么？

### 6. 局限性与深度批判（博士思维的核心）
- **内在局限性**：方法的哪些设计是被问题"逼"出来的妥协？其成功是否过度依赖特定数据特性或任务设置？
- **实验与声明的不匹配**：实验结论是否完全支撑了作者的宣称？有没有被淡化的负面结果或未经检验的边界条件？
- **理论或逻辑缺陷**：有没有循环论证、概念偷换、不合理的简化假设？
- **如果你来做**：如果给你同等的计算资源和数据，你会选择保留什么、推翻什么？会设计一个什么实验来彻底击溃或证实本文的核心论断？

---

**论文信息：**
标题：{title}
来源：{source}
类型：{source_type}
发表日期：{date}
摘要/内容：
{content}

请用中文输出完整的深度解读报告。"""


def generate_single_report(item):
    """为单篇论文生成报告"""
    cid, title, summary, content, source, source_type, date, meta_json = item
    meta = json.loads(meta_json) if meta_json else {}
    journal = meta.get('journal', source)

    text = content or summary or ''
    if not text.strip():
        return cid, None, "No content available"

    prompt = REPORT_PROMPT.format(
        title=title,
        source=f"{source} ({journal})" if journal != source else source,
        source_type=source_type,
        date=date or '未知',
        content=text[:4000]  # 限制长度避免超token
    )

    try:
        resp = requests.post(
            f"{API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0.3
            },
            timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        report_text = data['choices'][0]['message']['content']
        return cid, report_text, None
    except Exception as e:
        return cid, None, str(e)


def main():
    conn = sqlite3.connect(DB, timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')

    # 获取所有内容
    rows = conn.execute(
        'SELECT id, title, summary, content, source, source_type, date, meta FROM content ORDER BY date DESC'
    ).fetchall()
    print(f"📊 共 {len(rows)} 条数据需要生成报告")

    # 检查哪些已有报告
    existing = set(r[0] for r in conn.execute('SELECT content_id FROM reports').fetchall())
    todo = [r for r in rows if r[0] not in existing]
    print(f"📝 已有报告: {len(existing)}, 待生成: {len(todo)}")

    if not todo:
        print("✅ 所有报告已存在")
        conn.close()
        return

    # 并发生成报告
    success = 0
    failed = 0
    batch_size = 5  # 并发数

    for i in range(0, len(todo), batch_size):
        batch = todo[i:i+batch_size]
        print(f"\n🔄 处理批次 {i//batch_size + 1}/{(len(todo)-1)//batch_size + 1} ({len(batch)} 篇)")

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = {executor.submit(generate_single_report, item): item for item in batch}
            for future in as_completed(futures):
                cid, report, error = future.result()
                if report:
                    # 保存报告
                    conn.execute(
                        '''INSERT OR REPLACE INTO reports (content_id, report_type, file_path, year, month, source, md_content)
                           VALUES (?, 'deep_analysis', ?, ?, ?, ?, ?)''',
                        (cid, f"reports/{cid}.md", 2026, 5, 'ai_generated', report)
                    )
                    conn.commit()
                    success += 1
                    title = futures[future][1][:50]
                    print(f"  ✅ {title}...")
                else:
                    failed += 1
                    title = futures[future][1][:50]
                    print(f"  ❌ {title}... 错误: {error[:80]}")

        # 避免API限流
        if i + batch_size < len(todo):
            time.sleep(1)

    conn.close()
    print(f"\n{'='*50}")
    print(f"✅ 成功: {success}")
    print(f"❌ 失败: {failed}")
    print(f"📊 总计: {len(rows)} 条数据")


if __name__ == '__main__':
    main()
