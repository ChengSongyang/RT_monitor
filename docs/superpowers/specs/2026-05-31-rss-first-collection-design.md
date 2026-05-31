# RSS-first 采集与订阅源页面设计

## 背景

当前采集链路主要由手动刷新触发后端 `collect.py`，再调用论文 API、静态指南入口、厂商/行业搜索等采集器。这个模式对新内容发现偏被动，且搜索兜底承担了过多主采集职责，容易带来噪声、重复和成本问题。

第一期目标是把论文采集改成 RSS-first，并在界面导航中提供只读的 RSS 订阅源页面，方便查看订阅源和同步状态。

## 范围

第一期只接入三个确认可用的 RSS/Atom 源：

| ID | 名称 | 类型 | URL |
| --- | --- | --- | --- |
| `arxiv-radiotherapy-ai` | arXiv 放疗 + AI | 预印本 Atom 检索源 | `https://export.arxiv.org/api/query?search_query=all:radiotherapy+AND+all:%22artificial+intelligence%22&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending` |
| `ijrobp-red-journal` | International Journal of Radiation Oncology•Biology•Physics / Red Journal | 放疗期刊 RSS | `https://rss.sciencedirect.com/publication/science/03603016` |
| `radonc-green-journal` | Radiotherapy and Oncology / Green Journal | 放疗期刊 RSS | `https://rss.sciencedirect.com/publication/science/01678140` |

不使用 `http://www.redjournal.org/current.rss` 作为主源，因为该源可返回 200，但 XML 解析不稳定。

第一期不做页面内新增、编辑、删除 RSS 地址，也不做自动发现全网 RSS。后续可以在这个基础上扩展启用/停用、单源同步和源发现。

## 架构

采集策略调整为：RSS 负责发现，API 负责增强，搜索负责兜底。

1. 新增 RSS 源配置模块，维护三条初始订阅源及其启用状态、分类、来源标识和展示信息。
2. 新增 `rss_feeds` 采集器，统一解析 RSS 2.0 和 Atom 1.0。
3. `collect.py` 优先运行 `rss_feeds`，再运行现有兜底采集器。
4. 现有 `papers` 采集器暂时保留，但不再作为有 RSS 来源的默认主入口。
5. Semantic Scholar、arXiv API 或 DOI 查询后续只做元数据增强，不阻塞第一期 RSS 采集。
6. 新增后端 `/api/rss-sources`，返回 RSS 源配置和最近同步状态。
7. 新增 Next.js 代理接口和前端页面，并在侧边导航加入“RSS 订阅源”。

## RSS 源配置

每个订阅源包含以下字段：

- `id`：稳定唯一 ID。
- `name`：完整名称。
- `short_name`：界面短名。
- `kind`：`academic` 或 `journal`。
- `source_type`：第一期固定为 `paper`。
- `category`：第一期固定为 `paper`。
- `feed_url`：RSS/Atom URL。
- `homepage`：来源主页。
- `enabled`：是否启用。
- `description`：页面展示说明。
- `trust_level`：来源可信度。
- `collection_method`：例如 `RSS/Atom 订阅` 或 `arXiv Atom 检索源`。

同步状态从现有同步日志聚合，不把运行状态硬编码到配置里。

## 采集数据流

`rss_feeds.collect(days_back)` 的流程：

1. 读取启用的 RSS 源配置。
2. 对每个源发起 HTTP 请求，带合理超时和 User-Agent。
3. 根据 XML 根节点识别 RSS 2.0 或 Atom 1.0。
4. 提取标题、链接、摘要、发布日期、作者、DOI、arXiv ID。
5. 按 `days_back` 过滤过旧条目。
6. 归一化为现有 `content` 表需要的字段。
7. 使用稳定 ID 生成规则避免重复。
8. 调用 `upsert_content()` 写入内容。
9. 对每个源写入同步日志，记录 found/new/updated/error。

单个源失败不影响其他源继续采集。

## 去重规则

稳定 ID 和去重优先级：

1. DOI。
2. arXiv ID。
3. canonical URL。
4. 归一化标题。

红皮和绿皮默认全收，因为来源本身就是放疗核心期刊。arXiv 源仍保留放疗 + AI 检索条件，并在条目层补充关键词检查，避免宽泛条目进入。

## 推荐分与分类

所有 RSS 条目第一期写入 `category = paper` 和 `source_type = paper`。

推荐分采用轻量规则：

- arXiv：基础分 70。
- Red Journal / Green Journal：基础分 85。
- 标题或摘要命中 AI、自适应放疗、自动勾画、治疗计划、质子、FLASH、SBRT、MR-Linac 等关键词时加分。
- `is_featured` 根据最终分数阈值生成。

后续可以接入现有 LLM enrichment 或 Semantic Scholar 元数据增强，但第一期不依赖这些增强才能入库。

## API 设计

后端新增：

- `GET /api/rss-sources`

返回结构：

```json
{
  "sources": [
    {
      "id": "ijrobp-red-journal",
      "name": "International Journal of Radiation Oncology•Biology•Physics",
      "short_name": "Red Journal",
      "kind": "journal",
      "feed_url": "https://rss.sciencedirect.com/publication/science/03603016",
      "enabled": true,
      "last_sync_at": "2026-05-31T10:00:00Z",
      "items_found": 100,
      "items_new": 3,
      "items_updated": 0,
      "status": "success",
      "error_message": ""
    }
  ]
}
```

Next.js 新增代理：

- `src/app/api/rss-sources/route.ts`

该代理沿用现有 `API_BASE_URL` 模式。

## 页面设计

侧边导航新增入口：

- RSS 订阅源

页面展示只读订阅源列表。字段包括：

- 源名称和短名。
- 类型。
- RSS/Atom URL。
- 启用状态。
- 最近同步时间。
- 最近发现、新增、更新数量。
- 最近错误信息。

页面只负责透明展示当前订阅源，不承担配置编辑。错误状态直接暴露，便于判断是网络问题、源格式变化还是空结果。

## 错误处理

- HTTP 请求失败、非 2xx、XML 解析失败、空结果都记录到对应源的同步日志。
- 单个源失败不终止整次采集。
- UI 显示最近错误文本。
- 如果 ScienceDirect feed 格式变化，错误会体现在 RSS 订阅源页面，而不是静默失败。

## 验证计划

1. 验证三个 URL 均能返回 RSS/Atom 内容。
2. 跑一次 RSS 采集，确认 `content` 表有新增或更新。
3. 打开首页，确认 RSS 论文进入现有信息流。
4. 打开“RSS 订阅源”页面，确认三个源和同步状态显示正确。
5. 运行 `npm run typecheck`。
6. 如改动 Python 采集器，运行对应采集脚本验证解析与入库。

## 参考来源

- arXiv API User Manual: https://info.arxiv.org/help/api/user-manual.html
- arXiv RSS/Atom feeds: https://info.arxiv.org/help/rss.html
- ScienceDirect IJROBP journal page: https://www.sciencedirect.com/journal/international-journal-of-radiation-oncology-biology-physics
- ScienceDirect Radiotherapy and Oncology journal page: https://www.sciencedirect.com/journal/radiotherapy-and-oncology
- ScienceDirect RSS setup instructions: https://service.elsevier.com/app/answers/detail/a_id/10818/supporthub/sciencedirect/
