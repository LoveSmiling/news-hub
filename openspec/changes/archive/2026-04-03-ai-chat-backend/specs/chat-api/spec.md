## 新增需求

### 需求:会话列表API
系统必须提供 `GET /api/chat/sessions` 端点，返回所有聊天会话。

#### 场景:默认查询
- **当** 不带参数请求时
- **那么** 必须返回所有会话，按 `updated_at` 降序排列，每条包含 id, title, created_at, updated_at, message_count（消息数）

### 需求:创建会话API
系统必须提供 `POST /api/chat/sessions` 端点，创建新的聊天会话。

#### 场景:正常创建
- **当** 请求 body 为 `{title: "新对话"}` 或空 body 时
- **那么** 必须创建新会话，默认标题为 "新对话"，返回会话记录

### 需求:会话详情API
系统必须提供 `GET /api/chat/sessions/{id}` 端点，返回会话详情及消息历史。

#### 场景:正常获取
- **当** 请求已存在的会话 ID 时
- **那么** 必须返回会话信息和所有消息列表（按 created_at 升序排列）

#### 场景:不存在的ID
- **当** 请求不存在的会话 ID 时
- **那么** 必须返回 HTTP 404

### 需求:删除会话API
系统必须提供 `DELETE /api/chat/sessions/{id}` 端点，删除会话。

#### 场景:正常删除
- **当** 删除已存在的会话时
- **那么** 必须删除会话及其所有消息，返回 HTTP 200

### 需求:发送消息SSE端点
系统必须提供 `POST /api/chat/sessions/{id}/messages` 端点，发送用户消息并以 SSE 流式返回 AI 回复。

#### 场景:正常对话
- **当** 请求 body 为 `{content: "今天有什么科技新闻？"}` 时
- **那么** 必须：(1) 保存用户消息到 DB, (2) 执行 RAG 检索, (3) 组装上下文, (4) 调用 LLM 流式生成, (5) 通过 SSE 逐 chunk 推送 `data: {delta: "..."}`, (6) 流结束时推送 `data: {done: true, message_id: N}`, (7) 保存完整 assistant 消息到 DB

#### 场景:自动更新会话标题
- **当** 会话的 title 为默认值 "新对话" 且收到首条用户消息时
- **那么** 必须将会话标题更新为用户消息的前 30 个字符

#### 场景:会话不存在
- **当** session_id 不存在时
- **那么** 必须返回 HTTP 404

#### 场景:SSE Content-Type
- **当** 返回流式响应时
- **那么** 必须设置 Content-Type 为 `text/event-stream`
