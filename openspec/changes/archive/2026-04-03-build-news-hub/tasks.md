## 1. 项目初始化与基础设施

- [x] 1.1 创建项目根目录结构（app/、frontend/、data/ 等）
- [x] 1.2 创建 requirements.txt，添加核心依赖（fastapi、uvicorn、sqlalchemy、alembic、psycopg2-binary、httpx、feedparser、apscheduler、pydantic-settings）
- [x] 1.3 创建 Dockerfile（Python 应用镜像）
- [x] 1.4 创建 docker-compose.yml（FastAPI + PostgreSQL + RSSHub + Nginx）
- [x] 1.5 配置 Nginx 反向代理（/ 指向前端静态文件，/api/* 反代 FastAPI）
- [x] 1.6 创建 .env 文件和 app/config.py（数据库连接、RSSHub 地址等配置项管理）

## 2. 数据库与数据模型

- [x] 2.1 创建 app/db/database.py（SQLAlchemy 异步引擎和会话管理）
- [x] 2.2 创建 app/models/hot_item.py（hot_items 表模型：source、title、url、rank、hot_value、category、raw_data、collected_at 等字段）
- [x] 2.3 创建 app/models/source.py（数据源元信息模型）
- [x] 2.4 配置 Alembic 数据库迁移，生成初始迁移脚本
- [x] 2.5 创建 source + collected_at 复合索引

## 3. 数据采集核心

- [x] 3.1 创建 app/spiders/sources.yaml（首批 6 站配置：微博、知乎、百度、B站、今日头条、澎湃）
- [x] 3.2 创建 app/spiders/base.py（采集器基类，定义统一的 fetch 接口和返回数据结构）
- [x] 3.3 创建 app/spiders/rss_spider.py（RSS 通用采集器：调用 RSSHub、解析 RSS/Atom XML、提取条目信息）
- [x] 3.4 创建 app/services/collector.py（采集编排服务：加载 sources.yaml、调用对应 Spider、处理结果入库）
- [x] 3.5 创建 app/services/dedup.py（去重逻辑：URL + source 去重，排名/热度值更新）
- [x] 3.6 创建 app/scheduler/jobs.py（APScheduler 定时任务注册，根据 sources.yaml 的 cron 表达式调度）
- [x] 3.7 在 FastAPI 启动事件中初始化调度器并启动采集任务

## 4. 后端 API

- [x] 4.1 创建 app/main.py（FastAPI 应用入口、CORS 配置、路由注册）
- [x] 4.2 创建 app/api/hot.py（GET /api/hot — 全部热榜、GET /api/hot/{source} — 按来源查询、category 过滤、分页）
- [x] 4.3 创建 app/api/sources.py（GET /api/sources — 数据源元信息列表，含最后采集时间和状态）
- [x] 4.4 创建 Pydantic 响应模型（HotItemResponse、SourceResponse、PaginatedResponse）

## 5. 前端基础搭建

- [x] 5.1 使用 Vite 初始化 Vue 3 项目（frontend/ 目录）
- [x] 5.2 安装 Naive UI、vue-router、pinia、axios 依赖
- [x] 5.3 配置 Vite 开发代理（/api 代理到 FastAPI :8000）
- [x] 5.4 创建基础布局组件（Header + 分类标签栏 + 主内容区）
- [x] 5.5 实现暗黑模式切换功能（Naive UI ConfigProvider + localStorage 持久化）

## 6. 前端热榜展示

- [x] 6.1 创建热榜卡片组件（HotCard.vue：来源名称、条目列表、热度值、更新时间）
- [x] 6.2 创建首页视图（HomeView.vue：调用 API 获取数据、按分类过滤、卡片网格布局）
- [x] 6.3 实现分类标签页切换逻辑（全部/综合/科技/娱乐/新闻等）
- [x] 6.4 实现自动刷新功能（定时拉取最新数据，平滑更新）
- [x] 6.5 实现响应式布局（桌面 3-4 列、平板 2 列、手机单列）
- [x] 6.6 创建前端 Dockerfile（多阶段构建：Vite build → Nginx 托管静态文件）

## 7. 集成测试与部署验证

- [x] 7.1 编写采集器单元测试（RSS 解析、去重逻辑）
- [x] 7.2 编写 API 端点测试（FastAPI TestClient）
- [x] 7.3 docker-compose up 全链路验证（RSSHub → 采集 → 数据库 → API → 前端展示）
- [x] 7.4 添加第二波站点配置（36氪、IT之家、GitHub Trending、HackerNews）

## 8. Phase 2 — 搜索与历史浏览

- [x] 8.1 为 hot_items.title 添加 PostgreSQL 全文搜索索引（tsvector + GIN 索引）
- [x] 8.2 创建 app/api/search.py（GET /api/search — 关键词搜索，支持来源和时间范围过滤）
- [x] 8.3 创建 app/api/history.py（GET /api/history/{source}/{date} — 历史快照查询）
- [x] 8.4 前端创建搜索页面（搜索框、结果列表、来源/时间过滤器）
- [x] 8.5 前端创建历史浏览页面（日历选择器 + 来源选择 + 历史热榜快照展示）

## 9. Phase 3 — AI 摘要与关键词

- [x] 9.1 在 docker-compose.yml 中添加 Ollama 容器（GPU passthrough 配置）
- [x] 9.2 创建 app/services/ai/llm_client.py（统一 LLM 客户端，兼容 OpenAI API 格式，支持本地/云端切换）
- [x] 9.3 创建 app/services/ai/summarizer.py（调用 LLM 生成热榜摘要，批量模式 + 按需模式）
- [x] 9.4 创建 app/services/ai/keyword_extractor.py（从标题中提取关键词标签）
- [x] 9.5 为 hot_items 表添加 summary 和 keywords 字段（Alembic 迁移）
- [x] 9.6 在采集流程中集成摘要生成（Top N 条目自动生成）
- [x] 9.7 前端热榜卡片中展示 AI 摘要（展开/折叠交互）
- [x] 9.8 前端添加"生成摘要"按钮（按需触发）

## 10. Phase 4 — 趋势分析

- [x] 10.1 创建 app/services/ai/embedder.py（调用 bge-m3 模型生成文本 Embedding）
- [x] 10.2 安装 pgvector 扩展，为 hot_items 表添加 embedding 向量字段
- [x] 10.3 创建 app/services/trending.py（话题聚合：基于关键词重叠和 Embedding 相似度）
- [x] 10.4 创建 app/services/burst_detector.py（热点爆发检测：热度急升或多平台同时出现）
- [x] 10.5 创建 app/api/trends.py（GET /api/trends — 趋势数据、爆发话题列表、热度曲线数据）
- [x] 10.6 安装 vue-echarts，创建趋势分析前端页面（热度曲线图、跨平台对比图、爆发话题列表）

## 11. Phase 4 — 个性化推荐

- [x] 11.1 前端实现分类偏好设置功能（设置页面 + localStorage 存储）
- [x] 11.2 前端实现阅读历史记录（点击事件记录 + 历史页面展示）
- [x] 11.3 创建 app/api/recommend.py（GET /api/recommend — 基于用户兴趣向量做 pgvector 近邻查询）
- [x] 11.4 实现冷启动推荐逻辑（无历史时按偏好分类推荐热门条目）
- [x] 11.5 前端创建"为你推荐"模块（推荐列表 + 推荐理由展示）
