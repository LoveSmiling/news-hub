## 1. Embedding 生成服务

- [x] 1.1 创建 app/services/kb_service.py — build_embedding_text() 函数和 batch_generate_embeddings() 批量处理函数
- [x] 1.2 单元验证：build_embedding_text 对有/无 summary 的条目正确拼接

## 2. 后台任务管理器

- [x] 2.1 创建 app/services/kb_task_manager.py — KBTask 数据类、内存任务存储、run_incremental/run_full_rebuild 异步任务函数
- [x] 2.2 实现任务互斥（同时只允许一个运行中任务）和进度更新

## 3. 知识库 API

- [x] 3.1 创建 app/api/kb.py — GET /api/kb/stats 统计端点
- [x] 3.2 实现 POST /api/kb/search 语义搜索端点
- [x] 3.3 实现 POST /api/kb/tasks 创建任务端点（202 + task_id）
- [x] 3.4 实现 GET /api/kb/tasks/{task_id} 进度查询端点
- [x] 3.5 在 app/main.py 中注册 kb_router

## 4. 采集自动化改造

- [x] 4.1 在 collector.py 中添加 _enrich_embeddings() 函数，采集后自动为全部新条目生成 embedding
- [x] 4.2 修改 _enrich_ai_keywords() 取消前 10 条限制，改为全覆盖

## 5. 知识库管理前端

- [x] 5.1 创建 KnowledgeBaseView.vue — 概览统计面板（总量/已索引/覆盖率/按源分布表格）
- [x] 5.2 实现语义搜索功能（搜索框 + 结果列表 + 相似度分数）
- [x] 5.3 实现构建操作（增量更新/全量重建按钮 + 确认对话框 + 进度条轮询）
- [x] 5.4 添加 /knowledge-base 路由和导航栏"知识库"按钮

## 6. 部署验证

- [x] 6.1 Docker 构建部署 app + frontend
- [x] 6.2 E2E 验证：stats API → 增量构建任务 → 进度查询 → 前端页面
