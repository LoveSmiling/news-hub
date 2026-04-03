## 上下文

系统已有 pgvector 1024 维向量索引（bge-m3 模型），hot_items 表存储了 embedding 列。现有的 `content_service` 可以检索和清洗内容，`llm_client` 封装了 OpenAI SDK 的异步调用。需要在此基础上构建对话式查询功能。

## 目标 / 非目标

**目标：**
- 支持多轮对话，保持上下文连贯性
- 通过 RAG 检索相关热点新闻作为 LLM 上下文
- SSE 流式响应，实时推送 token
- 会话持久化，支持历史对话查看

**非目标：**
- 不实现 Agent/Tool-use 模式（仅问答）
- 不实现用户认证（单用户系统）
- 不做前端实现（留给 ai-chat-frontend 变更）

## 决策

### D1: 流式响应使用 SSE（而非 WebSocket）
- SSE 是单向推送，符合 LLM 对话的请求-响应模式
- FastAPI 原生支持 `StreamingResponse`，无需额外依赖
- 前端 `EventSource` API 或 `fetch` stream 即可消费
- 替代方案：WebSocket 双向通信，但对话场景无需服务端主动发起消息

### D2: RAG 检索使用向量搜索 + 关键词混合
- 先从用户消息提取关键词，再用向量相似度搜索 hot_items
- 使用现有的 embedding 列和 pgvector HNSW 索引
- 取 Top-10 相关条目作为上下文注入 system prompt
- 替代方案：纯关键词搜索（缺少语义理解）、纯向量搜索（可能遗漏精确匹配）

### D3: 上下文窗口管理 — 最近 N 轮 + 系统提示
- 保留最近 10 轮对话历史（user+assistant 各算一轮）
- 系统提示包含：角色定义 + RAG 检索到的新闻摘要
- 总 prompt 控制在合理长度，超出时截断最早的历史
- 替代方案：全量历史（token 爆炸）、摘要压缩（增加复杂度和延迟）

### D4: 会话模型采用简单的 session + messages 结构
- `chat_sessions` 表：id, title, created_at, updated_at
- `chat_messages` 表：id, session_id, role, content, created_at
- title 由首次用户消息自动生成（取前 30 字）
- 替代方案：嵌套 JSON 存储（查询不便）、独立对话树（过于复杂）

### D5: LLM 调用使用 OpenAI SDK stream 模式
- `client.chat.completions.create(stream=True)` 返回 async iterator
- 逐 chunk 通过 SSE 推送给前端，同时拼接完整回复存入 DB
- 日志仅在完成后记录一次（含总 token 数）

## 风险 / 权衡

- [风险] embedding 模型未给所有 hot_items 生成向量 → 回退到关键词搜索
- [风险] 长对话上下文占用大量 token → 通过截断最早历史缓解
- [风险] SSE 连接中断导致消息不完整 → 前端需处理重连，后端保存已生成的部分内容
- [权衡] 不做对话摘要压缩，换取实现简单性，代价是长会话后期可能重复引用早期信息
