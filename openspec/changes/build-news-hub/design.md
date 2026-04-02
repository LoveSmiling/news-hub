## 上下文

这是一个全新项目，构建类似 tophub.today 的多源热点信息聚合系统。开发者具有 Java 背景，通过此项目学习 Python 全栈开发。本地拥有 RTX 4090 (24GB VRAM)，可运行本地 AI 模型。项目分 4 个阶段增量交付，全程 Docker Compose 部署。

## 目标 / 非目标

**目标：**

- 通过 Docker Compose 一键部署完整系统（采集 + API + 前端 + 数据库）
- 以 RSSHub 为核心数据源，实现稳定、低维护成本的多站点数据采集
- 按数据源分类存储，保留历史数据以支持溯源和趋势分析
- 提供现代化的前端展示界面，支持分类浏览和暗黑模式
- Phase 3+ 利用本地 GPU 实现 AI 摘要、语义搜索和个性化推荐

**非目标：**

- 不做商用级高可用或水平扩展设计（自用项目）
- 不自建复杂的反爬对抗系统（依赖 RSSHub 社区维护）
- 不做移动端 APP（Web 响应式即可）
- 不做用户注册/多用户系统（单用户自用）
- 不追求所有站点全覆盖（优先做主流平台，逐步扩展）

## 决策

### 1. 后端框架：FastAPI

**选择**：FastAPI + Uvicorn

**考虑过的替代**：
- Django：全家桶太重，自带 Admin 用不上，异步支持较晚
- Flask：异步支持弱，大了以后缺乏结构

**理由**：
- 异步原生，适合并发抓取多个 RSS Feed
- 自动生成 Swagger API 文档，前后端联调方便
- Pydantic 类型校验机制与 Java DTO 思路相似，降低学习曲线
- 轻量、启动快、Docker 镜像小

### 2. 数据库：PostgreSQL

**选择**：PostgreSQL 16 + 未来 pgvector 扩展

**考虑过的替代**：
- SQLite：并发写入受限，不适合定时采集 + API 同时读写
- MongoDB：灵活但查询能力不如 PG，全文搜索需额外配置
- 按站点分库 SQLite：跨站查询困难

**理由**：
- 统一表 `hot_items` + `source` 字段，兼顾查询灵活性和溯源需求
- 原生全文搜索 (tsvector/tsquery) 可覆盖 Phase 2 搜索需求
- pgvector 扩展可在同一数据库内支持 Phase 4 语义搜索
- JSONB 字段存储各站点差异化的原始数据，避免 schema 僵化
- 成熟可靠，Docker 部署简单

### 3. 数据采集：RSSHub 为主

**选择**：自建 RSSHub 实例 + 标准 RSS/Atom 解析

**考虑过的替代**：
- 自写全套爬虫：维护成本高，反爬对抗复杂
- 直接调用 tophub.today API：依赖第三方服务稳定性
- 纯官方 API：覆盖面不够

**理由**：
- RSSHub 社区维护 1000+ 路由，反爬由社区持续更新
- 输出标准 RSS/Atom 格式，解析代码统一且简单
- Docker 一键部署，与主应用在同一 Compose 网络
- 不够的站点可通过自定义 Spider 补充（fallback 策略）

### 4. 前端：Vue 3 + Naive UI

**选择**：Vue 3 + Vite + Naive UI + ECharts

**考虑过的替代**：
- React/Next.js：功能同等强大但中文生态不如 Vue
- Jinja2 + HTMX：上手快但交互天花板低，无法满足后期趋势图表需求
- Element Plus：设计偏传统后台管理风格

**理由**：
- Vue 模板语法直观，适合 Java 背景开发者入门
- Naive UI 设计现代、暗黑模式原生支持、主题定制灵活
- ECharts 为未来趋势分析可视化提供强大图表能力
- Vite 构建快速，开发体验好
- 构建产物为纯静态文件，Nginx 直接托管

### 5. AI 推理：本地 Ollama

