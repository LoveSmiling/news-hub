## 为什么

简报生成流程中，LLM 提示词和简报标题直接使用 `source.name`（英文标识，如 `v2ex`、`ithome`），导致生成的简报内容中引用的来源标识对用户不直观，难以快速识别对应的平台。前端展示已正确使用 `display_name`（中文名称），但后端简报生成未跟进。

## 变更内容

- 简报标题从 `"{source} 简报 - {date}"` 改为使用 `display_name`
- `summarize_titles()` 的 LLM 提示词中 `【{source_name}】` 改为传入 `display_name`
- Map-Reduce 摘要器中 `[{item.source}]` 格式改为使用 `display_name`
- `briefing_generator.py` 中建立 `name → display_name` 映射，向下游传递

## 功能 (Capabilities)

### 新增功能

_无_

### 修改功能

- `briefing-generation`: 简报生成时，所有用户/LLM 可见的来源标识改为使用 display_name 而非 name

## 影响

- `app/services/briefing_generator.py` — 简报标题、传参
- `app/services/ai/summarizer.py` — LLM 提示词
- `app/services/ai/map_reduce_summarizer.py` — 内容格式化
- 不影响数据库存储、API 查询、调度器等内部使用 `name` 的逻辑
