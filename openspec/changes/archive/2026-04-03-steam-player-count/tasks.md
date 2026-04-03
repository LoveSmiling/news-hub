## 1. 依赖安装

- [x] 1.1 在 `requirements.txt` 中添加 `beautifulsoup4` 和 `lxml` 依赖

## 2. 自定义爬虫加载机制

- [x] 2.1 修改 `app/services/collector.py` 的 `create_spider()` 函数，添加 `type: custom` 分支，使用 `importlib.import_module` 按 `app.spiders.custom.{name}_spider` 命名约定动态加载爬虫模块
- [x] 2.2 在动态加载逻辑中查找模块内 `BaseSpider` 子类并实例化，模块不存在或无有效类时抛出 `ValueError`
- [x] 2.3 确保 `app/spiders/custom/__init__.py` 存在（使其成为合法 Python 包）

## 3. Steam 爬虫实现

- [x] 3.1 创建 `app/spiders/custom/steam_spider.py`，继承 `BaseSpider`，实现 `fetch()` 方法
- [x] 3.2 在 `fetch()` 中使用 httpx 请求 `https://store.steampowered.com/stats/stats/`，用 BeautifulSoup 解析 `#detailStats tr.player_count_row`
- [x] 3.3 提取每行的游戏名称（`a.gameLink` 文本）、游戏链接（`a.gameLink` href）、在线人数（`.currentServers` 文本），构建 `SpiderItem` 列表
- [x] 3.4 将在线人数存入 `SpiderItem.hot_value`，游戏链接存入 `url`，排行序号存入 `rank`

## 4. 数据源配置

- [x] 4.1 在 `app/spiders/sources.yaml` 中添加 Steam 数据源配置：`name: steam`，`display_name: Steam在线`，`category: 游戏`，`type: custom`，`schedule: "*/10 * * * *"`，`max_items: 30`

## 5. 验证

- [x] 5.1 运行项目确认 Steam 爬虫能成功加载并采集数据
