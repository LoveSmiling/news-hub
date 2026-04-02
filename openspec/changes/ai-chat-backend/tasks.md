## 1. 数据模型与迁移

- [x] 1.1 创建 ChatSession 和 ChatMessage SQLAlchemy 模型（app/models/chat.py）
- [x] 1.2 创建 Alembic 迁移脚本 008，建立 chat_sessions 和 chat_messages 表

## 2. 对话服务

- [x] 2.1 创建 chat_service.py，实现 RAG 上下文检索（向量搜索 + 关键词回退）
- [x] 2.2 实现对话上下文组装（system prompt + RAG 上下文 + 最近 10 轮历史）
- [x] 2.3 实现流式 LLM 调用（async generator + token 拼接 + 日志记录 + 错误处理）

## 3. API 端点

- [x] 3.1 创建 chat router（app/api/chat.py）并注册到 app
- [x] 3.2 实现 POST /api/chat/sessions 创建会话
- [x] 3.3 实现 GET /api/chat/sessions 会话列表（含 message_count）
- [x] 3.4 实现 GET /api/chat/sessions/{id} 会话详情（含消息历史）
- [x] 3.5 实现 DELETE /api/chat/sessions/{id} 删除会话
- [x] 3.6 实现 POST /api/chat/sessions/{id}/messages SSE 流式端点

## 4. 部署验证

- [x] 4.1 Docker 构建部署并端到端验证（创建会话→发送消息→SSE 流式响应→历史查看）
