<template>
  <n-space vertical :size="16">
    <n-h2 style="margin: 0">趋势分析</n-h2>

    <!-- Trending Topics -->
    <n-card title="跨平台热点话题" size="small">
      <template #header-extra>
        <n-select
          v-model:value="trendHours"
          :options="hourOptions"
          size="small"
          style="width: 120px"
          @update:value="loadTrends"
        />
      </template>
      <n-spin :show="trendLoading">
        <n-empty v-if="!trendLoading && topics.length === 0" description="暂无跨平台热点" />
        <div v-else class="topic-list">
          <n-card
            v-for="topic in topics"
            :key="topic.keyword"
            size="small"
            embedded
            class="topic-card"
          >
            <div class="topic-header">
              <n-tag type="warning" size="small" round>{{ topic.keyword }}</n-tag>
              <n-text depth="3" style="font-size: 12px">
                {{ topic.source_count }} 个平台 · {{ topic.item_count }} 条
              </n-text>
            </div>
            <div class="topic-items">
              <div v-for="item in topic.items" :key="item.id" class="topic-item">
                <n-tag size="tiny" :bordered="false">{{ item.source }}</n-tag>
                <a
                  :href="item.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="topic-link"
                >{{ item.title }}</a>
              </div>
            </div>
          </n-card>
        </div>
      </n-spin>
    </n-card>

    <!-- Burst Detection -->
    <n-card title="热点爆发检测" size="small">
      <n-spin :show="burstLoading">
        <n-empty v-if="!burstLoading && bursts.length === 0" description="暂无爆发话题" />
        <n-data-table
          v-else
          :columns="burstColumns"
          :data="bursts"
          :bordered="false"
          size="small"
        />
      </n-spin>
    </n-card>

    <!-- Hot Curve -->
    <n-card title="热度趋势曲线" size="small">
      <template #header-extra>
        <n-select
          v-model:value="curveSource"
          :options="sourceOptions"
          size="small"
          placeholder="选择来源"
          style="width: 150px"
          @update:value="loadCurve"
        />
      </template>
      <n-spin :show="curveLoading">
        <div v-if="curveData.length > 0" class="chart-container">
          <v-chart :option="chartOption" autoresize style="height: 300px" />
        </div>
        <n-empty v-else-if="!curveLoading" description="选择来源查看趋势" />
      </n-spin>
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NSpace, NH2, NCard, NTag, NText, NEmpty, NSpin, NSelect, NDataTable,
} from 'naive-ui'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { fetchTrends, fetchBursts, fetchHotCurve, fetchSources } from '../api'
import type { SourceInfo } from '../api'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const trendHours = ref(24)
const trendLoading = ref(false)
const burstLoading = ref(false)
const curveLoading = ref(false)
const topics = ref<any[]>([])
const bursts = ref<any[]>([])
const curveData = ref<any[]>([])
const curveSource = ref<string | null>(null)
const sources = ref<SourceInfo[]>([])

const hourOptions = [
  { label: '6小时', value: 6 },
  { label: '12小时', value: 12 },
  { label: '24小时', value: 24 },
  { label: '48小时', value: 48 },
  { label: '7天', value: 168 },
]

const sourceOptions = computed(() =>
  sources.value.map(s => ({ label: s.display_name, value: s.name }))
)

const burstColumns = [
  { title: '关键词', key: 'keyword', width: 120 },
  {
    title: '爆发倍率',
    key: 'burst_ratio',
    width: 100,
    render: (row: any) => h(NTag, { type: 'error', size: 'small' }, () => `×${row.burst_ratio}`),
  },
  { title: '近期出现', key: 'recent_count', width: 80 },
  { title: '平台数', key: 'source_count', width: 80 },
  {
    title: '来源',
    key: 'sources',
    render: (row: any) => row.sources.join(', '),
  },
]

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: curveData.value.map(d => {
      const dt = new Date(d.time)
      return `${dt.getMonth() + 1}/${dt.getDate()} ${dt.getHours()}:00`
    }),
  },
  yAxis: { type: 'value', name: '条目数' },
  series: [
    {
      data: curveData.value.map(d => d.count),
      type: 'line',
      smooth: true,
      areaStyle: { opacity: 0.3 },
    },
  ],
}))

async function loadTrends() {
  trendLoading.value = true
  try {
    const res = await fetchTrends(trendHours.value)
    topics.value = res.topics || []
  } finally {
    trendLoading.value = false
  }
}

async function loadBursts() {
  burstLoading.value = true
  try {
    const res = await fetchBursts()
    bursts.value = res.bursts || []
  } finally {
    burstLoading.value = false
  }
}

async function loadCurve() {
  if (!curveSource.value) return
  curveLoading.value = true
  try {
    const res = await fetchHotCurve(curveSource.value)
    curveData.value = res.data || []
  } finally {
    curveLoading.value = false
  }
}

onMounted(async () => {
  const [s] = await Promise.all([
    fetchSources(),
    loadTrends(),
    loadBursts(),
  ])
  sources.value = s
})
</script>

<style scoped>
.topic-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.topic-card {
  margin: 0;
}

.topic-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.topic-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.topic-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topic-link {
  color: var(--n-text-color);
  text-decoration: none;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topic-link:hover {
  text-decoration: underline;
}

.chart-container {
  width: 100%;
}
</style>
