## ADDED Requirements

### 需求:Steam 在线人数数据采集
系统必须从 Steam 统计页面（`https://store.steampowered.com/stats/stats/`）采集游戏在线人数排行数据。爬虫必须解析页面 HTML，提取 `#detailStats` 表格中每个 `tr.player_count_row` 行的游戏名称、游戏链接和当前在线人数。

#### 场景:成功采集 Steam 在线人数
- **当** 调度器触发 Steam 数据源的采集任务
- **那么** 系统必须请求 Steam 统计页面，解析 HTML 表格，为每款游戏生成一个 `SpiderItem`，其中 `title` 为游戏名称，`url` 为游戏 Steam 商店链接，`hot_value` 为当前在线人数字符串，`rank` 为排行序号

#### 场景:Steam 页面不可访问
- **当** Steam 统计页面返回 HTTP 错误或请求超时
- **那么** 系统必须记录错误日志并返回空列表，禁止影响其他数据源的采集

#### 场景:Steam 页面结构变化
- **当** HTML 中没有找到预期的 `#detailStats` 表格或 `.player_count_row` 行
- **那么** 系统必须记录警告日志并返回空列表

### 需求:Steam 数据源配置
Steam 数据源必须在 `sources.yaml` 中配置，`type` 为 `custom`，`name` 为 `steam`，`category` 为 `游戏`，采集频率为每 10 分钟一次。

#### 场景:Steam 配置加载
- **当** 系统从 `sources.yaml` 加载数据源配置
- **那么** Steam 源必须以 `type: custom` 被识别，并通过自定义爬虫机制加载 `steam_spider.py`
