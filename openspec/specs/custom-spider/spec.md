# custom-spider 规范

## 目的
自定义爬虫动态加载基础设施，支持非 RSS 类型的数据源采集。

## 需求
### 需求:自定义爬虫动态加载
系统必须支持 `type: custom` 类型的数据源。当 `create_spider()` 遇到 `type` 为 `custom` 时，必须通过 `importlib` 按命名约定 `app.spiders.custom.{source_name}_spider` 动态导入爬虫模块，并在模块中查找 `BaseSpider` 的子类进行实例化。

#### 场景:加载已存在的自定义爬虫
- **当** 数据源配置的 `type` 为 `custom` 且 `name` 为 `steam`
- **那么** 系统必须导入 `app.spiders.custom.steam_spider` 模块，找到其中继承 `BaseSpider` 的类并创建实例

#### 场景:自定义爬虫模块不存在
- **当** 数据源配置的 `type` 为 `custom` 但对应的爬虫模块文件不存在
- **那么** 系统必须抛出 `ValueError` 并包含明确的错误信息，指出缺失的模块路径

#### 场景:自定义爬虫模块中无有效爬虫类
- **当** 爬虫模块存在但其中没有 `BaseSpider` 的子类
- **那么** 系统必须抛出 `ValueError` 并包含明确的错误信息

### 需求:自定义爬虫必须遵循 BaseSpider 接口
所有自定义爬虫必须继承 `BaseSpider` 并实现 `fetch()` 方法，返回 `list[SpiderItem]`。爬虫文件必须放置在 `app/spiders/custom/` 目录下，文件名必须为 `{source_name}_spider.py`。

#### 场景:自定义爬虫返回标准数据
- **当** 自定义爬虫的 `fetch()` 方法执行成功
- **那么** 必须返回 `list[SpiderItem]`，每个 item 包含 `title`、`url`、`rank` 等标准字段
