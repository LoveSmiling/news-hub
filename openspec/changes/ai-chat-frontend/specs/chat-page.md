## chat-page

聊天页面整体功能，包含会话管理侧边栏和消息对话区域。

### 行为

- 页面加载时自动获取会话列表
- 左侧侧边栏固定宽度 280px，显示会话列表和新建按钮
- 右侧消息区域自适应宽度，显示当前会话的消息和输入框
- 未选中会话时，右侧显示欢迎提示
- 选中会话后，加载并显示历史消息

### 会话侧边栏

- 顶部"新建对话"按钮，点击调用 POST /api/chat/sessions 创建并自动选中
- 会话列表按 updated_at 降序排列，显示 title 和 message_count
- 当前选中会话高亮
- 每个会话项右侧有删除图标，点击弹出确认后调用 DELETE
- 删除当前选中会话后清空右侧

### 消息区域

- 消息列表滚动区域，user 消息右对齐蓝色气泡，assistant 消息左对齐灰色气泡
- assistant 消息内容使用 markdown-it 渲染 HTML
- 流式接收中的消息实时更新，显示打字光标动画
- 消息区域自动滚动到最新消息

### 输入和发送

- 底部输入框 + 发送按钮，支持 Enter 发送、Shift+Enter 换行
- 发送时：保存用户消息到本地列表，调用 POST /api/chat/sessions/{id}/messages
- 使用 fetch + ReadableStream 消费 SSE 流
- 流式期间禁用输入框和发送按钮
- 流结束后刷新会话列表（获取自动生成的标题）
- 处理 `<think>` 标签：过滤掉 `<think>...</think>` 内容

### 路由和导航

- 注册 /chat 路由，懒加载 ChatView.vue
- AppLayout 导航栏添加"对话"按钮
