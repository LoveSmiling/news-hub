## 上下文

当前系统的源配置存在"双源"问题：`sources.yaml` 存储完整配置（type/route/url/schedule/max_items），DB `sources` 表仅存元信息（name/display_name/category/status）。启动时通过 `seed_sources()` 单向同步（只增不删不改），运行时 Scheduler 从 yaml 加载 job。这导致所有源管理操作都要手动编辑文件并重新构建部署容器。

## 目标 / 非目标

**目标：**
- DB 成为运行时唯一配置源，提供完整的 CRUD API
- 源的增删改保存后即刻生效（APScheduler 热更新）
- 提供前端源管理页面，包含预览测试和批量操作
- 软删除（disabled 状态），保护历史数据
- 自定义分类（自由文本，前端 combo box）
- BriefingsView 的 sourceOptions 改为动态获取

**非目标：**
- 不做分类的独立 CRUD（分类是自由文本标签，不建独立表）
- 不做源的导入/导出功能
- 不做采集日志的实时查看（已有 LogsView）
- 不做源的健康检查告警

## 决策

### D1: DB 为运行时真相源，YAML 降级为种子

**选择**：将 `type`、`route`、`url`、`schedule`、`max_items` 五个字段加入 DB `sources` 表。运行时所有读写都走 DB。

**替代方案**：
- API 直接读写 YAML 文件 → Docker 容器内文件操作不可靠，且非真正热更新
- 同时维护 YAML 和 DB → 双源同步复杂度高

**理由**：APScheduler 原生支持运行时 `add_job(replace_existing=True)` 和 `remove_job()`，DB 作为配置源可以直接触发 scheduler 更新。YAML 保留为启动种子，首次部署时自动导入。

### D2: 软删除 + 有条件物理删除

**选择**：删除操作将 `status` 设为 `disabled`，scheduler 移除 job，历史数据保留。仅 `pending` 状态且无关联 `hot_items` 的源允许物理删除。

**替代方案**：
- 统一物理删除 + CASCADE → 丢失历史数据，影响趋势和知识库
- 统一软删除 → pending 误添加的源会永远留在系统中

**理由**：`active` 源有关联数据（hot_items、embeddings），删除会破坏趋势分析和知识库。`pending` 且无数据的源是安全可删的。

### D3: 分类使用自由文本 + 前端聚合

**选择**：`category` 字段保持 `VARCHAR(50)` 不变，不建独立 categories 表。前端通过 `GET /api/sources/categories` 获取去重列表，新增/编辑时用可创建的下拉框。

**替代方案**：
- 独立 `categories` 表 + 外键 → 多一套 CRUD，过度设计
- 枚举限制 → 不灵活

**理由**：源数量不会太大（几十到上百），分类本质是标签。自由文本零成本，满足自定义需求。

### D4: 预览测试接口不依赖 DB

**选择**：`POST /api/sources/test` 接收 `{ type, route, url, max_items }` 参数，临时创建 Spider 执行 `fetch()`，返回抓取结果。不需要先保存到 DB。

**理由**：用户在新增对话框填写信息后可先预览，确认有效再保存。避免保存无效源到 DB。

### D5: 批量操作使用单一 PATCH 端点

**选择**：`PATCH /api/sources/batch` 接收 `{ ids, action, ...params }`，支持 `enable`、`disable`、`set_category`、`collect` 四种操作。

**替代方案**：
- 每种操作独立端点 → 端点膨胀
- 通用 batch update → 过度灵活，难以校验

**理由**：四种操作的参数结构不同但 pattern 一致，单端点 + action 判断简洁明了。

### D6: Scheduler 热更新策略

**选择**：在 API 的 create/update/delete handler 中直接调用 scheduler 操作：
- 新增/修改 → `scheduler.add_job(..., replace_existing=True)`
- 禁用/删除 → `scheduler.remove_job(job_id)`
- 启用 → `scheduler.add_job(..., replace_existing=True)`

**理由**：APScheduler 的 `AsyncIOScheduler` 是线程安全的，支持运行时动态操作。`replace_existing=True` 已在现有代码中使用。

### D7: DB 迁移采用启动时自动迁移

**选择**：在 `seed_sources()` 中增强：先用 raw SQL 检查并添加缺失的列，然后从 YAML 回填所有现有记录的新字段（仅填充值为空/默认的字段）。

**替代方案**：
- Alembic 迁移 → 项目未使用 Alembic，引入成本高
- 手动 SQL → 不可复现

**理由**：项目规模小，源数量少，启动时自动迁移简单可靠。

## 风险 / 权衡

- **[风险] 迁移遗漏** → 迁移脚本只处理 21 条记录，手动验证即可。启动时有日志输出迁移状态。
- **[风险] Scheduler 热更新 race condition** → APScheduler 的 add/remove 是线程安全的；API 是单进程 uvicorn，不存在跨进程竞争。
- **[权衡] seed_sources 只增不覆盖** → 用户通过 UI 修改的配置不会被 YAML 覆盖，但也意味着 YAML 变更不会自动同步到已存在的 DB 记录。这是有意设计：DB 是真相源。
- **[权衡] 无 Alembic** → 以后更复杂的迁移可能需要引入。目前规模可控。
