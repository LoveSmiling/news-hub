# kb-api 规范

## 目的
待定 - 由归档变更 knowledge-base 创建。归档后请更新目的。
## 需求
### 需求:知识库统计
系统必须提供 GET /api/kb/stats 端点，返回知识库概览统计。

#### 场景:获取统计信息
- **当** GET /api/kb/stats
- **那么** 返回 {"total": 2159, "indexed": 1800, "coverage_pct": 83.4, "by_source": [{"source": "cls", "total": 874, "indexed": 800}, ...]}

### 需求:语义搜索
系统必须提供 POST /api/kb/search 端点，基于向量相似度搜索知识库。

#### 场景:语义搜索
- **当** POST /api/kb/search body={"query": "AI手机", "limit": 20}
- **那么** 对 query 生成 embedding，在 hot_items 中按 cosine_distance 排序，返回 {"items": [{"id", "title", "source", "url", "summary", "score", "has_embedding", "keywords", "collected_at"}]}

#### 场景:无索引数据
- **当** hot_items 中没有任何 embedding 数据时搜索
- **那么** 返回空列表 {"items": []}

### 需求:任务管理端点
系统必须提供 POST /api/kb/tasks 和 GET /api/kb/tasks/{task_id} 端点（详见 kb-task-manager 规范）。

#### 场景:端点注册
- **当** 服务启动
- **那么** /api/kb/* 路由已注册并可访问

