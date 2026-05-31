# Medical News RSS Expansion Design

## 背景

当前 RSS-first 改造已经覆盖论文源：arXiv 放疗 + AI、Red Journal、Green Journal。新闻源仍主要依赖搜索/页面采集，不够主动，也不利于透明展示来源状态。

本设计将医疗新闻、监管、安全警报、肿瘤研究期刊 RSS 纳入统一 RSS 目录，使新闻采集也遵循“RSS 负责发现，搜索负责兜底”的原则。

## 小修订版（实施前补充）

为避免把新闻 RSS 误接入论文流，实施时使用三层字段约定：

- `kind`：来源性质，用于来源识别和 UI 标签，例如 `journal`、`industry_news`、`regulatory`、`medical_reference`。
- `source_type`：内容主类型，只使用 `paper` 或 `news`。只有 `source_type = paper` 的条目生成论文解读报告。
- `category`：首页筛选与内容标签，例如 `paper`、`research`、`industry_news`、`regulatory`。

RSS 源目录与主来源目录需要同步维护：

- `scripts/rss_source_catalog.py` 负责 RSS URL、启用状态、基础分、每源采集上限和 RSS 页面展示。
- `scripts/source_catalog.py` 负责首页卡片来源识别；新增 AACR、MedlinePlus 等来源时需要同步加入，避免首页只显示原始 source 字符串。
- 已存在的 FDA、Medical Xpress 来源可以复用，但 RSS 条目仍应写入 `meta.source_id`、`meta.source_kind`、`meta.rss_feed_url`，方便追踪 RSS 来源。

新闻 RSS 第一阶段不强制 AI/放疗双关键词过滤，但必须设置每源采集上限，避免宽泛新闻源造成噪声和 LLM 成本失控。默认使用 `max_items_per_run = 20`，期刊源可按需要设为 30；后续再引入更细的相关性过滤或 UI 筛选。

前端验收需要包含分类显示：

- 首页分类筛选增加 `research`（研究）和 `regulatory`（监管）。
- 内容卡片标签映射增加 `regulatory`（监管/安全）。
- `/rss-sources` 页面继续只读展示，不新增编辑功能。

## 第一阶段范围

第一阶段只启用已验证能被当前 Python XML 解析器直接读取的 RSS 源。

| ID | 名称 | kind | source_type | category | max_items_per_run | RSS URL | 验证结果 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fda-medwatch` | FDA MedWatch Safety Alerts | regulatory | news | regulatory | 20 | `https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml` | HTTP 200，RSS，可解析，20 items |
| `medicalxpress-cancer` | Medical Xpress Oncology/Cancer | industry_news | news | research | 20 | `https://medicalxpress.com/rss-feed/cancer-news/` | HTTP 200，RSS，可解析，30 items |
| `medicalxpress-breaking-cancer` | Medical Xpress Breaking Oncology/Cancer | industry_news | news | research | 20 | `https://medicalxpress.com/rss-feed/breaking/cancer-news/` | HTTP 200，RSS，可解析，14 items |
| `aacr-cancer-discovery` | AACR Cancer Discovery | journal | paper | paper | 30 | `https://aacrjournals.org/rss/site_1000003/1000004.xml` | HTTP 200，RSS，可解析，38 items |
| `aacr-clinical-cancer-research` | AACR Clinical Cancer Research | journal | paper | paper | 30 | `https://aacrjournals.org/rss/site_1000013/1000009.xml` | HTTP 200，RSS，可解析，20 items |
| `medlineplus-cancer` | MedlinePlus Cancer | medical_reference | news | industry_news | 20 | `https://medlineplus.gov/feeds/topics/cancer.xml` | HTTP 200，RSS，可解析，0 items |
| `medlineplus-radiation-therapy` | MedlinePlus Radiation Therapy | medical_reference | news | industry_news | 20 | `https://medlineplus.gov/feeds/topics/radiationtherapy.xml` | HTTP 200，RSS，可解析，0 items |

MedlinePlus 两个源当前为空，但 URL 和格式有效。它们可以启用并在页面显示“暂无内容”，不应被视为失败。

## 暂不启用来源

以下来源重要，但第一阶段不进入主采集：

| 来源 | 原因 | 后续处理 |
| --- | --- | --- |
| NCI News Releases | 官方 RSS 存在，但脚本请求返回 403 | 后续做请求头/访问策略适配，或页面监控 |
| NCI Cancer Currents | 官方 RSS 存在，但脚本请求返回 403 | 后续做请求头/访问策略适配，或页面监控 |
| ASCO JCO RSS | 返回 200，但 XML 标准解析失败 | 后续做容错解析或改用更稳定细分 feed |
| RSNA AI / Imaging Cancer Most Read | 请求返回 403 | 后续用页面监控或授权友好的 feed |
| RSNA eTOC 推断 URL | 返回 404 | 不接入，除非找到官方有效 URL |
| ASTRO 新闻页 | 未发现官方 RSS | 继续作为页面监控/搜索兜底来源 |
| 厂商 press release 页 | 未发现官方 RSS | 继续作为页面监控/搜索兜底来源 |

## 架构调整

现有 `scripts/rss_source_catalog.py` 从“论文 RSS 目录”升级为“统一 RSS 订阅源目录”。每个源继续使用同一结构，但 `source_type` 和 `category` 不再固定为 `paper`。

