## 新增需求

### 需求:Briefing数据模型
系统必须提供 `Briefing` SQLAlchemy 模型，映射到 `briefings` 表。

#### 场景:表字段定义
- **当** 创建 `briefings` 表时
- **那么** 必须包含以下字段：`id` (SERIAL PK), `title` (TEXT NOT NULL), `brief_type` (VARCHAR(20) NOT NULL, 值为 source/daily/topic/custom 之一), `scope_params` (JSONB), `content` (TEXT, 生成后的 Markdown 内容), `token_usage` (INTEGER), `status` (VARCHAR(20) NOT NULL, 默认 "pending"), `created_at` (TIMESTAMP WITH TZ, 默认 now()), `completed_at` (TIMESTAMP WITH TZ, 可空)

#### 场景:状态字段值
- **当** 记录简报状态时
- **那么** `status` 必须为以下值之一：`pending`（等待生成）、`generating`（正在生成中）、`done`（生成完成）、`failed`（生成失败）

### 需求:BriefingItem关联模型
系统必须提供 `BriefingItem` SQLAlchemy 模型，映射到 `briefing_items` 表，记录简报与热点条目的关联关系。

#### 场景:关联表字段
- **当** 创建 `briefing_items` 表时
- **那么** 必须包含：`id` (SERIAL PK), `briefing_id` (INTEGER FK → briefings.id, ON DELETE CASCADE), `hot_item_id` (INTEGER FK → hot_items.id, ON DELETE CASCADE)

#### 场景:级联删除
- **当** 删除一条 briefing 记录时
- **那么** 必须自动删除所有关联的 `briefing_items` 记录

### 需求:数据库迁移
系统必须提供 Alembic 迁移脚本创建 `briefings` 和 `briefing_items` 表。

#### 场景:迁移执行
- **当** 运行迁移时
- **那么** 必须创建 `briefings` 表和 `briefing_items` 表，并在 `briefing_items.briefing_id` 和 `briefing_items.hot_item_id` 上建立外键和索引
