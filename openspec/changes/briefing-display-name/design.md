## 上下文

系统使用 `Source` 模型的两个字段标识数据源：
- `name`（英文标识，如 `v2ex`、`ithome`）：用于 DB 存储、API 查询、调度器 job ID 等内部逻辑
- `display_name`（中文名称，如 `V2EX热门`、`IT之家`）：用于前端展示

前端已正确使用 `display_name`，但后端简报生成流程中有 3 处直接将 `name` 暴露给用户和 LLM。

## 目标 / 非目标

**目标：**
- 简报标题、LLM 提示词、Map-Reduce 格式化中使用 `display_name` 替代 `name`
- 改动局限于简报生成流程的展示层，不触及内部存储和查询逻辑

**非目标：**
- 不修改 `HotItem.source` 字段的存储值
- 不修改 API URL 路径参数
- 不修改调度器 job ID
- 不修改前端（前端已正确使用 `display_name`）

## 决策

### 使用映射表而非扩展 ContentItem

**选择**：在 `briefing_generator.py` 中查询 Source 表构建 `{name: display_name}` 映射，传递给下游函数。

**替代方案**：给 `ContentItem` 数据类添加 `source_display` 字段，`retrieve_contents()` 查询时 JOIN Source 表。

**理由**：映射表方案侵入性更小——不需要修改 `ContentItem` 数据类、`content_service.py` 的查询逻辑，也不需要 JOIN 查询。简报生成是唯一需要 `display_name` 的后端消费者，在入口处做映射最经济。

### 函数签名变更

- `summarize_titles(source_name, ...)` 中的 `source_name` 参数语义不变（仍然是字符串），但调用方传入 `display_name` 值
- `_format_batch()` 增加一个可选的 `display_map` 参数，用于将 `item.source` 映射为中文名

## 风险 / 权衡

- **[低]** 若 Source 表中 `display_name` 为空或缺失 → 回退到 `name`，不会导致错误
- **[低]** `summarize_titles` 的 `source_name` 参数语义略有模糊（可以是 name 也可以是 display_name） → 可接受，因为它只用于展示，不用于查询
