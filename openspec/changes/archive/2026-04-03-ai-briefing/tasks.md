## 1. 数据模型与迁移

- [x] 1.1 创建 Briefing 和 BriefingItem SQLAlchemy 模型（app/models/briefing.py）
- [x] 1.2 创建 Alembic 迁移脚本，建立 briefings 和 briefing_items 表

## 2. 简报生成服务

- [x] 2.1 创建 briefing_generator.py，实现 generate_source_briefing 函数
- [x] 2.2 实现 generate_daily_briefing 函数
- [x] 2.3 实现 generate_topic_briefing 函数
- [x] 2.4 实现 generate_custom_briefing 函数
- [x] 2.5 实现后台异步执行逻辑（asyncio.create_task + 异常处理 + 状态更新）

## 3. API 端点

- [x] 3.1 创建 briefing router（app/routers/briefings.py）并注册到 app
- [x] 3.2 实现 GET /api/briefings 列表端点（分页、类型和状态过滤）
- [x] 3.3 实现 GET /api/briefings/{id} 详情端点（含关联 hot_items）
- [x] 3.4 实现 POST /api/briefings/generate 触发生成端点（4种类型 + 重复检查）
- [x] 3.5 实现 DELETE /api/briefings/{id} 删除端点

## 4. 定时任务

- [x] 4.1 在 scheduler 中注册每日 23:00 简报定时任务（串行生成 + 部分失败容错）

## 5. 前端页面

- [x] 5.1 创建 BriefingsView.vue 页面骨架并添加路由和导航栏入口
- [x] 5.2 实现简报列表展示（类型标签、状态标签颜色、时间排序）
- [x] 5.3 实现类型和状态过滤器
- [x] 5.4 实现简报详情面板（Markdown 渲染 + 引用来源列表）
- [x] 5.5 实现 generating 状态轮询自动刷新
- [x] 5.6 实现手动触发简报生成面板（来源选择、每日汇总、主题输入）

## 6. 集成测试与部署

- [x] 6.1 Docker 构建部署并端到端验证（生成→列表→详情→轮询完整流程）
