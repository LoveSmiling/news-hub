# map-reduce-summarizer 规范

## 目的
待定 - 由归档变更 content-service 创建。归档后请更新目的。
## 需求
### 需求:Map阶段批次摘要
系统必须提供 Map 阶段处理能力，将一批内容条目压缩为一段批次摘要。

#### 场景:单批次摘要生成
- **当** 输入一批 ≤ BATCH_SIZE（默认 10）条 `ContentItem`
- **那么** 必须将所有条目的标题和内容组装为 prompt，调用 LLM 生成该批次的摘要（约 300 字）

#### 场景:批次内容组装格式
- **当** 组装 Map 阶段的 prompt 时
- **那么** 每条内容必须以编号列表格式呈现：`{序号}. [{来源}] {标题}\n{截断后内容}`

#### 场景:Map调用参数
- **当** 调用 LLM 时
- **那么** 必须使用 `action="map_summarize"` 记录日志，`max_tokens` 必须使用 MAP_MAX_TOKENS（默认 512），必须传递 `enable_thinking=False`

### 需求:Reduce阶段聚合简报
系统必须提供 Reduce 阶段处理能力，将多个 Map 摘要聚合为一份结构化简报。

#### 场景:聚合生成
- **当** 输入多个 Map 阶段生成的批次摘要
- **那么** 必须将所有批次摘要拼接后调用 LLM，生成结构化的 Markdown 格式简报

#### 场景:简报结构
- **当** 生成最终简报时
- **那么** 简报必须包含：核心要点（要点列表）、分主题归纳、趋势洞察（如有明显趋势）

#### 场景:Reduce调用参数
- **当** 调用 LLM 时
- **那么** 必须使用 `action="reduce_summarize"` 记录日志，`max_tokens` 必须使用 REDUCE_MAX_TOKENS（默认 2048），必须传递 `enable_thinking=False`

### 需求:完整Map-Reduce管线
系统必须提供 `map_reduce_summarize(items: list[ContentItem], ...) -> str` 异步函数，执行完整的两阶段管线。

#### 场景:正常流程
- **当** 输入 N 条 `ContentItem`（N > 0）
- **那么** 必须自动分批（每批 BATCH_SIZE 条），并行执行 Map 阶段，收集所有批次摘要后执行 Reduce 阶段，返回最终简报 Markdown 文本

#### 场景:少量内容跳过Map
- **当** 输入条目数 ≤ BATCH_SIZE（只有一批）
- **那么** 必须跳过 Map 阶段，直接将所有内容送入 Reduce 阶段生成简报

#### 场景:并发控制
- **当** Map 阶段并行执行时
- **那么** 必须通过信号量（默认并发数 3）限制同时进行的 LLM 调用数量

#### 场景:Map批次部分失败
- **当** Map 阶段某个批次调用 LLM 失败
- **那么** 必须跳过该批次并记录警告日志，使用其余成功批次的摘要继续 Reduce 阶段

#### 场景:全部Map失败
- **当** Map 阶段所有批次均失败
- **那么** 必须返回错误信息字符串，禁止抛出异常

#### 场景:空输入
- **当** 输入为空列表
- **那么** 必须返回空字符串，禁止抛出异常

### 需求:可配置参数
Map-Reduce 框架的关键参数必须可通过函数参数覆盖，包含合理默认值。

#### 场景:默认参数值
- **当** 调用 `map_reduce_summarize` 未指定可选参数时
- **那么** 必须使用默认值：`batch_size=10`, `max_content_chars=2000`, `map_max_tokens=512`, `reduce_max_tokens=2048`, `max_concurrency=3`

#### 场景:自定义参数
- **当** 调用时显式传入参数（如 `batch_size=5`, `reduce_max_tokens=4096`）
- **那么** 必须使用传入的值覆盖默认值

