## 为什么

当前系统有 2000+ 条新闻数据，但 embedding 字段全部为空，导致 Chat RAG 向量搜索无法命中任何内容，AI 对话质量严重受限。keywords 也仅覆盖每次采集的前 10 条。需要一套知识库管理机制：采集时自动生成 embedding/keywords，并提供管理页面支持可视化、语义搜索和手动构建/重建。

## 变更内容

- **新增**：embedding 生成服务（拼接 title+summary 生成 1024 维向量）
- **新增**：知识库后台任务管理器（内存任务，支持增量更新/全量重建+进度追踪）
- **新增**：知识库 API（stats/search/tasks 三个端点）
- **新增**：知识库管理前端页面（概览面板+语义搜索+构建操作+进度显示）
- **修改**：采集调度器，采集后自动生成 embedding 和 keywords（全覆盖，不再只前 10 条）

## 功能 (Capabilities)

### 新增功能
- `kb-embedding-service`: embedding 文本拼接与批量生成服务，提供 build_embedding_text() 和批量处理函数
- `kb-task-manager`: 内存后台任务管理器，支持增量更新/全量重建，进度追踪，供 API 调用
- `kb-api`: 知识库 REST API — GET /api/kb/stats, POST /api/kb/search, POST /api/kb/tasks, GET /api/kb/tasks/{id}
- `kb-frontend`: 知识库管理前端页面 — 概览统计、语义搜索、构建操作触发与进度显示

### 修改功能
- `data-collection`: 采集调度器改造 — 采集后自动为所有新条目生成 embedding 和 keywords（取消前 10 条限制）

## 影响

- 新增文件：`app/services/kb_service.py`, `app/services/kb_task_manager.py`, `app/api/kb.py`, `frontend/src/views/KnowledgeBaseView.vue`
- 修改文件：`app/scheduler/jobs.py`（采集后自动 enrich）, `app/main.py`（注册 kb router）, `frontend/src/router/index.ts`, `frontend/src/AppLayout.vue`
- 依赖现有：`app/services/ai/embedder.py`（get_embeddings_batch）, `app/utils/html_cleaner.py`, `app/services/ai/keyword_extractor.py`
- 无数据库迁移（复用 hot_items 现有 embedding/keywords 字段）