**选择**：Ollama + Qwen2.5-14B (摘要) + bge-m3 (Embedding)

**考虑过的替代**：
- 云端 API (OpenAI/DeepSeek)：有成本，需网络
- vLLM：配置复杂，适合生产环境
- LocalAI：社区不如 Ollama 活跃

**理由**：
- 本地 RTX 4090 24GB 显存可轻松运行 14B 模型
- Ollama API 兼容 OpenAI 格式，代码可无缝切换本地/云端
- Docker 部署，GPU passthrough 配置成熟
- Qwen2.5-14B 中文能力强，适合中文热榜摘要
- bge-m3 多语言 Embedding 模型，支持中英文语义搜索

### 6. 调度器：APScheduler

**选择**：APScheduler (AsyncIOScheduler)

**考虑过的替代**：
- Celery + Redis：对单节点项目过重
- 系统 cron：不够灵活，无法热更新

**理由**：
- 内嵌在 FastAPI 进程中，不需要额外服务
- 支持 cron 表达式，与 sources.yaml 配置自然映射
- 异步兼容 FastAPI 的事件循环

### 7. 数据源配置：声明式 YAML

**选择**：`sources.yaml` 配置文件驱动

**理由**：
- 新增站点只需添加 YAML 配置，无需改代码
- 可实现运行时热加载
- 每个源独立调度频率、分类、展示名等

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Compose                         │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │  Nginx   │  │ FastAPI  │  │ RSSHub   │  │Postgres│  │
│  │  :80     │  │  :8000   │  │  :1200   │  │ :5432  │  │
│  │ 前端静态 │  │ API+调度 │  │ 数据采集 │  │ 数据库 │  │
│  └────┬─────┘  └────┬─────┘  └──────────┘  └────────┘  │
│       │             │                                    │
│       │        ┌────▼─────┐  (Phase 3+)                 │
│       │        │  Ollama  │                              │
│       │        │  :11434  │                              │
│       │        │ AI 推理  │                              │
│       │        └──────────┘                              │
│       │                                                  │
│  前端路由:                                               │
│  /          → Vue 静态文件                               │
│  /api/*     → 反代 FastAPI                               │
└─────────────────────────────────────────────────────────┘
```

## 数据模型核心表

```
hot_items
├── id              SERIAL PK
├── source          VARCHAR(50)     -- 'weibo', 'zhihu', ...
├── title           TEXT NOT NULL
├── url             TEXT NOT NULL
├── rank            INTEGER
├── hot_value       VARCHAR(100)    -- '5.2万讨论', '1.3亿阅读'
├── category        VARCHAR(50)     -- '综合', '科技', '娱乐'
├── summary         TEXT            -- AI 摘要 (Phase 3)
├── embedding       VECTOR(1024)    -- 文本向量 (Phase 4, pgvector)
├── raw_data        JSONB           -- 原始采集数据
├── collected_at    TIMESTAMP       -- 采集时间
├── created_at      TIMESTAMP       -- 入库时间
└── INDEX(source, collected_at DESC)  -- 按来源+时间溯源
```

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| RSSHub 路由失效（上游网站改版） | 监控采集成功率，失败时告警；社区通常几天内修复；关键站点准备 fallback 自定义 Spider |
| 单进程 APScheduler 可靠性 | 记录每次采集的状态和结果；异常自动重试；后期可迁移到 Celery |
| PostgreSQL 单点故障 | 定时备份数据卷；自用项目可接受短暂停机 |
| 数据量增长导致查询变慢 | 建立合理索引；按时间分区（如需要）；定期清理过旧数据（可配置保留天数） |
| Ollama 占用 GPU 显存影响其他任务 | Phase 3 才引入；设置显存上限；可随时 stop 容器释放 GPU |
| 前端学习成本（Vue 3 不熟悉） | Vue 中文文档完善；Naive UI 组件开箱即用减少手写量；Phase 1 页面简单 |
