## 为什么

首页热榜卡片当前固定两列布局（最大 1120px 容器），在宽屏显示器上浪费大量水平空间。每次刷新数据后卡片顺序随 API 返回值变化，用户需要反复翻找关注的信息源。卡片高度由内容撑开，内容多的卡片过长，导致页面纵向拉伸严重，一屏可见信息密度低。

## 变更内容

1. **自适应多列网格**：将 grid 从 `repeat(2, ...)` 改为 `repeat(auto-fill, minmax(380px, 1fr))`，同时将前台内容容器最大宽度从 1120px 放宽至 1520px，使宽屏下自动展示三列或更多列。
2. **卡片顺序持久化 + 拖拽排序**：引入 `vuedraggable@next`，将卡片排列顺序保存到 localStorage，刷新数据时保持用户设定的顺序不变。卡片 header 区域增加拖拽手柄，支持自由拖拽改变位置。
3. **整卡固定高度 + OverlayScrollbar**：卡片统一固定高度（420–450px），内容区使用 `overlayscrollbars` 实现滚动时浮现细条滚动条、停止后自动隐藏的交互，取代当前内容溢出直接裁切的行为。

## 功能 (Capabilities)

### 新增功能
- `card-drag-sort`: 热榜卡片拖拽排序与顺序持久化

### 修改功能
- `frontend-dashboard`: 网格布局从固定两列改为自适应多列，卡片从自由高度改为固定高度，内容区从溢出裁切改为 OverlayScrollbar 可滚动

## 影响

- **前端依赖**：新增 `vuedraggable@next`、`overlayscrollbars`、`overlayscrollbars-vue` 三个 npm 包
- **前端文件**：`HomeView.vue`（grid 布局 + draggable 集成）、`HotCard.vue`（固定高度 + OverlayScrollbar + 拖拽手柄）、`main.ts`（CSS 导入）、`styles/theme.css`（容器宽度）、新建 `stores/cardOrder.ts`（排序持久化）
- **后端/API**：无变更
- **其他页面**：仅影响首页 HomeView，不影响搜索、历史、趋势等页面
