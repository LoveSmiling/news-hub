## 新增需求

### 需求:构建embedding输入文本
系统必须提供 `build_embedding_text(title, raw_summary)` 函数，将标题和清理后的摘要拼接为 embedding 输入文本。

#### 场景:有摘要的条目
- **当** 传入 title="高德开源ABot" 和 raw_summary="<p>近日高德宣布...</p>"
- **那么** 返回 "高德开源ABot\n\n近日高德宣布..."（HTML 已清理，摘要截断 500 字）

#### 场景:无摘要的条目
- **当** 传入 title="某新闻标题" 和 raw_summary=None
- **那么** 返回 "某新闻标题"（仅标题）

### 需求:批量生成embedding
系统必须提供批量 embedding 生成函数，接收 hot_items 列表，为每条生成 embedding 并写入数据库。

#### 场景:批量处理
- **当** 传入 50 条无 embedding 的 hot_items
- **那么** 调用 get_embeddings_batch 生成 1024 维向量，批量 UPDATE 到 hot_items.embedding 字段

#### 场景:生成失败
- **当** embedding API 调用失败
- **那么** 记录错误日志，跳过本批次，不影响后续批次处理
