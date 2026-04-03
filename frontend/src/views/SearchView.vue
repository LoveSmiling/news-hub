<template>
  <div class="search-view">
    <section class="search-hero">
      <h2>搜索你关心的话题</h2>
      <p>支持来源、分类与时间范围筛选，快速定位热点演化线索。</p>
    </section>

    <div class="search-bar">
      <n-input-group>
        <n-input
          v-model:value="keyword"
          placeholder="搜索热榜标题..."
          clearable
          size="large"
          @keyup.enter="doSearch"
        >
          <template #prefix>
            <n-icon><search-icon /></n-icon>
          </template>
        </n-input>
        <n-button type="primary" size="large" @click="doSearch" :loading="loading">
          搜索
        </n-button>
      </n-input-group>
    </div>

    <div class="filters">
      <n-space>
        <n-select
          v-model:value="filterSource"
          placeholder="来源"
          clearable
          style="width: 150px"
          :options="sourceOptions"
        />
        <n-select
          v-model:value="filterCategory"
          placeholder="分类"
          clearable
          style="width: 120px"
          :options="categoryOptions"
        />
        <n-date-picker
          v-model:value="dateRange"
          type="daterange"
          clearable
          :shortcuts="dateShortcuts"
        />
      </n-space>
    </div>

    <n-spin :show="loading">
      <div v-if="hasSearched" class="search-results">
        <n-text depth="3" class="result-count">
          共找到 {{ total }} 条结果
        </n-text>
        <div class="result-list">
          <div
            v-for="item in results"
            :key="item.id"
            class="result-item"
            @click="openLink(item.url)"
          >
            <div class="result-header">
              <n-tag :type="categoryType(item.category)" size="small" round>
                {{ item.source }}
              </n-tag>
              <n-text depth="3" class="result-time">
                {{ formatTime(item.collected_at) }}
              </n-text>
            </div>
            <div class="result-title">{{ item.title }}</div>
            <div v-if="item.hot_value" class="result-hot">
              <n-text depth="3">热度: {{ item.hot_value }}</n-text>
            </div>
          </div>
        </div>

        <div class="pagination" v-if="total > pageSize">
          <n-pagination
            v-model:page="currentPage"
            :page-size="pageSize"
            :item-count="total"
            @update:page="onPageChange"
          />
        </div>

        <n-empty v-if="!loading && results.length === 0" description="未找到相关结果" style="margin-top: 60px" />
      </div>
      <n-empty v-else-if="!loading" description="输入关键词搜索热榜标题" style="margin-top: 80px" />
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NInput, NInputGroup, NButton, NSelect, NDatePicker,
  NTag, NText, NPagination, NEmpty, NSpin, NSpace, NIcon,
} from 'naive-ui'
import { SearchOutline as SearchIcon } from '@vicons/ionicons5'
import { searchHotItems, fetchSources, type HotItem, type SourceInfo } from '../api'

const keyword = ref('')
const filterSource = ref<string | null>(null)
const filterCategory = ref<string | null>(null)
const dateRange = ref<[number, number] | null>(null)
const results = ref<HotItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const loading = ref(false)
const hasSearched = ref(false)
const sources = ref<SourceInfo[]>([])

const sourceOptions = computed(() =>
  sources.value.map(s => ({ label: s.display_name, value: s.name }))
)

const categoryOptions = [
  { label: '综合', value: '综合' },
  { label: '科技', value: '科技' },
  { label: '娱乐', value: '娱乐' },
  { label: '新闻', value: '新闻' },
]

const dateShortcuts = {
  '今天': () => {
    const now = Date.now()
    const start = new Date(); start.setHours(0, 0, 0, 0)
    return [start.getTime(), now] as [number, number]
  },
  '近7天': () => {
    const now = Date.now()
    return [now - 7 * 24 * 3600 * 1000, now] as [number, number]
  },
  '近30天': () => {
    const now = Date.now()
    return [now - 30 * 24 * 3600 * 1000, now] as [number, number]
  },
}

function categoryType(cat: string | null) {
  const map: Record<string, 'info' | 'success' | 'warning' | 'error'> = {
    '综合': 'info', '科技': 'success', '娱乐': 'warning', '新闻': 'error',
  }
  return map[cat || '综合'] || 'info'
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

function openLink(url: string) {
  if (url) window.open(url, '_blank', 'noopener,noreferrer')
}

async function doSearch() {
  if (!keyword.value.trim()) return
  loading.value = true
  hasSearched.value = true
  currentPage.value = 1
  await fetchResults()
}

async function fetchResults() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      q: keyword.value.trim(),
      page: currentPage.value,
      size: pageSize,
    }
    if (filterSource.value) params.source = filterSource.value
    if (filterCategory.value) params.category = filterCategory.value
    if (dateRange.value) {
      params.start_date = new Date(dateRange.value[0]).toISOString()
      params.end_date = new Date(dateRange.value[1]).toISOString()
    }
    const res = await searchHotItems(params)
    results.value = res.items
    total.value = res.total
  } catch (e) {
    console.error('Search failed:', e)
  } finally {
    loading.value = false
  }
}

function onPageChange() {
  fetchResults()
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
.search-view {
  max-width: 920px;
  margin: 0 auto;
}

.search-hero {
  border: 1px solid var(--front-border);
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--front-surface) 92%, transparent);
  padding: 14px 16px;
  margin-bottom: 14px;
}

.search-hero h2 {
  margin: 0;
  font-size: 20px;
}

.search-hero p {
  margin: 6px 0 0;
  color: var(--front-text-muted);
  font-size: 13px;
}

.search-bar {
  margin-bottom: 16px;
}

.filters {
  margin-bottom: 20px;
}

.result-count {
  display: block;
  margin-bottom: 12px;
  font-size: 13px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-item {
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
  border: 1px solid var(--front-border);
  background: color-mix(in srgb, var(--front-surface) 90%, transparent);
}

.result-item:hover {
  background-color: color-mix(in srgb, var(--front-accent) 8%, transparent);
  transform: translateY(-1px);
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.result-title {
  font-size: 15px;
  line-height: 1.5;
}

.result-time {
  font-size: 12px;
}

.result-hot {
  margin-top: 4px;
  font-size: 12px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
