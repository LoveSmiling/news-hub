# briefing-generation 规范

## 目的
待定 - 由归档变更 ai-briefing 创建。归档后请更新目的。
## 需求
### 需求:单来源简报生成
系统必须提供 `generate_source_briefing(source: str, date: str | None)` 异步函数，为指定来源生成当日简报。

#### 场景:正常生成
- **当** 调用指定 `source="thepaper"` 时
- **那么** 必须：(1) 创建 briefing 记录（status=generating）, (2) 通过 `retrieve_contents` 获取该来源当日数据, (3) 调用 `map_reduce_summarize` 生成简报, (4) 更新 briefing 的 content 和 status=done, (5) 保存关联的 briefing_items

#### 场景:无数据时
- **当** 指定来源在指定日期无条目
- **那么** 必须将 briefing 的 content 设置为提示信息，status 设置为 done

### 需求:每日汇总简报生成
系统必须提供 `generate_daily_briefing(date: str | None)` 异步函数，生成跨所有来源的当日汇总简报。

#### 场景:正常生成
- **当** 调用时
- **那么** 必须获取所有来源的当日数据，调用 `map_reduce_summarize` 生成汇总简报

#### 场景:自动标题
- **当** 生成每日汇总简报时
- **那么** 标题必须为格式 "每日简报 - {date}"（如 "每日简报 - 2026-04-01"）

### 需求:主题简报生成
系统必须提供 `generate_topic_briefing(keyword: str, hours: int)` 异步函数，为指定关键词生成主题简报。

#### 场景:正常生成
- **当** 调用指定 `keyword="AI"`, `hours=72` 时
- **那么** 必须通过 `retrieve_contents(keyword=keyword)` 获取最近 72 小时内匹配的条目，生成简报

### 需求:自选条目简报生成
系统必须提供 `generate_custom_briefing(item_ids: list[int], title: str | None)` 异步函数，为指定条目生成简报。

#### 场景:正常生成
- **当** 调用指定 `item_ids=[1, 2, 3]` 时
- **那么** 必须通过 `retrieve_contents(item_ids=item_ids)` 获取指定条目，生成简报

#### 场景:自定义标题
- **当** 未提供 title 参数时
- **那么** 必须使用默认标题 "自选简报 - {datetime}"

### 需求:后台异步执行
所有简报生成函数必须支持在后台 asyncio task 中执行，不阻塞 API 请求。

#### 场景:异步任务
- **当** API 触发简报生成时
- **那么** 必须通过 `asyncio.create_task` 在后台执行生成，API 立即返回简报记录（status=generating）

#### 场景:生成失败处理
- **当** 简报生成过程中发生异常
- **那么** 必须将 briefing 的 status 更新为 `failed`，将异常信息写入 content 字段，禁止抛出未处理异常

### 需求:简报来源标识展示

简报生成流程中所有用户可见和 LLM 可见的来源标识，必须使用 `display_name`（中文名称）而非 `name`（英文标识）。

#### 场景:简报标题使用 display_name

- **当** 系统为某个数据源生成简报时
- **那么** 简报标题必须使用该来源的 `display_name`（如 `IT之家 简报 - 2026-04-02`），而非 `name`（如 `ithome 简报 - 2026-04-02`）

#### 场景:单源摘要 LLM 提示词使用 display_name

- **当** 系统调用 `summarize_titles()` 为某个来源生成摘要时
- **那么** 传递给 LLM 的提示词中来源名称必须为该来源的 `display_name`（如 `以下是【IT之家】的热榜标题`）

#### 场景:Map-Reduce 格式化使用 display_name

- **当** 系统在 Map-Reduce 摘要中格式化内容条目时
- **那么** 来源标识必须使用 `display_name`（如 `[IT之家] 标题...`），而非 `name`（如 `[ithome] 标题...`）

#### 场景:display_name 缺失时回退

- **当** 某个来源的 `display_name` 为空或不存在于映射中时
- **那么** 系统必须回退使用 `name` 而非抛出错误

