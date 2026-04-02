## 1. 数据模型与迁移

- [x] 1.1 Briefing 模型新增 share_token (VARCHAR(32), UNIQUE, NULLABLE) 和 share_expires (TIMESTAMP, NULLABLE) 字段
- [x] 1.2 在 lifespan 的 ALTER TABLE 自动迁移中添加 share_token 和 share_expires 列
- [x] 1.3 扩展 BriefingDetail 响应 schema 添加 share_token、share_expires、share_url 字段

## 2. 分享管理 API

- [x] 2.1 实现 POST /api/briefings/{id}/share 端点（生成 token、设置过期时间、支持更新有效期）
- [x] 2.2 实现 DELETE /api/briefings/{id}/share 端点（清空 token 和 expires）
- [x] 2.3 实现 GET /api/share/{token} 公开端点（返回简报内容，校验 token 有效性和过期时间，404/410 状态码）

## 3. 前端分享交互

- [x] 3.1 在 BriefingsView 详情 modal 底部添加“分享”和“导出 Markdown”按钮（仅 status=done 时显示）
- [x] 3.2 实现分享对话框组件：有效期选择（1天/7天/30天/永久）、链接展示、复制按钮、更新有效期、取消分享
- [x] 3.3 在简报列表中已分享简报旁显示分享图标标识
- [x] 3.4 在 api/index.ts 添加分享相关的 API 方法（createShare、deleteShare、getSharedBriefing）

## 4. 分享阅读页面

- [x] 4.1 创建 ShareView.vue：报告式布局（720px 居中、16px 正文、行高 1.8）、固定浅色主题、Markdown 渲染
- [x] 4.2 实现 ShareView 的过期/失效提示页面（友好提示 + NewsHub 品牌）
- [x] 4.3 添加底部 "Powered by NewsHub" 品牌区域及链接回主站
- [x] 4.4 在 router/index.ts 添加 /share/:token 路由

## 5. Markdown 导出

- [x] 5.1 实现前端 Markdown 拼接逻辑（标题 + 元信息 + 正文 + 引用来源）和文件名特殊字符处理
- [x] 5.2 实现 Blob 下载触发逻辑，绑定到导出按钮

## 6. 部署验证

- [x] 6.1 Docker 构建部署 app + frontend
- [x] 6.2 E2E 验证：分享创建/复制/更新有效期/取消、分享页面阅读、过期提示、Markdown 导出下载
