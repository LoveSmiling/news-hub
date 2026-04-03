# source-hot-reload 规范

## 目的
待定 - 由归档变更 source-management 创建。归档后请更新目的。
## 需求
### 需求:Scheduler 热更新
系统必须在源的增删改操作后立即同步 APScheduler job，无需重启应用。

#### 场景:新增源后注册 job
- **当** 通过 API 新增一个源
- **那么** 系统必须立即使用该源的 schedule 注册一个新的 APScheduler job，job id 为 `collect_{source.name}`

#### 场景:修改源 schedule 后更新 job
- **当** 通过 API 修改源的 schedule 字段
- **那么** 系统必须立即用新的 cron 表达式替换对应的 APScheduler job（使用 `replace_existing=True`）

#### 场景:禁用源后移除 job
- **当** 通过 API 禁用（disable）或软删除一个源
- **那么** 系统必须立即从 APScheduler 移除对应的 job

#### 场景:启用源后恢复 job
- **当** 通过 API 启用（enable）一个 disabled 源
- **那么** 系统必须立即使用该源的 schedule 注册 APScheduler job

### 需求:setup_scheduler 改为读 DB
系统启动时，`setup_scheduler()` 必须从 DB `sources` 表读取所有非 disabled 状态的源配置来注册 scheduler job，禁止直接依赖 `sources.yaml`。

#### 场景:启动时注册 job
- **当** 应用启动
- **那么** 系统必须查询 DB 中所有 status 不为 `disabled` 的源，为每个源注册 APScheduler job

#### 场景:disabled 源不注册 job
- **当** 应用启动且 DB 中有 status 为 `disabled` 的源
- **那么** 系统禁止为该源注册 scheduler job

### 需求:collect_source 改为从 DB 读配置
`collect_source()` 必须接受 source name 或 source id 作为参数，内部从 DB 读取完整源配置（type/route/url/schedule/max_items），禁止依赖 `SourceConfig` dataclass 传参。

#### 场景:从 DB 读配置执行采集
- **当** scheduler 触发或手动调用 `collect_source(source_name)`
- **那么** 系统必须从 DB 读取该源的完整配置，创建对应 Spider 并执行采集

#### 场景:源不存在时跳过
- **当** `collect_source` 被调用但 DB 中无对应源
- **那么** 系统必须记录错误日志并跳过该次采集

