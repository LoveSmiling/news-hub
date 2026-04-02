## 新增需求

### 需求:支持外部RSS链接订阅
系统必须支持通过 `type: rss` 配置类型和 `url` 字段直接订阅任意外部 RSS/Atom 链接。解析逻辑必须复用现有 RSSSpider。

#### 场景:配置外部RSS源
- **当** sources.yaml 中存在 `type: rss` 且 `url: https://example.com/feed.xml` 的源配置
- **那么** RSSSpider 必须使用 url 字段值作为 feed URL 进行抓取，不拼接 rsshub_url

#### 场景:RSSHub源保持不变
- **当** sources.yaml 中存在 `type: rsshub` 且 `route: /v2ex/topics/hot` 的源配置
- **那么** RSSSpider 必须使用 rsshub_url + route 拼接作为 feed URL（行为不变）

#### 场景:create_spider支持rss类型
- **当** collector.py 的 create_spider() 接收到 `type == "rss"` 的 SourceConfig
- **那么** 必须创建并返回 RSSSpider 实例

### 需求:新增RSSHub采集源
系统必须在 sources.yaml 中新增以下 RSSHub 源（实际可用的）：微博热搜、知乎热榜、GitHub Trending、央视新闻、华尔街见闻等。每个源必须指定 name、display_name、category、type、route、schedule、max_items。

#### 场景:新增源配置格式正确
- **当** 新增一个 RSSHub 源到 sources.yaml
- **那么** 该源必须包含 name（唯一英文标识）、display_name（中文显示名）、category（综合/娱乐/新闻/科技）、type（rsshub）、route（RSSHub路径）、schedule（cron表达式）、max_items

#### 场景:路由验证
- **当** 新增 RSSHub 源
- **那么** 必须先通过 http://localhost:1200/<route> 验证返回有效 RSS XML 后方可加入

### 需求:新增外部RSS采集源
系统必须在 sources.yaml 中新增若干外部 RSS 源作为示范，使用 `type: rss` + `url` 配置方式。

#### 场景:外部RSS源配置格式
- **当** 新增一个外部 RSS 源到 sources.yaml
- **那么** 该源必须使用 `type: rss` 并提供完整的 `url` 字段（而非 route）

### 需求:前端来源选项同步
BriefingsView.vue 中的 sourceOptions 数组必须包含所有新增源的选项，使用与 sources.yaml 中 name/display_name 一致的 value/label。

#### 场景:新源出现在简报生成下拉列表
- **当** 用户在简报生成面板选择来源
- **那么** 下拉列表必须包含所有新增源的选项
