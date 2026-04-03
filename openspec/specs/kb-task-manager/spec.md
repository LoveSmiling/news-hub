# kb-task-manager 规范

## 目的
待定 - 由归档变更 knowledge-base 创建。归档后请更新目的。
## 需求
### 需求:创建后台任务
系统必须提供 POST /api/kb/tasks 端点创建后台任务，支持 incremental 和 full_rebuild 两种类型，返回 202 状态码和 task_id。

#### 场景:创建增量更新任务
- **当** POST /api/kb/tasks body={"type": "incremental"}
- **那么** 返回 202 {"task_id": "...", "type": "incremental", "status": "pending", "total": N}，后台开始处理 embedding IS NULL 的条目

#### 场景:创建全量重建任务
- **当** POST /api/kb/tasks body={"type": "full_rebuild"}
- **那么** 先将所有 hot_items.embedding 设为 NULL，然后返回 202 并开始全量生成

#### 场景:已有任务运行中
- **当** 已有一个 running 状态的任务时再次 POST
- **那么** 返回 409 {"detail": "已有任务正在运行"}

### 需求:查询任务进度
系统必须提供 GET /api/kb/tasks/{task_id} 端点查询任务进度。

#### 场景:任务运行中
- **当** GET /api/kb/tasks/{id}，任务正在处理
- **那么** 返回 {"task_id", "type", "status": "running", "progress": 120, "total": 2159}

#### 场景:任务完成
- **当** 任务处理完毕
- **那么** status 变为 "done"，progress 等于 total

#### 场景:任务失败
- **当** 任务执行过程中发生不可恢复的错误
- **那么** status 变为 "failed"，包含 error 字段描述原因

#### 场景:任务不存在
- **当** GET /api/kb/tasks/{无效id}
- **那么** 返回 404

### 需求:内存任务存储
任务管理器必须使用内存 dict 存储任务状态，通过 asyncio.create_task 执行后台处理，每批（50 条）处理完更新 progress。

#### 场景:服务重启
- **当** 服务重启后查询之前的任务
- **那么** 返回 404（内存任务不持久化，可接受）

