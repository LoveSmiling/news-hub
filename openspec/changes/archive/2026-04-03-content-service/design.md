## 上下文

NewsHub 当前的 AI 功能（关键词提取、标题摘要）仅基于标题层运作。数据库中 `hot_items.raw_data` 的 `summary` 字段已存储了 RSS 提供的正文内容（HTML 格式），覆盖率 100%，长度从 130 字符（36kr 快讯）到 10K 字符（少数派全文）不等。

后续计划新增 AI 简报系统（`ai-briefing`）和 AI 对话系统（`ai-chat-backend`），两者都需要：清洗 HTML → 检索内容 → 压缩摘要。本变更抽取这些共享逻辑为独立服务层。

技术栈约束：Python 3.12、FastAPI、SQLAlchemy async、PostgreSQL 16、OpenAI 兼容 LLM API。

## 目标 / 非目标

**目标：**
- 提供可靠的 HTML → 纯文本清洗工具
- 提供按来源/时间/关键词/ID 批量检索清洗后内容的服务
- 提供 Map-Reduce 分级摘要框架，控制 Token 预算在可预测范围内
- 所有模块可独立测试，无前端和 API 端点依赖

**非目标：**
- 不新增 HTTP API 端点（由上层变更暴露）
- 不新增数据库表或迁移
- 不实现外部网页爬取（仅使用已采集的 RSS 数据）
- 不实现简报/对话的业务逻辑（那是上层变更的职责）

## 决策

### D1: HTML 清洗方案 — BeautifulSoup `get_text()`

**选择**: `BeautifulSoup4` + `html.parser`

**替代方案考虑**:
- 正则替换 `re.sub(r'<[^>]+>', '', text)`: 简单但不可靠，无法处理嵌套标签、HTML 实体、`<script>` 内容
- `lxml.html.clean`: 功能强大但引入重依赖
- `markdownify`: 转 Markdown 而非纯文本，对 LLM 输入不必要

**理由**: BeautifulSoup 已是 Python 生态标准，`html.parser` 是内建解析器无需额外依赖，`get_text(separator='\n')` 能干净地提取文本并保留段落结构。

### D2: 内容截断策略 — 字符级截断

**选择**: 按字符数截断，默认上限 2000 字符/条

**理由**: 
- Token 计算依赖 tokenizer，字符截断更简单且与模型无关
- 中文约 1 字符 ≈ 1-2 tokens，2000 字符约 2000-3000 tokens，安全可控
- 截断点尽量在句子边界（查找最后一个句号/句末标点）

### D3: Map-Reduce 架构 — 两阶段固定分批

**选择**: 固定分批大小的两阶段管线

```
输入 N 条内容
    │
    ├─ 分批: ceil(N / BATCH_SIZE) 个批次
    │
    ▼ MAP 阶段 (可并行)
    每批 → LLM → 批次摘要 (~300字)
    │
    ▼ REDUCE 阶段
    所有批次摘要 → LLM → 最终结构化简报
```

**配置参数**:
- `MAX_CONTENT_CHARS = 2000` — 单条内容截断上限
- `BATCH_SIZE = 10` — Map 阶段每批条目数
- `MAP_MAX_TOKENS = 512` — Map 输出 token 上限
- `REDUCE_MAX_TOKENS = 2048` — Reduce 输出 token 上限

**替代方案考虑**:
- 递归 Map-Reduce（多层聚合）: 过度复杂，当前数据量（每源 ≤30 条）两阶段足够
- Stuff（全部塞进一个 prompt）: 超长内容会超 context window
- Refine（逐条累积）: 串行调用太慢

**理由**: 两阶段在简单性和效果之间最优。30 条内容 → 3 批 MAP + 1 次 REDUCE = 4 次 LLM 调用，总 Token 约 14K，耗时约 30 秒。

### D4: Map 阶段并发 — asyncio.gather 有限并发

**选择**: `asyncio.gather` 并行 MAP 调用，通过 `asyncio.Semaphore` 限制并发数（默认 3）

**理由**: LLM 服务端可能有并发限制，信号量防止打满。3 并发下 3 批 MAP 一轮即可完成。

### D5: 内容检索 — 直接查询 hot_items 表

**选择**: 通过 SQLAlchemy async 查询 `hot_items` 表，使用 `raw_data->>'summary'` 提取内容后在 Python 层清洗

**理由**: 不新增表，不冗余存储。清洗是轻量 CPU 操作，无需持久化。检索条件直接复用已有索引（source、collected_at）。

## 风险 / 权衡

- **[HTML 清洗质量]** 部分来源的 HTML 结构复杂（含视频、图片标签）→ 清洗后可能丢失重要上下文。缓解：为特殊标签（如 `<img alt="...">`）保留 alt 文本。

- **[Token 预算不精确]** 字符截断无法精确对应实际 Token 数 → 可能偶尔超预算。缓解：截断上限保守设置，留有余量。

- **[LLM 调用失败]** Map 阶段某批失败会导致 Reduce 结果不完整 → 缓解：失败的批次跳过并在最终简报中注明。

- **[并发控制]** 多个简报同时生成可能打满 LLM 服务 → 缓解：信号量限制 + 上层调度控制。
