## 上下文

首页热榜（HomeView）当前使用 CSS Grid 固定两列布局，容器最大宽度 1120px。卡片（HotCard）高度由内容撑开，无滚动支持，溢出内容被 `overflow: hidden` 裁切。卡片顺序完全依赖 API 返回顺序，无持久化机制。技术栈为 Vue 3 + Naive UI + Pinia + Vite。

参考项目 NewsNow 使用了 `auto-fill + minmax` 自适应列数、固定卡片高度 500px、overlayscrollbars 美化滚动条、@atlaskit/pragmatic-drag-and-drop 拖拽排序，验证了此类方案在类似场景下的可行性。

## 目标 / 非目标

**目标：**
- 宽屏（≥1440px）下首页自动展示三列或更多卡片列
- 卡片排列顺序由用户控制，支持拖拽调整，持久化存储，不受数据刷新影响
- 所有卡片统一固定高度，内容区可滚动浏览，滚动条在滚动时浮现、停止后自动隐藏

**非目标：**
- 不改变后端 API 接口或数据结构
- 不影响搜索、历史、趋势、简报等非首页页面
- 不实现跨设备同步（排序仅存 localStorage）
- 不改变分类筛选的逻辑（仍然是前端过滤）

## 决策

### D1: 网格自适应方案 — `auto-fill + minmax`

**选择**：`grid-template-columns: repeat(auto-fill, minmax(380px, 1fr))`

**替代方案**：
- 手动媒体查询断点（≥1400px 三列, ≥900px 两列, <900px 一列）：需要维护多个断点，不灵活
- 全宽无容器限制：与其他页面风格不统一

**理由**：浏览器自动计算列数，无需媒体查询。380px 最小宽度保证卡片内容可读。配合容器放宽至 1520px（`min(1520px, 100% - 32px)`），在 1440-1920px 屏幕上自然展示 3-4 列。保留 `@media (max-width: 768px)` 移动端强制单列。

### D2: 容器宽度 — 放宽至 1520px

**选择**：`.front-reading-container` 的 `width` 从 `min(1120px, 100% - 32px)` 改为 `min(1520px, 100% - 32px)`

**替代方案**：
- 仅首页覆盖容器宽度、保留全局 1120px：增加 CSS 特殊化，但更隔离
- 全宽布局（仅 padding）：与阅读型页面风格割裂

**理由**：1520px 在 1920px 屏幕上留有约 200px 两侧边距，视觉上不会太满。所有前台页面统一放宽，风格一致。如果后续发现搜索/历史页太宽，可以给那些页面单独设置 `max-width`。

### D3: 拖拽库 — vuedraggable@next

**选择**：`vuedraggable@next`（基于 SortableJS）

**替代方案**：
- `vue-draggable-plus`：更现代 API 但社区更小
- `@atlaskit/pragmatic-drag-and-drop`：NewsNow 使用，但无 Vue 封装，需自己写 composable
- 原生 HTML5 Drag API：零依赖但代码量大、移动端体验差

**理由**：vuedraggable@next 是 Vue 3 生态中最成熟的拖拽排序方案，社区大、文档全、支持 grid 布局。SortableJS 底层处理了 grid 拖拽的位置计算和动画。直接替换 `<div class="hot-grid">` 为 `<draggable>` 组件即可，改动最小。

### D4: 排序持久化 — localStorage + Pinia store

**选择**：新建 `stores/cardOrder.ts`（Pinia store），排序数据存 localStorage

**设计**：
- store 保存 `orderedSources: string[]`（source 标识的有序列表）
- API 返回 groups 后，按 `orderedSources` 排列；新出现的 source 追加末尾
- 拖拽结束时更新 store → 自动写入 localStorage
- 分类筛选在排序之后执行（先全局排序，再过滤）

### D5: 卡片高度 — 整卡固定 420px

**选择**：`.hot-card { height: 420px }`，配合 flex 布局让内容区自动填充

**替代方案**：
- 仅限制 `.hot-list` 区域 `max-height`：卡片高度不统一，grid 行不对齐
- 500px（与 NewsNow 一致）：过高，与"缩小卡片"的目标冲突

**理由**：420px 约可显示 10 条热搜条目（header ~44px + footer ~32px + 列表区 ~344px，每条约 34px）。所有卡片等高使 grid 行整齐对齐，视觉干净。

### D6: 滚动条方案 — overlayscrollbars

**选择**：`overlayscrollbars` + `overlayscrollbars-vue`，配置 `scrollbars.autoHide: 'scroll'`

**替代方案**：
- 纯 CSS `scrollbar-width: none` + `::-webkit-scrollbar { display: none }`：无可发现性，用户不知道内容可滚动
- 原生浏览器滚动条：样式粗糙，跨浏览器不一致

**理由**：overlayscrollbars 在滚动时短暂浮现细条滚动条，停止后自动消失。与 macOS 原生行为一致，既保持界面干净又提供可发现性暗示。Vue 官方适配器 `overlayscrollbars-vue` 提供 `OverlayScrollbarsComponent` 组件，直接包裹 `.hot-list` 即可。

**CSS 集成**：在 `.hot-card` 上设置 `display: flex; flex-direction: column`，通过 `:deep(.n-card__content) { flex: 1; min-height: 0; overflow: hidden }` 让 Naive UI card 的 content 区域成为弹性区域。

## 风险 / 权衡

- **[R1] grid 拖拽动画抖动** → SortableJS 内置了 grid 拖拽的位置计算，但在自适应列数变化时可能有边界情况。缓解：测试不同屏幕宽度下的拖拽行为，必要时设置 `animation: 150` 减少抖动。
- **[R2] NaiveUI n-card 内部 DOM 结构** → 通过 `:deep()` 穿透修改 n-card__content 的 flex 行为，如果 Naive UI 版本升级改变内部结构可能失效。缓解：锁定 naive-ui 版本，版本升级时验证。
- **[R3] 展开摘要时的滚动** → 用户点击卡片底部条目展开摘要后，展开内容可能超出可视区域。缓解：展开后调用 `scrollIntoView` 确保内容可见。
- **[R4] 首次访问无排序记录** → 首次访问时 localStorage 为空，卡片按 API 返回顺序显示。这是可接受的默认行为，用户拖拽后即持久化。
- **[R5] 容器放宽影响其他页面** → `front-reading-container` 是全局样式，放宽到 1520px 会影响搜索、历史等页面。这些页面当前内容较窄，放宽后不会有负面影响，但需视觉验证。
