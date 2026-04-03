## 新增需求

### 需求:ChatSession数据模型
系统必须提供 `ChatSession` SQLAlchemy 模型，映射到 `chat_sessions` 表。

#### 场景:表字段定义
- **当** 创建 `chat_sessions` 表时
- **那么** 必须包含以下字段：`id` (SERIAL PK), `title` (TEXT NOT NULL), `created_at` (TIMESTAMP WITH TZ, 默认 now()), `updated_at` (TIMESTAMP WITH TZ, 默认 now())

#### 场景:标题自动生成
- **当** 未显式提供标题时
- **那么** 必须使用首条用户消息的前 30 个字符作为标题

### 需求:ChatMessage数据模型
系统必须提供 `ChatMessage` SQLAlchemy 模型，映射到 `chat_messages` 表。

#### 场景:表字段定义
- **当** 创建 `chat_messages` 表时
- **那么** 必须包含以下字段：`id` (SERIAL PK), `session_id` (INTEGER FK → chat_sessions.id, ON DELETE CASCADE), `role` (VARCHAR(20) NOT NULL, 值为 user/assistant/system), `content` (TEXT NOT NULL), `created_at` (TIMESTAMP WITH TZ, 默认 now())

#### 场景:级联删除
- **当** 删除一条 chat_session 记录时
- **那么** 必须自动删除所有关联的 `chat_messages` 记录

### 需求:数据库迁移
系统必须提供 Alembic 迁移脚本创建 `chat_sessions` 和 `chat_messages` 表。

#### 场景:迁移执行
- **当** 运行迁移时
- **那么** 必须创建两张表，并在 `chat_messages.session_id` 上建立外键和索引
