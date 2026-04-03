## 1. 依赖安装

- [x] 1.1 安装 npm 依赖：`vuedraggable@next`、`overlayscrollbars`、`overlayscrollbars-vue`
- [x] 1.2 在 `main.ts` 中导入 `overlayscrollbars/overlayscrollbars.css`

## 2. 容器与网格布局

- [x] 2.1 将 `styles/theme.css` 中 `.front-reading-container` 的 `width` 从 `min(1120px, 100% - 32px)` 改为 `min(1520px, 100% - 32px)`
- [x] 2.2 将 `HomeView.vue` 中 `.hot-grid` 的 `grid-template-columns` 从 `repeat(2, minmax(0, 1fr))` 改为 `repeat(auto-fill, minmax(380px, 1fr))`
- [x] 2.3 移除 `HomeView.vue` 中 `@media (max-width: 1200px)` 的 grid 单列覆盖（auto-fill 自动处理），保留 768px 移动端断点

## 3. 卡片固定高度 + OverlayScrollbar

- [x] 3.1 修改 `HotCard.vue` 的 `.hot-card` 样式：`height: 100%` 改为 `height: 420px`，添加 `display: flex; flex-direction: column`
- [x] 3.2 添加 `:deep(.n-card__content)` 样式：`flex: 1; min-height: 0; overflow: hidden`
- [x] 3.3 用 `OverlayScrollbarsComponent` 包裹 `.hot-list`，配置 `{ scrollbars: { autoHide: 'scroll' } }` 和 `defer`
- [x] 3.4 验证卡片内容滚动行为：超出内容可滚轮滚动，滚动时细条浮现，停止后隐藏

## 4. 排序持久化 Store

- [x] 4.1 新建 `stores/cardOrder.ts` Pinia store，包含 `orderedSources` 状态和 localStorage 读写逻辑
- [x] 4.2 实现排序函数：按 `orderedSources` 排列 groups，新 source 追加末尾，已删除 source 自动清理
- [x] 4.3 在 `HomeView.vue` 中集成 store：`loadData()` 后调用排序，`filteredGroups` 基于排序后的数据

## 5. 拖拽排序集成

- [x] 5.1 在 `HomeView.vue` 中将 `<div class="hot-grid">` 替换为 `<draggable>` 组件，配置 `item-key`、`handle`、`animation` 等属性
- [x] 5.2 在 `HotCard.vue` 的 `header-extra` 区域添加拖拽手柄图标（⋮⋮），设置 `cursor: grab` 样式
- [x] 5.3 实现 `onEnd` 回调：拖拽完成后更新 cardOrder store，持久化到 localStorage
- [x] 5.4 验证分类筛选下的拖拽行为：筛选状态下拖拽后切回全部分类，顺序正确

## 6. 验证与收尾

- [x] 6.1 测试响应式：1920px（3-4列）、1440px（3列）、1200px（2列）、768px（1列）
- [x] 6.2 测试数据刷新后卡片顺序保持不变
- [x] 6.3 测试展开摘要时在固定高度卡片内的滚动表现
- [x] 6.4 测试暗黑模式下 overlayscrollbars 滚动条样式
