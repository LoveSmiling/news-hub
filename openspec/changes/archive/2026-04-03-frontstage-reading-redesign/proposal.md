## 为什么

当前前端同时承担内容消费入口和后台管理工作台两类职责，但它们共享同一套布局和组件观感，导致首页、搜索、分享等内容页面缺少统一的阅读体验，对话、设置、源管理等工具页面也被迫混入面向内容消费的视觉诉求。随着热榜聚合、简报、分享和历史检索能力逐步完善，现有布局已经成为用户理解产品定位和提升页面完成度的主要阻力。

现在推进这项变更，是为了把产品从“功能集合”整理成“前台阅读体验 + 后台工具体验”的双层结构，在不改动后端接口和核心业务逻辑的前提下，建立更清晰的信息架构、可持续的设计令牌体系，以及后续页面重构的稳定边界。

## 变更内容

- 新增前台阅读壳，用于承载首页、搜索、历史、分享页以及简报阅读态等内容消费页面。
- 新增后台工具壳，用于承载对话、设置、日志、知识库、源管理等管理与操作页面，并保留效率优先的工作台属性。
- 为前台和后台引入共享的设计令牌体系，包括颜色、排版、圆角、阴影、背景氛围、间距和状态反馈规范。
- 重构首页与热榜列表组件的展示逻辑，使其从功能卡片网格转向更接近阅读产品的内容密度和信息层次。
- 调整搜索、历史、分享和简报详情的页面定位，使其成为统一前台内容体验的一部分，而不是零散的独立工具页。
- 保留现有后台业务功能与接口行为，重点修改其布局壳、导航层级和视觉一致性，而非重写业务交互。

## 功能 (Capabilities)

### 新增功能
- `frontstage-shell`: 定义前台阅读壳的布局、导航聚焦、品牌表达、背景氛围和响应式行为。
- `reading-surface-pages`: 定义首页、搜索、历史、分享页和简报阅读态的统一阅读体验要求。
- `admin-workspace-shell`: 定义后台工具壳的导航、内容容器、视觉层级和与共享设计令牌的对齐要求。

### 修改功能

无。

## 影响

- 前端布局与路由集成，主要涉及 frontend/src/App.vue、frontend/src/AppLayout.vue、frontend/src/router/index.ts。
- 首页与核心内容入口页面，主要涉及 frontend/src/views/HomeView.vue、frontend/src/components/HotCard.vue、frontend/src/views/SearchView.vue、frontend/src/views/HistoryView.vue、frontend/src/views/ShareView.vue、frontend/src/views/BriefingsView.vue。
- 后台工作台页面，主要涉及 frontend/src/views/ChatView.vue、frontend/src/views/SettingsView.vue、frontend/src/views/LogsView.vue、frontend/src/views/KnowledgeBaseView.vue、frontend/src/views/SourcesView.vue。
- 前端样式体系与公共组件层，可能新增共享主题令牌、布局壳组件和内容展示组件。
- 不涉及后端 API 变更，也不要求立即替换现有依赖，但可能引入更适合前台页面开发的样式组织方式。