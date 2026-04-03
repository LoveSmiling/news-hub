# source-batch-ops 规范

## 目的
待定 - 由归档变更 source-management 创建。归档后请更新目的。
## 需求
### 需求:批量操作端点
系统必须提供 `PATCH /api/sources/batch` 端点，接收 `{ ids: number[], action: string, ...params }` 参数，支持以下操作：

| action | 效果 | 额外参数 |
|--------|------|----------|
| enable | 将指定源 status 设为 active 并注册 scheduler job | 无 |
| disable | 将指定源 status 设为 disabled 并移除 scheduler job | 无 |
| set_category | 修改指定源的 category 字段 | category: string |
| collect | 对指定源立即执行一次采集 | 无 |

#### 场景:批量启用
- **当** 客户端发送 `PATCH /api/sources/batch`，body 为 `{ ids: [1,2,3], action: "enable" }`
- **那么** 系统必须将 id 为 1、2、3 的源 status 设为 `active`，并为每个源注册 scheduler job

#### 场景:批量禁用
- **当** 客户端发送 `PATCH /api/sources/batch`，body 为 `{ ids: [1,2,3], action: "disable" }`
- **那么** 系统必须将 id 为 1、2、3 的源 status 设为 `disabled`，并移除对应的 scheduler job

#### 场景:批量修改分类
- **当** 客户端发送 `PATCH /api/sources/batch`，body 为 `{ ids: [1,2], action: "set_category", category: "金融" }`
- **那么** 系统必须将 id 为 1、2 的源 category 更新为 `金融`

#### 场景:批量立即采集
- **当** 客户端发送 `PATCH /api/sources/batch`，body 为 `{ ids: [1,2,3], action: "collect" }`
- **那么** 系统必须依次对 id 为 1、2、3 的源执行采集，跳过 disabled 状态的源，返回每个源的采集结果摘要

#### 场景:无效 action
- **当** 客户端发送的 action 不在支持列表中
- **那么** 系统必须返回 400 Bad Request

#### 场景:空 ids 数组
- **当** 客户端发送的 ids 为空数组
- **那么** 系统必须返回 400 Bad Request

