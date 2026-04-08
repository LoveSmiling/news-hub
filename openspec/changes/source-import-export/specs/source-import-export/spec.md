## ADDED Requirements

### Requirement: 导出全部源配置
系统必须提供 `GET /api/sources/export` 端点，将数据库中所有源的配置导出为 JSON 文件下载。导出格式必须包含 `version`（整数，初始值 1）、`exported_at`（ISO 8601 时间戳）和 `sources` 数组。每个源对象必须包含字段：`name`, `display_name`, `category`, `type`, `route`, `url`, `schedule`, `max_items`, `status`。不得包含 `id`, `last_collected_at`, `created_at`。响应必须设置 `Content-Disposition: attachment; filename=sources_export_YYYYMMDD.json` 头。

#### Scenario: 导出所有源
- **WHEN** 客户端请求 `GET /api/sources/export`
- **THEN** 系统必须返回包含所有源配置的 JSON 文件，Content-Type 为 `application/json`，Content-Disposition 为 attachment

#### Scenario: 导出空数据库
- **WHEN** 数据库中没有源且客户端请求 `GET /api/sources/export`
- **THEN** 系统必须返回 JSON 文件，`sources` 数组为空

### Requirement: 批量导入源配置
系统必须提供 `POST /api/sources/import` 端点，接收 JSON body 包含 `version` 和 `sources` 数组。系统必须按以下逻辑处理每个源：按 `name` 字段查找数据库中是否存在该源，存在则更新其配置字段（`display_name`, `category`, `type`, `route`, `url`, `schedule`, `max_items`, `status`），不存在则新增。数据库中有但导入文件中没有的源不做任何处理。

#### Scenario: 导入新增源
- **WHEN** 导入的 JSON 中包含 name 为 "new-source" 的源且数据库中不存在该 name
- **THEN** 系统必须创建新的源记录，返回结果中 `created` 计数加 1

#### Scenario: 导入更新已有源
- **WHEN** 导入的 JSON 中包含 name 为 "v2ex" 的源且数据库中已存在该 name
- **THEN** 系统必须更新该源的配置字段，返回结果中 `updated` 计数加 1

#### Scenario: 导入保留未涉及的源
- **WHEN** 数据库中存在源 A、B、C，导入文件只包含 B 和 D
- **THEN** 源 A 和 C 不受影响，B 被更新，D 被新增

#### Scenario: 导入数据校验失败
- **WHEN** 导入的某个源缺少必填字段（如 name 或 display_name）
- **THEN** 该源必须跳过，错误信息记录在响应的 `errors` 数组中，包含 `name` 和 `error` 字段

### Requirement: 导入响应格式
`POST /api/sources/import` 的响应体必须包含：`created`（新增数量，整数）、`updated`（更新数量，整数）、`errors`（错误列表，每项包含 `name` 和 `error` 字段）。

#### Scenario: 导入成功无错误
- **WHEN** 导入 5 个源，其中 2 个新增、3 个更新、0 个错误
- **THEN** 响应必须为 `{"created": 2, "updated": 3, "errors": []}`

#### Scenario: 导入部分失败
- **WHEN** 导入 3 个源，其中 1 个校验失败
- **THEN** 响应必须包含正确的 created/updated 计数和 errors 数组

### Requirement: 导入同步调度器
导入源后，系统必须同步更新调度器。对新增的 active 状态源必须注册调度任务。对更新的源如果 schedule 或 status 发生变化，必须重新注册或移除调度任务。

#### Scenario: 新增 active 源注册调度
- **WHEN** 导入新增一个 status 为 "active" 的源
- **THEN** 系统必须为该源注册调度任务

#### Scenario: 更新源 schedule 变化
- **WHEN** 导入更新一个源且其 schedule 值与数据库中不同
- **THEN** 系统必须用新的 schedule 重新注册该源的调度任务

#### Scenario: 更新源从 active 变为 disabled
- **WHEN** 导入更新一个源使其 status 从 "active" 变为 "disabled"
- **THEN** 系统必须移除该源的调度任务