新增源按用途配置：

- `kind = journal` 且 `source_type = paper`：AACR 期刊源，进入论文流，允许生成论文解读报告。
- `kind = industry_news` 或 `medical_reference` 且 `source_type = news`：Medical Xpress、MedlinePlus，进入新闻/研究动态流，不生成论文报告。
- `kind = regulatory`、`source_type = news` 且 `category = regulatory`：FDA MedWatch，进入监管/安全动态。

`rss_feeds.py` 继续作为统一 RSS/Atom 采集器，但生成内容时遵循源配置：

- `source` 使用配置中的来源名。
- `source_type` 使用配置值。
- `category` 使用配置值。
- `tags` 合并配置 tags、RSS、来源短名，并按 `source_type` 使用“论文”或“新闻”基础标签。
- `meta.source_id`、`meta.source_kind`、`meta.rss_feed_url` 继续保留。
- 只有 arXiv 源使用 arXiv 专属相关性过滤和 arXiv ID 规范化。
- 期刊 RSS 默认全收。
- 新闻 RSS 不强制 AI/放疗双关键词，但每源执行 `max_items_per_run` 上限；后续可以通过评分和 UI 筛选降低噪声。

## 推荐分规则

第一阶段继续使用轻量规则，按源设置基础分：

- FDA MedWatch：82。监管/安全警报对产品和临床风险有直接价值。
- Medical Xpress Cancer：72。医学媒体，覆盖面广但需要筛选。
- Medical Xpress Breaking Cancer：76。时效性更强。
- AACR Cancer Discovery：84。高质量肿瘤研究期刊。
- AACR Clinical Cancer Research：84。临床转化肿瘤研究期刊。
- MedlinePlus Cancer：68。偏患者教育/参考。
- MedlinePlus Radiation Therapy：72。与放疗主题直接相关。

命中以下关键词时加分：radiotherapy、radiation therapy、radiation oncology、AI、machine learning、adaptive radiotherapy、auto-contouring、treatment planning、FDA、recall、safety alert、device、clinical trial。

新闻源评分应允许低于论文源，但监管/安全警报不应因为缺少 AI/放疗关键词被压得过低。第一阶段只调整基础分和关键词加分，不做复杂降噪模型。

## UI 和 API

现有 `/api/rss-sources` 和 `/rss-sources` 页面继续复用。

页面需要自然展示更多源，不新增编辑功能。卡片字段保持：

- 源名称和短名。
- 类型标签。
- `source_type`。
- RSS URL。
- 启用状态。
- 最近同步时间。
- found/new/updated。
- 最近错误。
- 来源主页。

因为源数量从 3 个增加到 10 个，页面仍使用卡片列表即可，不做分页和分组；后续源数量继续增加时再考虑筛选。

首页分类筛选需要能看到新增新闻分类：

- `research` 显示为“研究”。
- `regulatory` 显示为“监管”或“监管/安全”。

## 错误处理

- 单个源失败不影响其他源。
- 空 feed 是成功状态，items_found=0，不记录为错误。
- 403/404/解析失败记录为对应源错误。
- 聚合同步状态在任一源失败时记录为 error，并写入错误摘要。
- 暂不启用 NCI/ASCO/RSNA 问题源，避免主页面长期显示已知失败。

## 验证计划

1. 验证 7 个新增启用源均出现在 `enabled_rss_sources()`。
2. 对 7 个新增源运行 `collect_by_source(days_back=14)`，确认：
   - FDA、Medical Xpress、AACR 源能返回 item。
   - MedlinePlus 源即使 items=0 也没有 error。
3. 跑 `collect_rss_sources(days_back=14)`，确认新增源写入 `sync_log`。
4. 打开 `/rss-sources`，确认页面展示现有 3 个论文源 + 7 个新闻/监管/研究源。
5. 打开首页，确认新闻 RSS 内容进入信息流，且 `source_type/news/category` 显示合理。
6. 运行 `npm run typecheck` 和 `npm run build`。

## 参考来源

- FDA News Feeds: https://www.fda.gov/about-fda/contact-fda/subscribe-podcasts-and-news-feeds
- FDA MedWatch RSS: https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml
- Medical Xpress RSS Feeds: https://medicalxpress.com/feeds/
- Medical Xpress Cancer RSS: https://medicalxpress.com/rss-feed/cancer-news/
- Medical Xpress Breaking Cancer RSS: https://medicalxpress.com/rss-feed/breaking/cancer-news/
- AACR RSS Feeds: https://aacrjournals.org/pages/rss
- AACR Cancer Discovery RSS: https://aacrjournals.org/rss/site_1000003/1000004.xml
- AACR Clinical Cancer Research RSS: https://aacrjournals.org/rss/site_1000013/1000009.xml
- MedlinePlus RSS Feeds: https://medlineplus.gov/rss.html
- MedlinePlus Cancer RSS: https://medlineplus.gov/feeds/topics/cancer.xml
- MedlinePlus Radiation Therapy RSS: https://medlineplus.gov/feeds/topics/radiationtherapy.xml
- ASCO Publications RSS: https://ascopubs.org/about/rss
- RSNA Alerts and RSS Feeds: https://pubs.rsna.org/page/help/alerts
- NCI RSS Feeds: https://www.cancer.gov/syndication/rss
