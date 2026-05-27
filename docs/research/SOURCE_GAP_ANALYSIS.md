# 后端信源差距分析

调研对象：<https://aihot.virxact.com/>、<https://aihot.virxact.com/all>、<https://aihot.virxact.com/agent>、<https://aihot.virxact.com/changelog>

## AIHOT 的信源模式

- 信息流不是只展示来源名称，而是区分精选、全部、频道和分类；`/all` 页可见“全部 / 一手信源 / 资讯 / 推文”等信源渠道筛选。
- Agent 接入页公开了 `GET /api/public/items?mode=selected`、`mode=all`、分类筛选、关键词搜索、日报和 RSS 等多种消费方式。
- 页面序列化数据里每条内容带有 `source.id`、`source.name`、`source.kind`，常见 kind 包括 `rss`、`x_search`、`json_list` 等。
- 更新日志说明其开放了“信源提报”和“信源墙”，把信源发现本身做成了可见、可审核、可沉淀的对象。

## 本项目原有差距

- 后端只有 `content.source` 字符串，没有 source id、来源类型、采集方式、主页、可信度和活跃状态。
- `/api/stats` 只能统计字符串来源，无法回答“配置了哪些信源、哪些启用、哪些近期没采到”。
- 采集入口只启用 `papers` 和 `vendor_news`，`google_news.py` 行业新闻采集器没有接入，导致内容过度偏向论文。
- 厂商广搜会把第三方媒体文章直接标成厂商来源，混淆“原文发布方”和“被提及厂商”。
- 前端卡片只显示 `source`，无法看出来源属于论文库、厂商官网、行业媒体、监管机构还是自动识别来源。

## 已改进

- 新增 `scripts/source_catalog.py`，集中维护论文数据库、期刊、学会/协会、监管机构、厂商官网、行业媒体和搜索聚合信源。
- `/api/items` 返回的每条内容新增 `source_id`、`source_kind`、`source_kind_label`、`source_display_name`、`source_collection_method`、`source_origin_host`、`source_note` 等字段。
- 新增 `/api/sources`，返回信源目录、活跃数量、内容数量、最新内容、分类覆盖和最近同步日志。
- `/api/stats` 增加 `source_kinds`、`source_cards`、`active_sources`、`configured_sources`。
- `collect.py` 接入 `radiotherapy_news` 行业新闻采集器，补齐学会、监管、行业新闻和临床动态入口。
- `vendor_news.py` 改为区分官网文章和第三方报道；第三方报道保留真实发布方，并在 `mentioned_vendor` 中标出厂商。
- 前端新增“信源覆盖”模块，展示配置/活跃/内容/待采集、信源类型分布和活跃信源卡片。
