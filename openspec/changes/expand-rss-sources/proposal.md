## 为什么

当前系统仅有 11 个采集源（v2ex、coolapk、cls、bilibili、douban-movie、thepaper、zaobao、ithome、36kr、sspai、hackernews），覆盖面有限。用户希望扩展信息源以获取更全面的热点聚合。同时，系统目前仅支持 RSSHub 代理路由（type: rsshub），无法直接订阅第三方发布的标准 RSS/Atom 链接，限制了源的来源渠道。

## 变更内容

1. **支持外部 RSS 链接**：扩展 RSSSpider 和 collector，使 `type: rss` + `url` 字段可直接订阅任意外部 RSS/Atom 链接，复用现有解析逻辑
2. **新增 RSSHub 源**：在 sources.yaml 中添加微博热搜、知乎热榜、抖音热榜、GitHub Trending、央视新闻、华尔街见闻等热门源
3. **新增外部 RSS 源**：添加阮一峰博客、Solidot 等标准 RSS 源作为示范
4. **前端来源选项同步**：简报生成页面的来源下拉列表需同步新增源

## 功能 (Capabilities)

### 新增功能
- `external-rss`: 支持 type: rss 直接订阅外部 RSS/Atom 链接，通过 url 字段指定 feed 地址

### 修改功能
- （无规范级需求变更，仅为配置新增和代码小幅改动）

## 影响

- `app/spiders/rss_spider.py`: RSSSpider.__init__ 增加 url 判断逻辑（~3行）
- `app/services/collector.py`: create_spider() 增加 type == "rss" 支持（~2行）
- `app/spiders/sources.yaml`: 新增多个源配置
- `frontend/src/views/BriefingsView.vue`: sourceOptions 数组同步新增源
