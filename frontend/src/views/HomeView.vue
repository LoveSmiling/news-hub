<template>
  <div class="home-view">
    <section class="home-hero">
      <p class="hero-kicker">NEWS FEED</p>
      <h1 class="hero-title">今天值得关注的热搜与话题</h1>
      <p class="hero-sub">聚合全网实时趋势，优先展示最具讨论价值的内容信号。</p>
    </section>

    <div class="category-bar">
      <n-tabs v-model:value="activeCategory" type="segment" @update:value="onCategoryChange">
        <n-tab-pane v-for="cat in categories" :key="cat.value" :name="cat.value" :tab="cat.label" />
      </n-tabs>
      <div class="refresh-info">
        <n-text depth="3" style="font-size: 12px">
          {{ autoRefreshText }}
        </n-text>
      </div>
    </div>

    <n-spin :show="loading" description="加载中...">
      <draggable
        v-model="sortedGroups"
        item-key="source"
        class="hot-grid"
        handle=".drag-handle"
        :animation="150"
        ghost-class="drag-ghost"
        @end="onDragEnd"
      >
        <template #item="{ element: group }">
          <HotCard
            :source="group.source"
            :display-name="group.display_name"
            :category="group.category"
            :items="group.items"
          />
        </template>
      </draggable>
      <n-empty v-if="!loading && filteredGroups.length === 0" description="暂无热榜数据" style="margin-top: 80px" />
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NTabs, NTabPane, NSpin, NEmpty, NText } from 'naive-ui'
import draggable from 'vuedraggable'
import HotCard from '../components/HotCard.vue'
import { fetchGroupedHot, type GroupedHot } from '../api'
import { useCardOrderStore } from '../stores/cardOrder'

const cardOrderStore = useCardOrderStore()

const categories = [
  { label: '全部', value: 'all' },
  { label: '综合', value: '综合' },
  { label: '科技', value: '科技' },
  { label: '娱乐', value: '娱乐' },
  { label: '新闻', value: '新闻' },
]

const activeCategory = ref('all')
const groups = ref<GroupedHot[]>([])
const loading = ref(false)
const lastRefresh = ref<Date | null>(null)
let refreshTimer: ReturnType<typeof setInterval> | null = null

const filteredGroups = computed(() => {
  if (activeCategory.value === 'all') return groups.value
  return groups.value.filter(g => g.category === activeCategory.value)
})

const sortedGroups = computed({
  get: () => filteredGroups.value,
  set: (newVal: GroupedHot[]) => {
    if (activeCategory.value === 'all') {
      groups.value = newVal
      cardOrderStore.updateOrder(newVal.map(g => g.source))
    } else {
      // Update global order based on relative positions within filtered view
      const filteredSources = new Set(newVal.map(g => g.source))
      const result: GroupedHot[] = []
      let filteredIdx = 0
      for (const g of groups.value) {
        if (filteredSources.has(g.source)) {
          result.push(newVal[filteredIdx++])
        } else {
          result.push(g)
        }
      }
      groups.value = result
      cardOrderStore.updateOrder(result.map(g => g.source))
    }
  },
})

const autoRefreshText = computed(() => {
  if (!lastRefresh.value) return ''
  return `上次刷新: ${lastRefresh.value.toLocaleTimeString('zh-CN')} · 每 5 分钟自动刷新`
})

async function loadData() {
  loading.value = true
  try {
    const raw = await fetchGroupedHot()
    groups.value = cardOrderStore.sortGroups(raw)
    lastRefresh.value = new Date()
  } catch (e) {
    console.error('Failed to fetch hot data:', e)
  } finally {
    loading.value = false
  }
}

function onDragEnd() {
  // Order already updated via sortedGroups setter
}

function onCategoryChange() {
  // 分类切换为前端过滤，无需重新请求
}

onMounted(() => {
  loadData()
  refreshTimer = setInterval(loadData, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.home-view {
  padding: 2px 0 12px;
}

.home-hero {
  border: 1px solid var(--front-border);
  border-radius: var(--radius-lg);
  background:
    radial-gradient(620px 240px at -8% -20%, rgba(241, 77, 66, 0.22), transparent 60%),
    linear-gradient(140deg, var(--front-surface), color-mix(in srgb, var(--front-surface) 75%, transparent));
  box-shadow: var(--front-shadow);
  padding: 20px 22px;
  margin-bottom: 14px;
}

.hero-kicker {
  margin: 0;
  font-size: 12px;
  letter-spacing: 1.8px;
  color: var(--front-accent);
  font-weight: 700;
}

.hero-title {
  margin: 6px 0;
  font-size: clamp(22px, 2.2vw, 30px);
  line-height: 1.28;
}

.hero-sub {
  margin: 0;
  color: var(--front-text-muted);
  font-size: 14px;
}

.category-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 12px;
}

.refresh-info {
  flex-shrink: 0;
}

.hot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 14px;
  min-width: 0;
}

@media (max-width: 768px) {
  .home-hero {
    padding: 16px;
  }

  .hero-title {
    font-size: 22px;
  }

  .hot-grid {
    grid-template-columns: 1fr;
  }
}

.drag-ghost {
  opacity: 0.4;
}
</style>

