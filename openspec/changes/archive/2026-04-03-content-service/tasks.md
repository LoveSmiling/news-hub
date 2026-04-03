## 1. HTML 清洗工具

- [x] 1.1 添加 beautifulsoup4 依赖到 requirements.txt
- [x] 1.2 创建 app/utils/html_cleaner.py，实现 clean_html() 函数（移除标签、保留 img alt、清除 script/style、转换 HTML 实体、压缩空白）
- [x] 1.3 在同文件实现 truncate_text() 函数（字符级截断、句子边界优先、追加省略号）

## 2. 内容检索服务

- [x] 2.1 在 app/services/content_service.py 定义 ContentItem 数据类（id, title, source, url, content, collected_at）
- [x] 2.2 实现 retrieve_contents() 异步函数，支持按 source/时间范围/keyword/item_ids/limit 多维条件查询
- [x] 2.3 在 retrieve_contents 中集成 HTML 清洗和内容截断（从 raw_data->>'summary' 提取并清洗）

## 3. Map-Reduce 摘要框架

- [x] 3.1 创建 app/services/ai/map_reduce_summarizer.py，实现 Map 阶段：单批次内容 → LLM 摘要
- [x] 3.2 实现 Reduce 阶段：多个批次摘要 → LLM 结构化简报（Markdown 格式）
- [x] 3.3 实现 map_reduce_summarize() 完整管线（自动分批、asyncio.Semaphore 并发控制、部分失败处理、少量内容跳过 Map）
- [x] 3.4 添加 /no_think 到 Map 和 Reduce 的 system prompt

## 4. 集成验证

- [x] 4.1 Docker 构建部署，通过 /api/enrich-keywords 或临时测试端点验证 HTML 清洗效果
- [x] 4.2 验证 Map-Reduce 管线端到端运行（手动调用或临时脚本）
