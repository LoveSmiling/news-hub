## 架构

### 页面布局
```
+--------------------------------------------------+
| AppLayout 导航栏 [热榜|搜索|...|对话|简报]       |
+--------------------------------------------------+
| 侧边栏 (280px)     |  消息区域                    |
| +--------------+    | +------------------------+  |
| | [+ 新建对话] |    | | 系统消息/历史消息       |  |
| +--------------+    | | user: 右对齐气泡        |  |
| | 会话1        |    | | assistant: 左对齐+MD    |  |
| | 会话2 (选中) |    | |                        |  |
| | 会话3   [x]  |    | | 流式打字中...          |  |
| +--------------+    | +------------------------+  |
|                     | | [输入框...] [发送按钮]  |  |
+--------------------------------------------------+
```

### 组件结构
单文件组件 `ChatView.vue`，使用 `<script setup>` + Composition API：
- 内部逻辑区分：会话管理、消息管理、SSE 流式、UI 状态

### SSE 消费方案
使用原生 `fetch` + `ReadableStream` 读取 SSE 流：
```js
const response = await fetch(url, { method: 'POST', body, headers })
const reader = response.body.getReader()
const decoder = new TextDecoder()
// 逐块读取，解析 data: {"content":"..."} 格式
// 遇到 data: [DONE] 结束
```

### Markdown 渲染
复用已有 `markdown-it` 依赖，配置与 BriefingsView.vue 一致。

### API 对接
| 操作 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 列表 | GET | /api/chat/sessions | 返回 items 数组 |
| 新建 | POST | /api/chat/sessions | body: {title?} |
| 详情 | GET | /api/chat/sessions/{id} | 含 messages |
| 删除 | DELETE | /api/chat/sessions/{id} | 204 |
| 发消息 | POST | /api/chat/sessions/{id}/messages | SSE 流 |

### 关键交互
1. 点击"新建对话" → POST 创建 → 选中新会话
2. 点击会话 → GET 详情 → 渲染历史消息
3. 发送消息 → POST → SSE 流式接收 → 逐字渲染 → 完成后刷新会话列表（获取自动标题）
4. 流式中禁用输入框，显示加载状态
5. 消息区域自动滚动到底部
