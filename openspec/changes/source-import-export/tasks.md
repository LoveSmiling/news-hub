## 1. 后端 Schema

- [x] 1.1 在 `app/api/schemas.py` 中新增导出响应模型（SourceExportItem, SourceExportResponse）和导入请求/响应模型（SourceImportRequest, SourceImportResponse, SourceImportError）

## 2. 后端 API 端点

- [x] 2.1 在 `app/api/sources.py` 中实现 `GET /api/sources/export` 端点：查询所有源，组装 JSON，返回文件下载响应
- [x] 2.2 在 `app/api/sources.py` 中实现 `POST /api/sources/import` 端点：校验输入，按 name 匹配执行更新或新增，同步调度器，返回操作结果

## 3. 前端 API 层

- [x] 3.1 在 `frontend/src/api/index.ts` 中新增 `exportSources()` 函数（触发文件下载）和 `importSources(data)` 函数（POST JSON body）

## 4. 前端 UI

- [x] 4.1 在 `frontend/src/views/SourcesView.vue` 工具栏区域添加"导出"和"导入"按钮
- [x] 4.2 实现导入对话框：文件选择器（.json）、预览信息、格式校验、确认按钮
- [x] 4.3 实现导入结果展示和列表刷新逻辑
