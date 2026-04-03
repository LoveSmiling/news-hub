<template>
  <div class="history-view">
    <section class="history-hero">
      <h2>历史热榜回看</h2>
      <p>按来源与日期回溯热点内容，追踪话题的传播轨迹。</p>
    </section>

    <div class="history-controls">
      <n-space align="center">
        <n-select
          v-model:value="selectedSource"
          placeholder="选择来源"
          style="width: 180px"
          :options="sourceOptions"
          @update:value="onSourceChange"
        />
        <n-date-picker
          v-model:value="selectedDate"
          type="date"
          :is-date-disabled="isDateDisabled"
          @update:value="onDateChange"
        />
      </n-space>
    </div>

    <n-spin :show="loading">
      <div v-if="selectedSource && selectedDate" class="history-content">
        <n-text depth="3" class="history-info">
          {{ currentSourceLabel }} · {{ formatDate(selectedDate) }} · 共 {{ total }} 条
        </n-text>

        <div class="history-list">
          <div
            v-for="(item, index) in items"
            :key="item.id"
            class="history-item"
            @click="openLink(item.url)"
          >
            <span class="item-rank" :class="rankClass(index)">{{ index + 1 }}</span>
            <span class="item-title" :title="item.title">{{ item.title }}</span>
            <span v-if="item.hot_value" class="item-hot">{{ item.hot_value }}</span>
          </div>
        </div>

        <div class="pagination" v-if="total > pageSize">
          <n-pagination
            v-model:page="currentPage"
            :page-size="pageSize"
            :item-count="total"
            @update:page="fetchData"
          />
        </div>

        <n-empty v-if="!loading && items.length === 0" description="该日期暂无数据" style="margin-top: 60px" />
      </div>
      <n-empty v-else-if="!loading" description="选择来源和日期查看历史热榜" style="margin-top: 80px" />
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NSelect, NDatePicker, NSpin, NEmpty, NText, NPagination, NSpace,
} from 'naive-ui'
import {
  fetchSources, fetchHistory, fetchAvailableDates,
  type HotItem, type SourceInfo,
} from '../api'

const sources = ref<SourceInfo[]>([])
const selectedSource = ref<string | null>(null)
const selectedDate = ref<number | null>(null)
const availableDates = ref<Set<string>>(new Set())
const items = ref<HotItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 50
const loading = ref(false)

const sourceOptions = computed(() =>
  sources.value.map(s => ({ label: s.display_name, value: s.name }))
)

const currentSourceLabel = computed(() => {
  const s = sources.value.find(s => s.name === selectedSource.value)
  return s?.display_name || selectedSource.value
})

function formatDate(ts: number) {
  return new Date(ts).toLocaleDateString('zh-CN')
}

function isDateDisabled(ts: number) {
  if (availableDates.value.size === 0) return false
  const d = new Date(ts).toISOString().slice(0, 10)
  return !availableDates.value.has(d)
}

function rankClass(index: number) {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return ''
}

function openLink(url: string) {
  if (url) window.open(url, '_blank', 'noopener,noreferrer')
}

async function onSourceChange(source: string) {
  selectedSource.value = source
  items.value = []
  total.value = 0
  selectedDate.value = null
  // Load available dates for this source
  try {
    const res = await fetchAvailableDates(source)
    availableDates.value = new Set(res.dates)
    // Auto-select the most recent date
    if (res.dates.length > 0) {
      const latest = res.dates[0]
      selectedDate.value = new Date(latest + 'T00:00:00').getTime()
      await fetchData()
    }
  } catch (e) {
    console.error('Failed to load dates:', e)
  }
}

async function onDateChange() {
  if (selectedSource.value && selectedDate.value) {
    currentPage.value = 1
    await fetchData()
  }
}

async function fetchData() {
  if (!selectedSource.value || !selectedDate.value) return
  loading.value = true
  try {
    const dateStr = new Date(selectedDate.value).toISOString().slice(0, 10)
    const res = await fetchHistory(selectedSource.value, dateStr, currentPage.value, pageSize)
    items.value = res.items
    total.value = res.total
  } catch (e) {
    console.error('Failed to load history:', e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    sources.value = await fetchSources()
  } catch (e) {
    console.error('Failed to load sources:', e)
  }
})
</script>

<style scoped>
.history-view {
  max-width: 920px;
  margin: 0 auto;
}

.history-hero {
  border: 1px solid var(--front-border);
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--front-surface) 90%, transparent);
  padding: 14px 16px;
  margin-bottom: 14px;
}

.history-hero h2 {
  margin: 0;
  font-size: 20px;
}

.history-hero p {
  margin: 6px 0 0;
  color: var(--front-text-muted);
  font-size: 13px;
}

.history-controls {
  margin-bottom: 16px;
}

.history-info {
  display: block;
  margin-bottom: 12px;
  font-size: 13px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
  border: 1px solid var(--front-border);
  background: color-mix(in srgb, var(--front-surface) 92%, transparent);
}

.history-item:hover {
  background-color: color-mix(in srgb, var(--front-accent) 8%, transparent);
  transform: translateY(-1px);
}

.item-rank {
  min-width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  border-radius: 4px;
  color: var(--front-text-muted);
  flex-shrink: 0;
}

.rank-1 { background: #f5222d; color: #fff; }
.rank-2 { background: #fa8c16; color: #fff; }
.rank-3 { background: #faad14; color: #fff; }

.item-title {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-hot {
  font-size: 12px;
  color: var(--front-text-muted);
  flex-shrink: 0;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
