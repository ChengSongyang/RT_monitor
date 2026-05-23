# Data 文件夹说明

## 文件结构

```
data/
├── seed.sql          # 示例数据（INSERT 语句，可直接导入 db）
├── news.json         # 旧格式新闻数据（已迁移，可忽略）
├── papers.json       # 旧格式论文数据（已迁移，可忽略）
└── rt_monitor.db     # SQLite 数据库（数据源）
```

## 数据架构

所有内容数据统一存储在 `rt_monitor.db` 的 `content` 表中。前端通过 API 读取，`db.py` 负责字段映射。

### content 表结构

```sql
CREATE TABLE content (
  id TEXT PRIMARY KEY,           -- 唯一标识
  title TEXT NOT NULL,           -- 标题
  summary TEXT DEFAULT '',       -- 摘要（卡片显示，最多3行）
  content TEXT DEFAULT '',       -- 完整正文
  url TEXT DEFAULT '',           -- 原文链接

  source TEXT DEFAULT '',        -- 来源名称（PubMed、arXiv、医脉通...）
  source_type TEXT DEFAULT 'news',  -- 来源类型：paper / news
  source_user TEXT DEFAULT '',   -- 作者/用户
  source_verified INTEGER DEFAULT 0, -- 来源是否认证
  source_verified_reason TEXT DEFAULT '', -- 认证原因

  date TEXT DEFAULT '',          -- 发布日期 YYYY-MM-DD
  timestamp REAL DEFAULT 0,     -- Unix 时间戳（秒）

  category TEXT DEFAULT 'industry_news', -- 分类
  tags TEXT DEFAULT '[]',       -- 标签 JSON 数组
  images TEXT DEFAULT '[]',     -- 图片 URL JSON 数组

  meta TEXT DEFAULT '{}',       -- 元数据 JSON（见下方）
  ai TEXT DEFAULT '{}',         -- AI 推荐信息 JSON（见下方）
  extra TEXT DEFAULT '{}',      -- 扩展字段 JSON（见下方）

  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
```

### reports 表结构

解读报告独立存储在 `reports` 表中，通过 `content_id` 关联 `content` 表。

```sql
CREATE TABLE reports (
  id TEXT PRIMARY KEY,
  content_id TEXT NOT NULL,        -- 关联 content.id
  report_type TEXT DEFAULT 'ai_analysis',  -- 报告类型
  file_path TEXT NOT NULL,         -- 路由路径，如 reports/2024/05/pubmed/xxx
  year INTEGER,
  month INTEGER,
  source TEXT,
  md_content TEXT DEFAULT '',      -- Markdown 正文（前端 react-markdown 渲染）
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (content_id) REFERENCES content(id)
);
```

**数据链路：**

```
content 表
  ├─ meta.report_path = "reports/2024/05/pubmed/xxx"
  │     ↓ 前端 NewsCard 解析
  │   链接到 /reports/2024/05/pubmed/{content_id}
  │     ↓ 页面组件
  │   fetch /api/reports/{content_id}
  │     ↓ API
  │   db.get_report(content_id) → reports 表
  │     ↓
  │   返回 md_content → react-markdown 渲染
  └─ meta.report_path 为空时，不显示"查看解读"链接
```

### JSON 字段详情

#### `meta` — 内容元数据

```json
{
  "authors": "Zhang W, Liu J",    // 论文作者
  "journal": "Nature Medicine",   // 期刊/会议名
  "pdf_url": "https://...",       // PDF 链接
  "html_url": "https://...",      // HTML 全文链接
  "doi": "10.1038/xxx",          // DOI
  "citation_count": 12,          // 引用次数
  "report_path": "reports/2026/05/pubmed_xxx", // AI 解读报告路径
  "report_type": "detailed"      // 报告类型
}
```

#### `ai` — AI 推荐信息

```json
{
  "score": 92,                    // 推荐分 0-100，卡片右侧显示
  "is_featured": true,            // 是否精选
  "recommendation_reason": "..."  // 推荐理由文字
}
```

#### `extra` — 扩展字段

```json
{
  "quoted_text": "...",           // 引用文字，显示为引用块
  "quoted_author": "Zhang W"      // 引用作者
}
```

### API 字段映射

`db.py` 的 `query_content()` 函数将数据库字段映射为前端使用的字段：

| 数据库字段 | 前端字段 | 说明 |
|-----------|---------|------|
| `ai.score` | `recommendation_score` | 推荐分 |
| `ai.is_featured` | `is_featured` | 精选标记 |
| `ai.recommendation_reason` | `recommendation_reason` | 推荐理由 |
| `extra.quoted_text` | `quoted_text` | 引用文字 |
| `extra.quoted_author` | `quoted_author` | 引用作者 |
| `meta.journal` | `journal` | 期刊名 |
| `meta.pdf_url` | `pdf_url` | PDF 链接 |
| `meta.html_url` | `html_url` | HTML 链接 |
| `meta.report_path` | `report_path` | 报告路径 |
| `images` | `image_urls` | 图片数组（前端用此字段名） |

