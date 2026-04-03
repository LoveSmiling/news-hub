## 1. 数据模型扩展与迁移

- [x] 1.1 扩展 Source 模型（app/models/source.py）：添加 type、route、url、schedule、max_items 字段
- [x] 1.2 扩展 SourceResponse schema（app/api/schemas.py）：添加新字段到响应模型，新增 SourceCreate/SourceUpdate 请求模型
- [x] 1.3 增强 seed_sources()（app/main.py）：自动检测并添加缺失列（ALTER TABLE），从 YAML 回填已有记录的新字段值（不覆盖已修改的）

## 2. Scheduler 热更新与 Collector 改造

- [x] 2.1 改造 setup_scheduler()（app/scheduler/jobs.py）：从 DB 读取非 disabled 源注册 job，不再依赖 load_source_configs()
- [x] 2.2 新增 scheduler 热更新函数：register_source_job(source)、remove_source_job(source_name) 供 API 调用
- [x] 2.3 改造 collect_source()（app/services/collector.py）：改为接收 source_name 参数，内部从 DB 读完整配置

## 3. CRUD API

- [x] 3.1 实现 GET /api/sources/{id} 端点
- [x] 3.2 实现 POST /api/sources 端点（含 name 唯一性校验、scheduler 注册）
- [x] 3.3 实现 PUT /api/sources/{id} 端点（含 scheduler 热更新）
- [x] 3.4 实现 DELETE /api/sources/{id} 端点（软删除 + 有条件物理删除 + scheduler 移除）
- [x] 3.5 实现 POST /api/sources/test 预览测试端点
- [x] 3.6 实现 POST /api/sources/{id}/collect 立即采集端点
- [x] 3.7 实现 GET /api/sources/categories 分类列表端点

## 4. 批量操作 API

- [x] 4.1 实现 PATCH /api/sources/batch 端点（enable/disable/set_category/collect 四种 action）

## 5. 前端 API 客户端

- [x] 5.1 在 frontend/src/api/index.ts 添加源管理相关的 API 方法（CRUD、test、collect、batch、categories）

## 6. 前端源管理页面

- [x] 6.1 创建 SourcesView.vue：表格列表 + 筛选栏（分类/类型/状态）
- [x] 6.2 实现新增/编辑源对话框（type 切换 route/url、可创建分类下拉框、cron 输入）
- [x] 6.3 实现预览测试功能（对话框内展示抓取结果）
- [x] 6.4 实现删除确认对话框
- [x] 6.5 实现批量操作栏（选中后显示：批量启用/禁用/改分类/采集）
- [x] 6.6 实现立即采集按钮

## 7. 路由与导航

- [x] 7.1 添加 /sources 路由到 router/index.ts
- [x] 7.2 在侧边栏导航添加 "源管理" 菜单项

## 8. BriefingsView 动态化

- [x] 8.1 BriefingsView.vue 的 sourceOptions 改为从 GET /api/sources 动态获取

## 9. 部署验证

- [x] 9.1 Docker 构建部署 app + frontend
- [x] 9.2 E2E 验证：源列表展示、新增/编辑/预览/删除/批量操作、热更新生效、BriefingsView 动态源选项
