## MODIFIED Requirements

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
