## 上下文

当前系统通过 RSSHub 容器代理采集 11 个源。所有源在 sources.yaml 中以 `type: rsshub` + `route` 方式配置，RSSSpider 将 `rsshub_url + route` 拼接为 feed URL。SourceConfig 数据类已预留 `url` 字段但未使用。collector.py 的 `create_spider()` 仅处理 `type == "rsshub"` 分支。

## 目标 / 非目标

**目标：**
- 支持通过 `type: rss` + `url` 直接订阅外部 RSS/Atom 链接
- 复用现有 RSSSpider 解析逻辑，最小化代码改动
- 在 sources.yaml 新增 8-12 个优质源（RSSHub + 外部 RSS 混合）
- 前端简报生成的来源下拉列表同步新增源

**非目标：**
- 不开发新的爬虫类型（如 API 爬虫、HTML 爬虫）
- 不做源的动态管理界面（后续可做）
- 不更改现有 11 个源的配置

## 决策

### D1: 复用 RSSSpider 处理外部 RSS

外部 RSS 和 RSSHub 返回的都是标准 RSS/Atom XML，解析逻辑完全相同，区别仅在于 feed URL 的来源。在 RSSSpider.__init__ 中判断：如果 config.url 存在则直接使用，否则走 rsshub_url + route 拼接。

替代方案：创建独立的 ExternalRSSSpider 类。但代码会完全重复，不值得。

### D2: 新增源的选择标准

选择依据：覆盖主流中文互联网平台 + 有代表性的国际源。优先选择 RSSHub 路由稳定、内容更新频繁的源。先在本地验证路由可用再加入配置。

### D3: 前端 sourceOptions 同步方式

直接在 BriefingsView.vue 的硬编码数组中补充新源。简单直接，与现有模式一致。

## 风险 / 权衡

- [新 RSSHub 路由不可用] → 添加前手动验证，不可用的跳过
- [外部 RSS 链接不稳定或响应慢] → RSSSpider 已有 30s 超时和错误处理，单源失败不影响其他
- [源过多导致采集压力] → 合理设置 schedule 频率，低频源用 */30 或每小时，避免并发过高
