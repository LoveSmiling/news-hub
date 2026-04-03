## 为什么

ai-chat-backend 已提供完整的对话 API（会话 CRUD + SSE 流式消息），但用户目前无法通过前端界面使用对话功能。需要实现一个聊天页面，让用户能以自然语言对话方式查询和分析热点新闻数据。

## 变更内容

- 新增 `/chat` 前端页面，包含会话侧边栏和对话主区域
- 实现 SSE 流式消息接收和逐字渲染
- 实现 Markdown 格式的 AI 回复渲染
- 添加导航栏"对话"入口

## 功能 (Capabilities)

### 新增功能
- `chat-page`: 聊天页面整体布局（左侧会话列表 + 右侧对话区域）
- `chat-session-sidebar`: 会话侧边栏（会话列表、新建、删除）
- `chat-message-area`: 消息展示区域（Markdown 渲染 + 流式打字效果）
- `chat-input`: 输入框和发送逻辑（SSE 消费 + 自动滚动）

## 影响

- 新增 Vue 组件：`ChatView.vue`
- 修改路由：添加 `/chat` 路由
- 修改导航栏：添加"对话"按钮
- 使用现有依赖：`markdown-it`、`axios`、Naive UI 组件
- 消费 API：`/api/chat/sessions`（CRUD）、`/api/chat/sessions/{id}/messages`（SSE）
