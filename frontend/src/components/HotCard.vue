<template>
  <n-card :title="displayName" size="small" hoverable class="hot-card">
    <template #header-extra>
      <n-tag :type="categoryType" size="small" round>{{ category || '综合' }}</n-tag>
    </template>
    <div class="hot-list">
      <div
        v-for="(item, index) in items"
        :key="item.id"
        class="hot-item-wrapper"
      >
        <div class="hot-item" @click="toggleExpand(item.id)">
          <span class="hot-rank" :class="rankClass(index)">{{ index + 1 }}</span>
          <span class="hot-title" :title="item.title">{{ item.title }}</span>
          <span v-if="item.hot_value" class="hot-value">{{ item.hot_value }}</span>
        </div>
        <!-- Expanded detail -->
        <div v-if="expandedId === item.id" class="hot-detail">
          <div v-if="item.keywords && item.keywords.length" class="hot-keywords">
            <n-tag v-for="kw in item.keywords" :key="kw" size="tiny" round type="info" style="margin: 0 4px 4px 0">{{ kw }}</n-tag>
          </div>
          <div v-if="item.summary" class="hot-summary">{{ item.summary }}</div>
          <div v-else class="hot-summary-actions">
            <n-button
              size="tiny"
              type="primary"
              :loading="loadingId === item.id"
              @click.stop="handleGenerateSummary(item)"
            >
              生成摘要
            </n-button>
          </div>
          <div class="hot-link">
            <n-button text size="tiny" type="info" @click.stop="openLink(item.url, item.id)">查看原文 →</n-button>
          </div>
        </div>
      </div>
      <n-empty v-if="items.length === 0" description="暂无数据" size="small" />
    </div>
    <template #action>
      <div class="card-footer">
        <n-text depth="3" style="font-size: 12px">
          {{ updateTimeText }}
        </n-text>
      </div>
    </template>
  </n-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { NCard, NTag, NEmpty, NText, NButton } from 'naive-ui'
import type { HotItem } from '../api'
import { generateSummary } from '../api'
import { usePreferenceStore } from '../stores/preference'

const props = defineProps<{
  source: string
  displayName: string
  category: string | null
  items: HotItem[]
}>()

const prefStore = usePreferenceStore()
const expandedId = ref<number | null>(null)
const loadingId = ref<number | null>(null)

function toggleExpand(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

async function handleGenerateSummary(item: HotItem) {
  loadingId.value = item.id
  try {
    const res = await generateSummary(item.id)
    item.summary = res.summary
  } catch {
    // silently fail
  } finally {
    loadingId.value = null
  }
}

const categoryType = computed(() => {
  const map: Record<string, 'info' | 'success' | 'warning' | 'error'> = {
    '综合': 'info',
    '科技': 'success',
    '娱乐': 'warning',
    '新闻': 'error',
  }
  return map[props.category || '综合'] || 'info'
})

const updateTimeText = computed(() => {
  if (props.items.length === 0) return '暂无更新'
  const latest = props.items[0]?.collected_at
  if (!latest) return '暂无更新'
  const date = new Date(latest)
  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 60000)
  if (diff < 1) return '刚刚更新'
  if (diff < 60) return `${diff} 分钟前更新`
  if (diff < 1440) return `${Math.floor(diff / 60)} 小时前更新`
  return date.toLocaleDateString('zh-CN')
})

function rankClass(index: number) {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return ''
}

function openLink(url: string, itemId?: number) {
  if (itemId) prefStore.recordRead(itemId)
  if (url) window.open(url, '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.hot-card {
  height: 100%;
  min-width: 0;
  overflow: hidden;
}

.hot-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hot-item-wrapper {
  border-radius: 4px;
}

.hot-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.hot-item:hover {
  background-color: var(--n-color-hover, rgba(0, 0, 0, 0.04));
}

.hot-rank {
  min-width: 20px;
  height: 20px;
  line-height: 20px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  border-radius: 4px;
  color: var(--n-text-color-3, #999);
  flex-shrink: 0;
}

.rank-1 {
  background: #f5222d;
  color: #fff;
}

.rank-2 {
  background: #fa8c16;
  color: #fff;
}

.rank-3 {
  background: #faad14;
  color: #fff;
}

.hot-title {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-value {
  font-size: 12px;
  color: var(--n-text-color-3, #999);
  flex-shrink: 0;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}

.hot-detail {
  padding: 4px 4px 8px 32px;
  font-size: 13px;
}

.hot-keywords {
  margin-bottom: 4px;
}

.hot-summary {
  color: var(--n-text-color-2, #666);
  line-height: 1.5;
  margin-bottom: 4px;
}

.hot-summary-actions {
  margin-bottom: 4px;
}

.hot-link {
  text-align: right;
}
</style>
