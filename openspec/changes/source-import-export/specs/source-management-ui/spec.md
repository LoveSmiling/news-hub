## ADDED Requirements

### Requirement: 导出源按钮
源管理页面工具栏必须包含"导出"按钮，点击后调用 `GET /api/sources/export` 触发 JSON 文件下载。

#### Scenario: 点击导出
- **WHEN** 用户点击工具栏的"导出"按钮
- **THEN** 浏览器必须下载包含所有源配置的 JSON 文件

### Requirement: 导入源按钮和对话框
源管理页面工具栏必须包含"导入"按钮。点击后必须打开导入对话框，包含文件选择器（只接受 .json 文件）。选择文件后必须显示预览信息（即将导入的源数量）。用户确认后调用 `POST /api/sources/import` 执行导入。

#### Scenario: 打开导入对话框
- **WHEN** 用户点击工具栏的"导入"按钮
- **THEN** 系统必须弹出导入对话框，包含文件选择器

#### Scenario: 选择文件后显示预览
- **WHEN** 用户选择了一个合法的 JSON 文件
- **THEN** 对话框必须显示"即将导入 N 个源"的预览信息

#### Scenario: 选择非法文件
- **WHEN** 用户选择的文件不是合法的源导出 JSON（缺少 version 或 sources 字段）
- **THEN** 对话框必须显示格式错误提示

#### Scenario: 确认导入显示结果
- **WHEN** 用户确认导入且操作完成
- **THEN** 对话框必须显示导入结果（新增 N 个，更新 N 个，失败 N 个），关闭后刷新源列表
