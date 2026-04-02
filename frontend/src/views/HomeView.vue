<template>
  <div class="home-view">
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
      <div class="hot-grid">
        <HotCard
          v-for="group in filteredGroups"
          :key="group.source"
          :source="group.source"
          :display-name="group.display_name"
          :category="group.category"
          :items="group.items"
        />
      </div>
      <n-empty v-if="!loading && filteredGroups.length === 0" description="暂无热榜数据" style="margin-top: 80px" />
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NTabs, NTabPane, NSpin, NEmpty, NText } from 'naive-ui'
import HotCard from '../components/HotCard.vue'
import { fetchGroupedHot, type GroupedHot } from '../api'

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

const autoRefreshText = computed(() => {
  if (!lastRefresh.value) return ''
  return `上次刷新: ${lastRefresh.value.toLocaleTimeString('zh-CN')} · 每 5 分钟自动刷新`
})

async function loadData() {
  loading.value = true
  try {
    groups.value = await fetchGroupedHot()
    lastRefresh.value = new Date()
  } catch (e) {
    console.error('Failed to fetch hot data:', e)
  } finally {
    loading.value = false
  }
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
  padding: 0;
}

.category-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.refresh-info {
  flex-shrink: 0;
}

.hot-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  min-width: 0;
}

@media (max-width: 1200px) {
  .hot-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hot-grid {
    grid-template-columns: 1fr;
  }
}
</style>

