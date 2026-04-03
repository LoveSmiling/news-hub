## 为什么

简报是 NewsHub 的核心产出物，但目前只能在应用内查看，无法分享给他人或离线保存。用户希望将高质量的 AI 简报分享给同事/朋友，也希望能导出为 Markdown 做本地归档或二次编辑。

## 变更内容

1. **简报分享**：为简报生成随机 token 分享链接，支持设置过期时间（1天/7天/30天/永久），支持取消分享和更新有效期。提供独立的分享阅读页面（报告式排版、固定浅色主题、NewsHub 品牌展示）。
2. **Markdown 导出**：在简报详情中添加导出按钮，纯前端拼接 Markdown 内容（标题 + 元信息 + 正文 + 引用来源）并下载为 .md 文件。

## 功能 (Capabilities)

### 新增功能
- `briefing-share`: 简报分享功能，包括分享链接生成、过期控制、取消分享、公开阅读 API 和独立分享页面
- `briefing-export`: 简报导出为 Markdown 文件，纯前端实现

### 修改功能

## 影响

- **数据模型**：Briefing 表新增 `share_token`、`share_expires` 字段
- **后端 API**：新增分享管理端点（POST/DELETE /api/briefings/{id}/share）和公开访问端点（GET /api/share/{token}）
- **前端路由**：新增 `/share/:token` 路由
- **前端组件**：BriefingsView.vue 详情 modal 新增分享/导出按钮，新建 ShareView.vue 分享阅读页
- **Nginx**：无变更（/api/ 代理已覆盖）
- **数据库迁移**：需通过 seed_sources 模式自动 ALTER TABLE 添加列
