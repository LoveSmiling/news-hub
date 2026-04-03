## 为什么

项目当前所有数据源都是通过 RSSHub 采集的 RSS/Atom feed，不支持直接 HTML 抓取类的数据源。Steam 在线人数统计是一个高频热点数据，展示各游戏实时在线玩家数，用户价值高。参考项目 NewsNow 已有该数据源实现，现在需要将其集成到本项目中，同时建立自定义爬虫（custom spider）的基础设施，为后续更多非 RSS 数据源打下基础。

## 变更内容

- 新增 Steam 在线人数自定义爬虫（`app/spiders/custom/steam_spider.py`），从 `https://store.steampowered.com/stats/stats/` 解析 HTML 获取游戏在线人数排行
- 修改 `collector.py` 的 `create_spider()` 函数，支持 `type: custom` 类型并按 source name 动态加载自定义爬虫
- 在 `sources.yaml` 中添加 Steam 数据源配置
- 前端 Dashboard 自动展示新的 Steam 卡片（依赖现有热门数据展示框架，无需额外前端改动）

## 功能 (Capabilities)

### 新增功能

- `custom-spider`: 自定义爬虫基础设施，支持在 `app/spiders/custom/` 目录下编写非 RSS 类型的爬虫，collector 根据 source type 动态分发
- `steam-source`: Steam 在线人数数据源，抓取 Steam 统计页面解析游戏名、链接、在线人数

### 修改功能

- `data-collection`: 扩展 `create_spider()` 支持 `custom` 类型，动态导入并实例化自定义爬虫类

## 影响

- `app/services/collector.py` — 修改爬虫分发逻辑
- `app/spiders/custom/` — 新增自定义爬虫模块
- `app/spiders/sources.yaml` — 新增 Steam 源配置
- `requirements.txt` — 可能需要添加 `beautifulsoup4` / `lxml` 依赖
- 数据库 — 无 schema 变更（复用现有 `hot_items` 表）
- 前端 — 无改动（现有 HotCard 组件自动渲染新源）
