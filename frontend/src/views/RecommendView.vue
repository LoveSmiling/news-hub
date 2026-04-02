<template>
  <n-space vertical :size="16">
    <n-h2 style="margin: 0">为你推荐</n-h2>

    <n-card size="small">
      <template #header>
        <n-space align="center">
          <span>个性推荐</span>
          <n-tag v-if="strategy" size="tiny" :type="strategy === 'category_filter' ? 'success' : 'info'" round>
            {{ strategy === 'category_filter' ? '偏好推荐' : '热门推荐' }}
          </n-tag>
        </n-space>
      </template>
      <template #header-extra>
        <n-button size="tiny" @click="loadRecommendations" :loading="loading">刷新</n-button>
      </template>

      <n-spin :show="loading">
        <n-empty v-if="!loading && items.length === 0" description="暂无推荐内容，请先设置偏好" />
        <div v-else class="recommend-list">
          <div
            v-for="(item, index) in items"
            :key="item.id"
            class="recommend-item"
            @click="handleClick(item)"
          >
            <span class="rec-rank">{{ index + 1 }}</span>
            <div class="rec-content">
              <div class="rec-title">{{ item.title }}</div>
              <n-space :size="4" style="margin-top: 4px">
                <n-tag v-if="item.category" size="tiny" :bordered="false">{{ item.category }}</n-tag>
                <n-tag v-for="kw in (item.keywords || []).slice(0, 3)" :key="kw" size="tiny" type="info" :bordered="false">{{ kw }}</n-tag>
              </n-space>
            </div>
            <n-text depth="3" style="font-size: 12px; flex-shrink: 0">
              {{ item.hot_value || '' }}
            </n-text>
          </div>
        </div>
      </n-spin>
    </n-card>

    <n-card size="small" title="偏好设置" style="margin-top: 8px">
      <n-text depth="3" style="font-size: 13px; display: block; margin-bottom: 8px">
        前往设置页配置分类偏好以获得更精准的推荐
      </n-text>
      <n-button size="small" @click="router.push('/settings')">前往设置</n-button>
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NSpace, NH2, NCard, NTag, NText, NButton, NEmpty, NSpin } from 'naive-ui'
import type { HotItem } from '../api'
import { fetchRecommendations } from '../api'
import { usePreferenceStore } from '../stores/preference'

const router = useRouter()
const prefStore = usePreferenceStore()

const items = ref<HotItem[]>([])
const strategy = ref('')
const loading = ref(false)

async function loadRecommendations() {
  loading.value = true
  try {
    const res = await fetchRecommendations(
      prefStore.preferredCategories,
      prefStore.readHistory,
    )
    items.value = res.items
    strategy.value = res.strategy
  } finally {
    loading.value = false
  }
}

function handleClick(item: HotItem) {
  prefStore.recordRead(item.id)
  if (item.url) window.open(item.url, '_blank', 'noopener,noreferrer')
}

onMounted(loadRecommendations)
</script>

<style scoped>
.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recommend-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.recommend-item:hover {
  background-color: var(--n-color-hover, rgba(0, 0, 0, 0.04));
}

.rec-rank {
  min-width: 22px;
  height: 22px;
  line-height: 22px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--n-text-color-3, #999);
  flex-shrink: 0;
}

.rec-content {
  flex: 1;
  min-width: 0;
}

.rec-title {
  font-size: 14px;
  line-height: 1.4;
}
</style>
