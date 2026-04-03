## ADDED Requirements

### 需求:Source 模型扩展
系统必须在 `sources` 表中包含以下字段：`type`（VARCHAR(20)，默认 'rsshub'）、`route`（VARCHAR(200)，默认 ''）、`url`（VARCHAR(500)，默认 ''）、`schedule`（VARCHAR(50)，默认 '*/10 * * * *'）、`max_items`（INTEGER，默认 30）。这些字段与现有的 `name`、`display_name`、`category`、`status`、`last_collected_at`、`created_at` 共同构成完整的源配置。

#### 场景:启动时自动迁移
- **当** 应用启动且 `sources` 表缺少新字段时
- **那么** 系统必须自动添加缺失的列并从 `sources.yaml` 回填现有记录的新字段值

#### 场景:新字段不覆盖已修改记录
- **当** 应用启动且 DB 中某源的 `schedule` 字段已有非默认值时
- **那么** 系统禁止用 YAML 中的值覆盖该字段

### 需求:Source CRUD API
系统必须提供以下 REST 端点来管理源：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/sources | 列表（含完整配置字段） |
| GET | /api/sources/{id} | 单个源详情 |
| POST | /api/sources | 新增源 |
| PUT | /api/sources/{id} | 修改源 |
| DELETE | /api/sources/{id} | 删除源 |

#### 场景:获取源列表
- **当** 客户端发送 `GET /api/sources` 请求
- **那么** 系统必须返回所有源（包括 disabled 状态），每个源包含 id、name、display_name、type、route、url、category、schedule、max_items、status、last_collected_at、created_at

#### 场景:新增 RSSHub 源
- **当** 客户端发送 `POST /api/sources`，body 包含 `{ name, display_name, type: "rsshub", route, category, schedule, max_items }`
- **那么** 系统必须创建新源记录，status 设为 `pending`，并返回完整源对象

#### 场景:新增外部 RSS 源
- **当** 客户端发送 `POST /api/sources`，body 包含 `{ name, display_name, type: "rss", url, category, schedule, max_items }`
- **那么** 系统必须创建新源记录，status 设为 `pending`，并返回完整源对象

#### 场景:name 唯一性校验
- **当** 客户端新增源的 name 与已有源重复时
- **那么** 系统必须返回 409 Conflict 错误

#### 场景:修改源
- **当** 客户端发送 `PUT /api/sources/{id}` 修改源配置
- **那么** 系统必须更新 DB 记录并返回更新后的完整源对象

#### 场景:修改不存在的源
- **当** 客户端发送 `PUT /api/sources/{id}`，id 不存在
- **那么** 系统必须返回 404 Not Found

### 需求:软删除机制
系统必须实现源的软删除。删除操作将 status 设为 `disabled`，保留所有关联的 `hot_items` 数据。仅当源处于 `pending` 状态且无关联 `hot_items` 时，允许物理删除。

#### 场景:软删除 active 源
- **当** 客户端发送 `DELETE /api/sources/{id}`，该源 status 为 `active`
- **那么** 系统必须将该源 status 设为 `disabled`，不删除 DB 记录

#### 场景:物理删除 pending 无数据源
- **当** 客户端发送 `DELETE /api/sources/{id}`，该源 status 为 `pending` 且无关联 hot_items
- **那么** 系统必须物理删除该 DB 记录

#### 场景:软删除 pending 有数据源
- **当** 客户端发送 `DELETE /api/sources/{id}`，该源 status 为 `pending` 但有关联 hot_items
- **那么** 系统必须将该源 status 设为 `disabled`，不物理删除

### 需求:预览测试接口
系统必须提供 `POST /api/sources/test` 端点，接收 `{ type, route, url, max_items }` 参数，临时创建 Spider 执行抓取，返回结果列表。该操作禁止写入 DB。

#### 场景:预览 RSSHub 源
- **当** 客户端发送 `POST /api/sources/test`，body 为 `{ type: "rsshub", route: "/v2ex/topics/hot", max_items: 5 }`
- **那么** 系统必须创建临时 RSSSpider 发起抓取，返回 `{ success: true, items: [...], count: N, elapsed_ms: M }` 或 `{ success: false, error: "..." }`

#### 场景:预览外部 RSS 源
- **当** 客户端发送 `POST /api/sources/test`，body 为 `{ type: "rss", url: "https://example.com/feed", max_items: 5 }`
- **那么** 系统必须创建临时 RSSSpider 发起抓取并返回结果

### 需求:立即采集
系统必须提供 `POST /api/sources/{id}/collect` 端点，对指定源立即执行一次采集（复用现有 `collect_source` 逻辑）。

#### 场景:立即采集 active 源
- **当** 客户端发送 `POST /api/sources/{id}/collect`，该源 status 为 `active` 或 `pending`
- **那么** 系统必须立即执行该源的采集流程并返回采集结果摘要

#### 场景:立即采集 disabled 源
- **当** 客户端发送 `POST /api/sources/{id}/collect`，该源 status 为 `disabled`
- **那么** 系统必须返回 400 Bad Request，提示源已禁用

### 需求:分类列表接口
系统必须提供 `GET /api/sources/categories` 端点，返回去重的分类列表，包含所有 `sources` 表中已存在的 category 值。

#### 场景:获取分类列表
- **当** 客户端发送 `GET /api/sources/categories`
- **那么** 系统必须返回去重排序的分类字符串数组
