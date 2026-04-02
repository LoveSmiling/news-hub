## 上下文

NewsHub 简报系统使用 LLM 对热榜内容做 Map-Reduce 摘要，生成 Markdown 格式的简报。当前简报仅存储在 PostgreSQL 的 `briefings` 表中，通过 `/api/briefings/{id}` 获取，无分享或导出机制。系统无认证体系，所有端点公开访问。

## 目标 / 非目标

**目标：**
- 为简报提供基于随机 token 的分享链接，支持过期时间管理（创建/更新/取消）
- 提供独立的分享阅读页面，报告式排版，固定浅色主题，展示 NewsHub 品牌
- 支持前端一键导出简报为 Markdown 文件

**非目标：**
- 不做用户认证/权限系统
- 不做 PDF 导出（仅 Markdown）
- 不做分享统计/访问计数
- 不做 SEO 优化（分享页无需被搜索引擎索引）

## 决策

### D1: 分享 token 方案 — 随机 token + 数据库字段

在 `briefings` 表新增 `share_token (VARCHAR(32), UNIQUE, NULLABLE)` 和 `share_expires (TIMESTAMP, NULLABLE)` 两个字段。

- **share_token = NULL** → 未分享
- **share_token 有值 + share_expires = NULL** → 永久分享
- **share_token 有值 + share_expires > now()** → 有效分享
- **share_token 有值 + share_expires ≤ now()** → 已过期

**备选方案：** JWT token（无状态验证）→ 不采用，因为取消分享需要吊销 token，无状态方案做不到。

### D2: 取消分享 — 清空 token（方案 A）

取消分享时将 `share_token` 和 `share_expires` 置为 NULL。旧链接永久失效。再次分享生成新 token。

**备选方案：** 设过期时间为过去（保留 token 历史）→ 不采用，无认证系统下保留历史无意义，清空更干净。

### D3: 更新有效期 — 复用 POST 端点

已分享状态下调 POST `/api/briefings/{id}/share` 会保持 token 不变，仅更新 `share_expires`。首次调用则生成新 token。

### D4: 公开 API 路径 — /api/share/{token}

分享查看端点使用 `/api/share/` 前缀，与 `/api/briefings/` 分离。语义上标识为公开访问端点，未来加认证时不受影响。

### D5: 分享页面 — 独立 Vue 组件 + 固定浅色

新建 `ShareView.vue`，路由 `/share/:token`。不使用 `NConfigProvider` 的主题切换，固定浅色背景。排版参考 Notion 分享页风格：最大宽度 720px、居中、正文 16px、行高 1.8。底部展示 "Powered by NewsHub" + 链接回主站。

### D6: Token 生成 — Python secrets 模块

使用 `secrets.token_urlsafe(24)` 生成 32 字符 URL 安全 token。足够防止枚举猜测。

### D7: 导出 — 纯前端实现

详情 modal 已持有完整数据（content + items），直接在前端拼接 Markdown 字符串，Blob 下载。不新增后端端点。

### D8: 数据库迁移 — 沿用 ALTER TABLE 模式

与 source-management 变更一致，在 `seed_sources()` / lifespan 阶段通过 try/except `ALTER TABLE ADD COLUMN` 自动添加字段，幂等执行。

## 风险 / 权衡

- **[风险] Token 枚举攻击** → 32 字符 URL-safe token 有 ~192 bit 熵，暴力猜测不可行
- **[风险] 过期检查仅在查询时进行** → 不做定时清理。过期 token 保留在数据库中直到用户取消分享或清理。影响微小（简报量不大）
- **[权衡] 纯前端导出无法保证格式一致性** → 接受。Markdown 本身就是纯文本，格式固定，前端拼接足够可靠
- **[权衡] 分享页不跟随暗色模式** → 接受。报告/文章类页面固定浅色更专业
