## 上下文

NewsHub 已完成 content-service 基础层（HTML 清洗、内容检索、Map-Reduce 摘要框架），已验证端到端运行。本变更在此基础上构建完整的简报系统：数据存储 → 生成服务 → API → 定时器 → 前端页面。

技术栈：Python 3.12、FastAPI、SQLAlchemy async + asyncpg、PostgreSQL 16、Vue 3 + Naive UI、Docker Compose。

## 目标 / 非目标

**目标：**
- 持久化存储 AI 生成的简报，支持随时查阅
- 支持多种简报粒度：单来源、跨来源、自选条目、自定义时间范围
- 提供手动触发和每日自动生成两种方式
- 前端展示简报列表、Markdown 详情、生成状态
- 简报关联原始热点条目，可溯源

**非目标：**
- 不实现简报编辑/修改功能（只读查阅）
- 不实现简报导出（PDF/邮件等）
- 不实现用户偏好个性化简报
- 不实现实时网页爬取（仅使用已采集的 RSS 数据）

## 决策

### D1: 简报生成异步模式 — 同步等待 + 状态轮询

**选择**: API 触发后立即在后台 asyncio task 中生成，前端通过轮询状态更新

**替代方案**:
- 同步阻塞等待：简报生成可能耗时 30-60 秒，HTTP 请求超时
- WebSocket 推送：复杂度过高，不值得

**方案**: POST 触发 → 立即返回 briefing 记录（status="generating"）→ 后台 task 执行 Map-Reduce → 完成后更新 status="done" → 前端每 3 秒轮询 GET 详情

### D2: 简报类型分类

| type | 含义 | scope_params |
|------|------|-------------|
| `source` | 单来源简报 | `{source: "thepaper"}` |
| `daily` | 每日全量简报 | `{date: "2026-04-01"}` |
| `topic` | 关键词主题简报 | `{keyword: "AI", hours: 72}` |
| `custom` | 自选条目简报 | `{item_ids: [1, 2, 3]}` |

### D3: Markdown 渲染方案 — markdown-it

**选择**: `markdown-it` + 自定义渲染

**替代方案**:
- `v-md-editor`: 编辑器组件，过重（简报只需只读渲染）
- `marked`: 功能类似但 markdown-it 插件生态更丰富

**理由**: markdown-it 轻量、纯渲染，配合 CSS 即可在暗色主题下美观展示。

### D4: 定时简报策略 — 每日 23:00 按来源分别生成

**选择**: 每天 23:00 为每个活跃来源各生成一份当日简报，另外生成一份跨来源汇总简报

**理由**: 按来源分开生成，便于用户按兴趣查看；汇总简报提供全局视角。串行生成避免打满 LLM。

### D5: 背景任务执行 — asyncio.create_task

**选择**: 使用 `asyncio.create_task` 在 FastAPI 事件循环中执行简报生成

**替代方案**:
- Celery/RQ: 引入 Redis 依赖，过度复杂
- 线程池: 与 async ORM 不兼容

**理由**: 简报生成本身是 IO-bound（LLM API 调用），asyncio task 天然适合，无需引入额外基础设施。

## 风险 / 权衡

- **[生成耗时]** 跨来源汇总简报（11来源）可能耗时数分钟 → 缓解：串行处理每来源，前端显示进度状态
- **[LLM 配额]** 每日定时生成消耗大量 Token → 缓解：usage_logger 已有追踪，可在设置中开关定时简报
- **[并发生成冲突]** 用户手动触发与定时任务同时生成 → 缓解：检查是否已有相同范围的 generating 简报，若有则跳过
- **[前端轮询开销]** 多份简报同时生成时频繁轮询 → 缓解：仅对 generating 状态的简报轮询，完成后停止
