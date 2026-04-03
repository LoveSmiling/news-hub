## 为什么

用户需要快速了解某个来源、某个时间段或某些主题的新闻全貌，而不是逐条浏览。当前系统仅展示标题级摘要，缺乏深度内容分析。需要一个 AI 简报系统，利用已部署的 content-service（HTML 清洗 + Map-Reduce 摘要框架）将大量热点内容自动压缩为结构化简报，支持手动触发和每日定时生成，生成后持久化存储供随时查阅。

## 变更内容

- **新增** `briefings` 数据库表，存储生成的简报（标题、类型、范围参数、Markdown 内容、状态、Token 消耗等）
- **新增** `briefing_items` 关联表，记录每份简报引用了哪些热点条目
- **新增** 简报生成服务 `briefing_service`，封装不同粒度的简报生成逻辑（单来源、多来源、自选条目）
- **新增** 简报 API 端点：列表、详情、手动触发生成、删除
- **新增** 每日定时任务：23:00 自动为所有来源生成当日简报
- **新增** 简报前端页面 `/briefings`：简报列表、手动触发面板、Markdown 详情查看、生成状态显示

## 功能 (Capabilities)

### 新增功能

- `briefing-storage`: 简报数据存储，包括 briefings 和 briefing_items 表的模型与迁移
- `briefing-generation`: 简报生成服务，封装单来源/跨来源/自选条目/每日全量等多种生成模式
- `briefing-api`: 简报 CRUD API 端点（列表、详情、触发生成、删除）
- `briefing-scheduler`: 每日定时简报生成任务
- `briefing-frontend`: 简报前端页面（列表、手动触发、Markdown 详情查看）

### 修改功能

（无）

## 影响

- **数据库**: 新增 2 张表 (`briefings`, `briefing_items`)，需要新迁移文件
- **后端 API**: 新增 `/api/briefings` 路由组
- **调度器**: 新增每日 23:00 定时任务
- **前端**: 新增 `BriefingsView.vue` 页面，导航栏新增入口
- **依赖**: 使用 `content-service` 变更提供的 `retrieve_contents` 和 `map_reduce_summarize`
- **前端依赖**: 需要 Markdown 渲染库（`markdown-it` 或 `v-md-editor`）
