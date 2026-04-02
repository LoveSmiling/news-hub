## 为什么

当前源配置分散在 `sources.yaml`（静态文件）和数据库 `sources` 表（仅存元信息）两处，新增或修改源需要手动编辑 YAML 文件并重新部署容器。缺少可视化的管理界面和运行时热更新能力，操作成本高且容易出错。需要一个完整的源管理页面，支持增删改查、预览测试和即时生效。

## 变更内容

- **扩展 Source 数据模型**：在 `sources` 表中增加 `type`、`route`、`url`、`schedule`、`max_items` 字段，使 DB 成为运行时唯一配置源
- **新增 CRUD API**：提供源的增删改查、预览测试、立即采集、批量操作等 REST 端点
- **软删除机制**：删除源时将状态设为 `disabled`（保留历史数据），仅 `pending` 且无关联数据的源可物理删除
- **Scheduler 热更新**：源的增删改操作后立即同步 APScheduler job，无需重启
- **自定义分类**：分类字段保持自由文本，前端使用可创建的下拉选择框（combo box），预置 `新闻/科技/娱乐/综合` 四个默认分类
- **批量操作**：支持批量启用、禁用、修改分类、立即采集
- **前端源管理页面**：包含表格列表、筛选、新增/编辑对话框、预览测试、批量操作栏
- **BriefingsView 动态化**：`sourceOptions` 从 API 动态获取，不再硬编码
- **seed_sources() 增强**：启动时从 YAML 种子同步到 DB（只增不覆盖已修改的记录）
- **collector 改造**：`collect_source()` 改为从 DB 读取源配置，不再依赖 `SourceConfig` dataclass

## 功能 (Capabilities)

### 新增功能
- `source-crud`: 源的增删改查 API 及数据模型扩展，包含软删除、预览测试、立即采集
- `source-batch-ops`: 批量操作 API（批量启用/禁用/改分类/立即采集）
- `source-hot-reload`: Scheduler 热更新——源变更后即时同步 APScheduler job
- `source-management-ui`: 前端源管理页面（表格、筛选、CRUD 对话框、预览、批量操作栏）

### 修改功能

## 影响

- **数据库**：`sources` 表 ALTER TABLE 增加 5 个字段，需一次性迁移（从 YAML 回填）
- **后端 API**：新增 `app/api/sources.py` 多个端点；修改现有 `GET /api/sources` 响应模型
- **后端服务**：`collector.py` 改为从 DB 读配置；`jobs.py` 的 `setup_scheduler()` 改为读 DB
- **前端**：新增 `SourcesView.vue`；修改 `BriefingsView.vue`（动态 sourceOptions）；修改 `router/index.ts` 和 `api/index.ts`
- **启动流程**：`main.py` 的 `seed_sources()` 增强为支持字段回填
- **sources.yaml**：降级为初始种子文件，不再是运行时配置源
