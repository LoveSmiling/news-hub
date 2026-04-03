# chat-service 规范

## 目的
待定 - 由归档变更 ai-chat-backend 创建。归档后请更新目的。
## 需求
### 需求:RAG上下文检索
系统必须提供 `retrieve_chat_context(query: str, limit: int)` 异步函数，从 hot_items 中检索与用户问题最相关的条目。

#### 场景:向量搜索可用
- **当** 用户消息存在对应的 embedding 时
- **那么** 必须通过 pgvector 余弦距离搜索 hot_items.embedding 列，返回 Top-N 相关条目（含 title, source, url, summary 摘要）

#### 场景:向量搜索不可用时回退
- **当** embedding 生成失败或 hot_items 中无向量数据时
- **那么** 必须回退到关键词搜索（标题包含 + keywords JSONB 匹配）

### 需求:对话上下文组装
系统必须提供 `build_chat_messages(session_id: int, user_message: str, rag_context: list)` 函数，组装发送给 LLM 的消息列表。

#### 场景:系统提示构建
- **当** 组装消息时
- **那么** 必须生成 system prompt，包含：角色定义（新闻分析助手）、RAG 检索到的新闻摘要作为参考资料、回答指引

#### 场景:历史上下文截取
- **当** 会话历史超过 10 轮（20 条消息）时
- **那么** 必须仅保留最近 10 轮对话历史，截断最早的消息

#### 场景:消息格式
- **当** 返回消息列表时
- **那么** 必须按 `[system, ...history, user_message]` 顺序排列，每条包含 role 和 content

### 需求:流式LLM调用
系统必须提供 `stream_chat_completion(messages: list)` 异步生成器，使用 OpenAI SDK stream 模式调用 LLM。

#### 场景:正常流式输出
- **当** 调用 LLM 成功时
- **那么** 必须逐 chunk yield 文本片段（delta content），同时在内部拼接完整回复

#### 场景:流式完成后
- **当** LLM 输出结束时
- **那么** 必须将完整的 assistant 回复保存到 chat_messages 表，并记录 token 使用日志

#### 场景:LLM调用失败
- **当** LLM 调用过程中发生异常时
- **那么** 必须 yield 一条错误消息文本，禁止抛出未处理异常

