## Why

当前源管理只能逐条增删改，缺少批量导出导入能力。用户在多环境迁移（开发→生产）、备份恢复、或批量调整源配置时，需要手动逐个操作，效率低下。需要一键导出全部源为 JSON 文件，并支持上传 JSON 文件一次性导入——按 `name` 匹配做覆盖更新和新增。

## What Changes

- 新增后端 `GET /api/sources/export` 端点，导出所有源配置为 JSON 文件下载
- 新增后端 `POST /api/sources/import` 端点，接收 JSON 数据执行批量导入（按 name 匹配：存在则更新，不存在则新增）
- 导入时同步更新调度器（新增源注册任务，更新源重新注册任务）
- 前端 SourcesView 工具栏新增"导出"和"导入"按钮
- 导入流程包含文件选择、预览确认、结果反馈

## Capabilities

### New Capabilities
- `source-import-export`: 源的批量导出（JSON 文件下载）和批量导入（JSON 上传，按 name 匹配做覆盖更新+新增），包含前后端完整交互

### Modified Capabilities
- `source-management-ui`: 工具栏新增导出/导入按钮及导入确认对话框

## Impact

- **后端 API**: `app/api/sources.py` 新增 2 个端点，`app/api/schemas.py` 新增请求/响应模型
- **前端 API**: `frontend/src/api/index.ts` 新增 2 个函数
- **前端 UI**: `frontend/src/views/SourcesView.vue` 新增按钮和对话框
- **调度器**: 导入触发调度任务的注册/更新
