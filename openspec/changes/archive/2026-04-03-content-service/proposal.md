## 为什么

当前系统的 AI 功能（摘要、关键词）仅基于标题生成，但 RSS 数据的 `raw_data.summary` 字段已包含丰富的正文内容（少数派平均 ~10K 字符，IT之家 ~2.3K，澎湃 ~1.6K）。需要一个内容基础层来清洗 HTML、检索内容、并通过 Map-Reduce 策略将大量内容分级压缩为结构化摘要，为后续的 AI 简报系统和 AI 对话系统提供共享基础设施。

## 变更内容

- **新增** HTML 清洗工具：将 RSS 中的 HTML 内容（`<p>`, `<a>`, `<img>`, `<video>` 等标签）转换为干净的纯文本
- **新增** 内容检索服务：按来源/时间范围/关键词/条目ID 批量获取清洗后的热点内容
- **新增** Map-Reduce 摘要框架：支持将大批量内容分批独立摘要（Map），再聚合为结构化简报（Reduce）的通用管线
- **新增** 内容截断策略：对超长内容按可配置上限截断，控制 Token 预算

## 功能 (Capabilities)

### 新增功能

- `html-cleaner`: HTML 标签清洗与纯文本提取工具
- `content-retrieval`: 内容检索服务，按多维条件批量获取和清洗热点内容
- `map-reduce-summarizer`: Map-Reduce 分级摘要框架，支持大批量内容的分批压缩与聚合

### 修改功能

（无）

## 影响

- **新增文件**: `app/utils/html_cleaner.py`, `app/services/content_service.py`, `app/services/ai/map_reduce_summarizer.py`
- **依赖**: 新增 `beautifulsoup4` Python 包用于 HTML 解析
- **被依赖**: 后续的 `ai-briefing` 和 `ai-chat-backend` 变更将依赖本变更提供的服务
- **无 API 变更**: 本变更仅提供内部服务层，不新增 HTTP 端点
- **无数据库变更**: 不涉及新表或迁移
