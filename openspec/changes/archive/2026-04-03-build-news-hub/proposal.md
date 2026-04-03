## 为什么

目前获取各大平台热点信息需要逐个访问不同网站，效率低下且容易遗漏。虽然存在 tophub.today 等聚合站点，但它们缺少历史溯源、AI 摘要、趋势分析和个性化推荐等深度功能。构建一个自用的热点聚合系统，既能解决信息获取效率问题，又是学习 Python 全栈开发（FastAPI + Vue 3）和本地 AI 推理的绝佳实践项目。

## 变更内容

构建一个基于 Docker 部署的热点信息聚合系统（NewsHub），以 RSSHub 为核心数据源，聚合微博、知乎、百度、B站、今日头条、澎湃等主流平台的热榜数据，按来源分站存储以便溯源，并逐步加入全文搜索、AI 摘要、趋势分析与个性化推荐功能。

新增功能清单：

- 基于 RSSHub 的多源数据采集系统（定时调度、去重、分站存储）
- FastAPI 后端 REST API 提供热榜数据查询
- Vue 3 + Naive UI 前端展示（分类浏览、暗黑模式）
- PostgreSQL 全文搜索与历史数据浏览
- 本地 Ollama (Qwen2.5) AI 摘要生成
- 跨平台趋势分析与话题聚合
- 基于阅读历史的个性化推荐

## 功能 (Capabilities)

### 新增功能

- `data-collection`: 多源数据采集与存储。包括 RSSHub 集成、定时调度、去重策略、YAML 配置驱动的数据源管理、按来源分类存储。
- `hot-items-api`: 热榜数据查询 API。提供按来源/分类/时间查询热榜条目的 RESTful 接口，支持分页、排序和过滤。
- `frontend-dashboard`: 前端热榜展示面板。基于 Vue 3 + Naive UI + ECharts 的信息聚合展示界面，支持分类浏览、暗黑模式切换、实时更新。
- `full-text-search`: 全文搜索与历史浏览。基于 PostgreSQL 的热榜条目全文搜索，以及历史热榜快照的回溯查看功能。
- `ai-summary`: AI 辅助摘要生成。基于本地 Ollama + Qwen2.5 模型对热榜条目生成智能摘要和关键词提取。
- `trend-analysis`: 跨平台趋势分析。追踪话题在多平台间的传播路径、热度变化曲线和爆发预测。
- `personalized-feed`: 个性化推荐。基于用户分类偏好和阅读历史，利用 Embedding 向量相似度进行个性化内容排序。

### 修改功能

（无现有功能需要修改）

## 影响

- **新项目**：全部为新增代码，无现有代码受影响
- **基础设施**：需要 Docker Compose 编排 PostgreSQL、RSSHub、Ollama、Nginx 等容器
- **外部依赖**：RSSHub 开源项目（数据源）、Ollama（AI 推理）、各平台的公开热榜接口
- **硬件要求**：本地 AI 推理需要 NVIDIA GPU（RTX 4090，24GB VRAM），非 AI 功能无特殊硬件要求
- **分阶段交付**：Phase 1（基础采集展示）→ Phase 2（搜索+历史）→ Phase 3（AI 增强）→ Phase 4（趋势+推荐）
