## 1. 简报生成器：构建 display_name 映射

- [x] 1.1 在 `briefing_generator.py` 中添加辅助函数，查询 Source 表构建 `{name: display_name}` 映射字典
- [x] 1.2 在 `generate_source_briefing()` 中使用映射将简报标题从 `f"{source} 简报"` 改为 `f"{display_name} 简报"`
- [x] 1.3 在 `generate_source_briefing()` 中将 `display_name` 传递给 `summarize_titles()` 的 `source_name` 参数

## 2. Map-Reduce 摘要器：使用 display_name 格式化

- [x] 2.1 修改 `_format_batch()` 函数，增加可选的 `display_map` 参数
- [x] 2.2 格式化时将 `item.source` 通过映射转换为 `display_name`，映射不存在时回退到 `item.source`
- [x] 2.3 更新 `_format_batch()` 的所有调用方，传入 `display_map`

## 3. 验证

- [x] 3.1 手动触发一个源的简报生成，确认标题和内容中使用中文来源名称
