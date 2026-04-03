# NewsHub - 智能新闻聚合与分析平台

NewsHub 是一个基于 AI 的智能新闻聚合与分析平台，自动从 20+ RSS 信息源采集热点资讯，并利用大语言模型（LLM）进行摘要生成、关键词提取、趋势分析和智能问答。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| **热点聚合** | 自动采集 V2EX、B站、36氪、澎湃新闻、HackerNews 等 20+ 信息源的热点内容 |
| **AI 摘要** | 使用 LLM 对新闻内容进行智能摘要和关键词提取 |
| **智能简报** | 自动生成每日/按源/按主题/自定义简报，支持公开分享 |
| **语义搜索** | 基于 pgvector 向量数据库的全文搜索 + 语义搜索 |
| **趋势分析** | 跨源热点趋势检测、突发事件识别、相似内容发现 |
| **RAG 对话** | 基于检索增强生成（RAG）的智能问答，流式响应 |
| **知识库** | 对采集内容建立向量索引，支持语义检索 |
| **信息源管理** | 可视化管理 RSS 信息源，支持调度配置和批量操作 |
| **多 AI 后端** | 支持 OpenAI、Ollama、自定义 API 等多种 LLM 提供商 |
| **用量监控** | AI API 调用统计与成本分析 |

## 🏗️ 技术栈

### 后端
- **框架**: FastAPI（异步）
- **数据库**: PostgreSQL + pgvector（向量存储）
- **ORM**: SQLAlchemy 2.0（async）
- **迁移**: Alembic
- **调度**: APScheduler
- **AI SDK**: OpenAI Python SDK

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI 组件库**: Naive UI
- **状态管理**: Pinia
- **图表**: ECharts / vue-echarts
- **路由**: Vue Router

## 🎨 前端页面分层

前端采用双壳结构，将内容阅读与后台工具明确分离：

- **前台阅读壳**：`/`、`/search`、`/history`、`/trends`、`/recommend`、`/share/:token`
- **后台工具壳**：`/chat`、`/briefings`、`/knowledge-base`、`/sources`、`/logs`、`/settings`

路由通过 `meta.layout` 指定页面归属：

- `front`：前台阅读壳
- `admin`：后台工具壳
- `minimal`：最小壳（仅渲染页面）

全局设计令牌与主题变量位于 `frontend/src/styles/theme.css`，用于统一前后台的色板、圆角、间距和状态反馈。

### 基础设施
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **RSS 服务**: RSSHub
- **LLM**: Ollama（本地）/ OpenAI（云端）

## 📁 项目结构

```
├── app/                    # 后端应用
│   ├── api/                # API 路由（13 个模块，50+ 接口）
│   ├── db/                 # 数据库配置与迁移
│   ├── models/             # SQLAlchemy 模型
│   ├── scheduler/          # 定时任务调度
│   ├── services/           # 业务逻辑服务
│   │   └── ai/             # AI 相关服务（LLM、Embedding、摘要等）
│   ├── spiders/            # 爬虫与 RSS 采集
│   └── utils/              # 工具函数
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # API 请求封装
│   │   ├── components/     # 公共组件
│   │   ├── views/          # 页面视图（12 个页面）
│   │   ├── stores/         # Pinia 状态管理
│   │   └── router/         # 路由配置
│   └── Dockerfile
├── nginx/                  # Nginx 反向代理配置
├── tests/                  # 测试
├── docker-compose.yml      # Docker 编排
├── Dockerfile              # 后端 Dockerfile
├── requirements.txt        # Python 依赖
└── alembic.ini             # 数据库迁移配置
```

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- （可选）Ollama - 本地 LLM 推理

### 1. 克隆仓库

```bash
git clone https://github.com/<your-username>/news-hub.git
cd news-hub
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下变量：

```env
# 数据库
POSTGRES_USER=newshub
POSTGRES_PASSWORD=newshub123
POSTGRES_DB=newshub

# AI 配置（可选，可在 Web UI 中配置）
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

### 3. 启动服务

```bash
docker compose up -d
```

服务启动后：
- **前端界面**: http://localhost
- **后端 API**: http://localhost:8888
- **API 文档**: http://localhost:8888/docs
- **RSSHub**: http://localhost:1200

### 4. （可选）安装 Ollama 并下载模型

如果使用本地 LLM 推理：

```bash
# 安装 Ollama 后
ollama pull qwen2.5:7b
```

## 🔧 开发环境

### 后端开发

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8888
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

### 运行测试

```bash
pytest
```

## 📡 API 概览

| 路由 | 说明 |
|------|------|
| `GET /api/hot` | 获取热点资讯（按来源分组） |
| `GET /api/search` | 全文搜索 + 语义搜索 |
| `GET /api/history/{source}/{date}` | 历史快照 |
| `CRUD /api/sources` | 信息源管理 |
| `CRUD /api/briefings` | 智能简报管理 |
| `POST /api/briefings/{id}/generate` | 生成简报内容 |
| `POST /api/chat/sessions` | 创建对话会话 |
| `POST /api/chat/sessions/{id}/messages` | 发送消息（流式） |
| `GET /api/kb/stats` | 知识库统计 |
| `POST /api/kb/search` | 语义搜索 |
| `GET /api/trends` | 趋势分析 |
| `GET /api/ai-config` | AI 配置管理 |
| `GET /api/share/{token}` | 公开分享简报 |

完整 API 文档请访问 `/docs`（Swagger UI）。

## 📰 内置信息源

| 分类 | 信息源 |
|------|--------|
| 综合 | V2EX、酷安、财联社 |
| 娱乐 | B 站热门、豆瓣电影 |
| 新闻 | 澎湃新闻、联合早报、IT之家 |
| 科技 | 36氪、少数派、HackerNews、华尔街见闻 |

信息源可在 Web UI 中自由管理，也可通过编辑 `app/spiders/sources.yaml` 批量配置。

## 🐳 Docker 服务

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| `app` | 自构建 | 8888 | FastAPI 后端 |
| `db` | pgvector/pgvector:pg16 | 5432 | PostgreSQL + pgvector |
| `rsshub` | diygod/rsshub | 1200 | RSS 订阅服务 |
| `frontend` | 自构建 | 80 | Vue 3 前端 |

## 📄 License

MIT
