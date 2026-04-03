## 上下文

当前项目的所有数据源均为 RSSHub 类型，通过 `RSSSpider` 统一采集 RSS/Atom feed。`collector.py` 中的 `create_spider()` 只处理 `rsshub`/`rss` 类型，遇到其它类型直接抛异常。`app/spiders/custom/` 目录已存在但为空。

Steam 在线人数数据来源于 `https://store.steampowered.com/stats/stats/` 页面，通过 HTML 解析获取（非 RSS），需要引入自定义爬虫机制。

参考项目 NewsNow 的实现（`server/sources/steam.ts`）使用 cheerio 解析 HTML 表格 `#detailStats tr.player_count_row`，提取游戏名（`a.gameLink`）、游戏链接（`href`）和在线人数（`.currentServers`）。

## 目标 / 非目标

**目标：**
- 建立自定义爬虫（custom spider）的动态加载机制，让 `create_spider()` 能按 source name 自动发现并实例化 `app/spiders/custom/` 下的爬虫类
- 实现 Steam 在线人数爬虫，作为第一个自定义爬虫
- Steam 爬虫的数据通过现有 `hot_items` 表存储，前端自动展示

**非目标：**
- 不修改前端代码（现有 HotCard 组件自动渲染新数据源）
- 不修改数据库 schema（复用 `hot_items` 表的 `raw_data` JSONB 字段存储额外信息）
- 不为自定义爬虫建立注册表或插件系统（按约定命名即可）

## 决策

### 1. 自定义爬虫加载方式：基于命名约定的动态导入

**选择**：`create_spider()` 对 `type: custom` 的源，用 `importlib` 按 `app.spiders.custom.{name}_spider` 路径动态导入模块，在模块中查找 `BaseSpider` 的子类并实例化。

**替代方案**：
- 显式注册表（dict mapping）：需要每加新爬虫就改 collector.py，违反开闭原则
- 扫描目录自动注册：启动时扫描整个 custom 目录，开销大且不必要

**理由**：命名约定最简洁，加新爬虫只需放一个文件到 `custom/` 目录并在 `sources.yaml` 配置即可，无需修改任何已有代码。

### 2. HTML 解析库：BeautifulSoup4 + lxml

**选择**：使用 `beautifulsoup4` 配合 `lxml` 解析器。

**替代方案**：
- `selectolax`：更快但 API 较少
- `parsel`（Scrapy 自带）：引入过重

**理由**：项目已使用 httpx 做 HTTP 请求，bs4 是 Python 生态最成熟的 HTML 解析方案，配合 lxml 解析器性能足够。

### 3. 在线人数存储方式

**选择**：在线人数存入 `SpiderItem.hot_value` 字段（字符串类型），同时完整数据放入 `raw_data`。

**理由**：`hot_value` 已有展示逻辑支持，不需要额外前端改动。在线人数本身就是一个"热度值"。

## 风险 / 权衡

- **Steam 页面结构变更** → HTML 选择器可能失效。缓解：爬虫 fetch 返回空列表时已有 warning 日志，不影响其他源
- **Steam 访问限制** → 中国大陆可能有访问延迟。缓解：httpx 超时设为 30s，失败走标准错误处理
- **动态导入安全性** → `importlib.import_module` 只加载 `app.spiders.custom` 下的模块，路径由代码控制而非用户输入，不存在路径注入风险
