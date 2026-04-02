## 新增需求

### 需求:简报列表API
系统必须提供 `GET /api/briefings` 端点，返回分页的简报列表。

#### 场景:默认查询
- **当** 不带参数请求时
- **那么** 必须返回最近 50 条简报，按 `created_at` 降序排列，每条包含 id, title, brief_type, status, token_usage, created_at, completed_at

#### 场景:按类型过滤
- **当** 请求带 `type=daily` 参数时
- **那么** 必须仅返回 `brief_type` 为 daily 的简报

#### 场景:按状态过滤
- **当** 请求带 `status=done` 参数时
- **那么** 必须仅返回已完成的简报

### 需求:简报详情API
系统必须提供 `GET /api/briefings/{id}` 端点，返回简报详情。

#### 场景:正常获取
- **当** 请求已存在的简报 ID 时
- **那么** 必须返回完整的简报信息，包含 content（Markdown 文本）和关联的 hot_item 信息（id, title, source, url）

#### 场景:不存在的ID
- **当** 请求不存在的简报 ID 时
- **那么** 必须返回 HTTP 404

### 需求:触发生成API
系统必须提供 `POST /api/briefings/generate` 端点，手动触发简报生成。

#### 场景:单来源生成
- **当** 请求 body 为 `{type: "source", source: "thepaper"}` 时
- **那么** 必须异步生成该来源的简报，立即返回简报记录（status=generating）

#### 场景:每日汇总
- **当** 请求 body 为 `{type: "daily"}` 时
- **那么** 必须异步生成当日跨来源汇总简报

#### 场景:主题生成
- **当** 请求 body 为 `{type: "topic", keyword: "AI", hours: 72}` 时
- **那么** 必须异步生成主题简报

#### 场景:自选条目
- **当** 请求 body 为 `{type: "custom", item_ids: [1,2,3], title: "我的报告"}` 时
- **那么** 必须异步生成自选条目简报

#### 场景:重复生成检查
- **当** 已有相同 scope_params 且 status 为 generating 的简报时
- **那么** 必须返回已有的简报记录而非创建新的

### 需求:删除简报API
系统必须提供 `DELETE /api/briefings/{id}` 端点，删除简报。

#### 场景:正常删除
- **当** 请求删除已存在的简报时
- **那么** 必须删除该简报及其关联的 briefing_items，返回 HTTP 200

#### 场景:不存在的ID
- **当** 请求删除不存在的简报时
- **那么** 必须返回 HTTP 404