## 如何添加新数据

### 方式一：SQL 直接导入（推荐）

参考 `seed.sql`，编写 INSERT 语句直接插入 `content` 表：

```sql
INSERT INTO content (id, title, summary, content, url, source, source_type,
  source_user, source_verified, source_verified_reason, date, timestamp,
  category, tags, images, meta, ai, extra)
VALUES (
  'pubmed_12345678',                              -- id: {来源}_{原始ID}
  '论文标题',                                       -- title
  '摘要，卡片上最多显示3行',                         -- summary
  '完整正文内容...',                                 -- content
  'https://pubmed.ncbi.nlm.nih.gov/12345678/',     -- url
  'PubMed',                                        -- source
  'paper',                                         -- source_type: paper 或 news
  'Wang X, Li Y',                                  -- source_user
  1,                                               -- source_verified: 1=认证 0=未认证
  '学术论文',                                        -- source_verified_reason
  '2026-05-24',                                     -- date: YYYY-MM-DD
  1748110200.0,                                     -- timestamp: Unix秒
  'paper',                                         -- category
  '["论文","PubMed","放疗"]',                        -- tags: JSON数组
  '[]',                                            -- images: JSON数组
  '{"authors":"Wang X, Li Y","journal":"Nature Medicine","pdf_url":"","html_url":"","doi":""}',  -- meta
  '{"score":85,"is_featured":true,"recommendation_reason":"该研究对临床实践有重要参考价值。"}',   -- ai
  '{"quoted_text":"关键发现的一句话引用","quoted_author":"Wang X"}'  -- extra
);
```

执行导入：

```bash
sqlite3 data/rt_monitor.db < data/seed.sql
```

### 方式二：带解读报告的论文

论文类内容可附带 AI 生成的解读报告，需要同时写入 `content` 和 `reports` 两张表。

**Step 1: 写入 content，meta 中填入 report_path**

```sql
INSERT INTO content (..., meta, ...) VALUES (
  ...,
  '{"authors":"...","journal":"...","report_path":"reports/2024/05/pubmed/xxx","report_type":"detailed"}',
  ...
);
```

`report_path` 格式：`reports/{year}/{month}/{source}/{content_id}`

**Step 2: 写入 reports，md_content 填 Markdown 正文**

```sql
INSERT INTO reports (id, content_id, report_type, file_path, year, month, source, md_content) VALUES (
  'xxx',                                      -- id，一般与 content_id 相同
  'xxx',                                      -- content_id，关联 content.id
  'ai_analysis',                              -- report_type
  'reports/2024/05/pubmed/xxx',               -- file_path，与 meta.report_path 一致
  2024, 5, 'pubmed',                          -- year, month, source
  '# 论文标题\n\n## 研究背景\n\n...'            -- md_content，完整的 Markdown
);
```

**前端渲染路径：** NewsCard 检测到 `meta.report_path` 非空 → 显示"查看解读 →"链接 →
点击跳转 `/reports/{year}/{month}/{source}/{id}` → 页面 fetch `/api/reports/{content_id}` →
react-markdown 渲染 `md_content`。

### 方式三：通过采集脚本

运行数据采集脚本会自动调用 `upsert_content()` 写入数据库：

```bash
python scripts/collect.py          # 采集所有数据源
python scripts/collect.py --days 3 # 只采集最近3天
```

## 数据源类型

| source_type | source 值 | 典型 category |
|-------------|-----------|--------------|
| `paper` | arXiv, PubMed, IJROBP, MICCAI, CVPR, SemanticScholar | `paper` |
| `news` | Google News, 医脉通, 健康报, Medscape | `industry_news`, `conference` |

## category 枚举值

| 值 | 中文标签 | 前端 Badge 颜色 |
|----|---------|----------------|
| `paper` | 论文 | 蓝色 |
| `industry_news` | 行业动态 | 绿色 |
| `guideline` | 指南共识 | 紫色 |
| `research` | 研究进展 | 橙色 |
| `conference` | 学术会议 | 粉色 |
| `case_report` | 病例报告 | 灰色 |
| `discussion` | 讨论 | 灰色 |

## 注意事项

- `id` 必须全局唯一，建议用 `{source}_{原始ID}` 格式
- `timestamp` 是 Unix **秒**级时间戳，不是毫秒
- `tags` 和 `images` 存的是 JSON 字符串，不是数组
- `source_verified` 在数据库中是 INTEGER（0/1），读取后自动转为 boolean
- `images` 最多显示4张缩略图，多余的在图上显示 "+N"
- `ai.score` 为 0 时不显示推荐分 Badge
- 新增数据源时需要在 `scripts/sources/` 下添加对应的采集器
