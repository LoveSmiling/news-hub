## Context

当前源管理支持单条 CRUD 和批量启用/禁用/改分类/采集。启动时可从 `sources.yaml` 种子化。但缺少运行时的批量导出导入能力，多环境迁移和备份恢复操作不便。

后端使用 FastAPI + SQLAlchemy，源模型有 `name` 字段（unique）可作为导入匹配键。调度器通过 APScheduler 管理，现有新增/编辑端点已包含调度任务的注册/更新逻辑。

## Goals / Non-Goals

**Goals:**
- 一键导出全部源配置为 JSON 文件
- 上传 JSON 文件批量导入源，按 `name` 匹配：存在则覆盖更新，不存在则新增
- 导入时同步更新调度器任务
- 前端提供导出/导入按钮，导入有预览和结果反馈

**Non-Goals:**
- 不做"完全同步"（数据库有但文件中没有的源不删除）
- 不做增量导出（筛选条件导出部分源）
- 不做 YAML 格式支持
- 不做导入冲突的交互式逐条确认

## Decisions

### D1: 导出格式为 JSON，包含版本号

采用 JSON 格式，带 `version` 字段（初始值 1）和 `exported_at` 时间戳。JSON 前端原生支持，API 天然契合。

**备选方案**: YAML（与 sources.yaml 一致）—— 但前端处理需额外依赖，且导出/导入是运行时操作，JSON 更合适。

### D2: 导入通过 JSON body POST，不是 multipart 文件上传

前端读取文件内容后以 JSON body 发送 `POST /api/sources/import`。避免后端处理文件上传的复杂性，也便于 API 调试。

**备选方案**: multipart form-data 文件上传 —— 增加后端文件解析逻辑，对此场景无额外收益。

### D3: 用 `name` 字段作为匹配键

`name` 是 unique 字段，语义明确（如 "v2ex"、"36kr"），适合跨环境标识同一源。不通过 `id`（自增，跨环境不一致）。

### D4: 导出字段范围

导出：`name`, `display_name`, `category`, `type`, `route`, `url`, `schedule`, `max_items`, `status`。
不导出：`id`, `last_collected_at`, `created_at`（运行时数据）。

### D5: 导入后同步调度器

复用现有调度注册逻辑。对新增的 active 源注册调度任务，对更新的源如果 schedule 或 status 变化则重新注册/移除调度任务。

### D6: 导出端点返回文件下载响应

`GET /api/sources/export` 返回 `application/json` 内容，设置 `Content-Disposition: attachment` 头触发浏览器下载。文件名包含日期：`sources_export_YYYYMMDD.json`。

## Risks / Trade-offs

- **大量源导入性能** → 使用数据库事务批量处理，单次提交。当前源数量级（几十到几百）不构成问题。
- **导入文件格式错误** → 后端做 schema 校验，返回具体错误信息。
- **并发导入冲突** → 不做特殊处理，依赖数据库 unique 约束。同一时间不太可能有多人同时导入。
- **调度器同步失败** → 数据先写入成功，调度器如果部分失败记录到错误列表但不回滚数据。
