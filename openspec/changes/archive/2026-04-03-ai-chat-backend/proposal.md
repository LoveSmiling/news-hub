## 为什么

用户需要以自然语言对话的方式查询和分析聚合的热点新闻数据，而不是仅通过列表浏览或关键词搜索。当前系统缺少对话式交互能力，无法结合上下文进行连续追问、深入分析或跨来源关联。

## 变更内容

- 新增 AI 对话会话（session）和消息（message）数据模型，支持多轮对话历史持久化
- 新增对话服务，支持基于 RAG（检索增强生成）的问答，利用现有的 pgvector 向量搜索和内容服务检索相关热点
- 新增 SSE（Server-Sent Events）流式响应端点，实时推送 LLM 生成的回答
- 新增会话管理 API（创建/列表/详情/删除会话，发送消息）

## 功能 (Capabilities)

### 新增功能
- `chat-storage`: 对话会话和消息的数据模型与数据库迁移
- `chat-service`: 对话服务，包含 RAG 检索、上下文组装、LLM 调用和流式生成
- `chat-api`: 会话管理及消息 SSE 流式端点

### 修改功能

## 影响

- 新增数据库表：`chat_sessions`、`chat_messages`
- 新增 API 端点：`/api/chat/sessions`、`/api/chat/sessions/{id}`、`/api/chat/sessions/{id}/messages`
- 依赖现有模块：`content_service`（内容检索）、`llm_client`（LLM 调用）、pgvector 向量搜索
- 需要 OpenAI SDK 的流式 API 支持（已有依赖）
