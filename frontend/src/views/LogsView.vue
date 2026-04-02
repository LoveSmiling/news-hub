<template>
  <n-space vertical :size="16">
    <n-h2 style="margin: 0">AI 日志</n-h2>

    <!-- Stats Overview Cards -->
    <n-spin :show="statsLoading">
      <div class="stats-grid" v-if="stats">
        <n-card size="small" embedded>
          <n-statistic label="总调用次数" :value="stats.overview.total_calls" />
        </n-card>
        <n-card size="small" embedded>
          <n-statistic label="成功 / 失败">
            <template #default>
              <n-text type="success">{{ stats.overview.success_count }}</n-text>
              <n-text depth="3"> / </n-text>
              <n-text type="error">{{ stats.overview.error_count }}</n-text>
            </template>
          </n-statistic>
        </n-card>
        <n-card size="small" embedded>
          <n-statistic label="总消耗 Tokens" :value="stats.overview.total_tokens" />
        </n-card>
        <n-card size="small" embedded>
          <n-statistic label="Prompt / Completion">
            <template #default>
              {{ stats.overview.total_prompt_tokens }} / {{ stats.overview.total_completion_tokens }}
            </template>
          </n-statistic>
        </n-card>
        <n-card size="small" embedded>
          <n-statistic label="平均延迟">
            <template #default>{{ stats.overview.avg_latency_ms }}ms</template>
          </n-statistic>
        </n-card>
      </div>
    </n-spin>

    <!-- Token Timeline Chart -->
    <n-card title="调用趋势" size="small" v-if="stats && stats.timeline.length > 0">
      <v-chart :option="chartOption" autoresize style="height: 260px" />
    </n-card>

    <!-- Per-Action Breakdown -->
    <n-card title="按操作类型统计" size="small" v-if="stats && stats.by_action.length > 0">
      <n-data-table :columns="actionColumns" :data="stats.by_action" :bordered="false" size="small" />
    </n-card>

    <!-- Operations -->
    <n-card title="操作" size="small">
      <n-space>
        <n-button type="primary" :loading="enriching" @click="handleEnrich">
          手动生成关键词 (补全缺失)
        </n-button>
        <n-select
          v-model:value="statsHours"
          :options="hoursOptions"
          style="width: 140px"
          @update:value="loadStats"
        />
      </n-space>
      <n-text v-if="enrichResult" depth="3" style="display: block; margin-top: 8px; font-size: 13px">
        处理 {{ enrichResult.total }} 条，成功 {{ enrichResult.success }}，失败 {{ enrichResult.errors }}
      </n-text>
    </n-card>

    <!-- Log List -->
    <n-card title="调用日志" size="small">
      <template #header-extra>
        <n-space :size="8">
          <n-select
            v-model:value="filterAction"
            :options="actionFilterOptions"
            placeholder="操作类型"
            clearable
            style="width: 160px"
            size="small"
            @update:value="loadLogs"
          />
          <n-select
            v-model:value="filterSuccess"
            :options="successFilterOptions"
            placeholder="状态"
            clearable
            style="width: 100px"
            size="small"
            @update:value="loadLogs"
          />
        </n-space>
      </template>

      <n-spin :show="logsLoading">
        <n-data-table :columns="logColumns" :data="logs" :bordered="false" size="small" max-height="500" />
      </n-spin>

      <n-space justify="center" style="margin-top: 12px" v-if="logTotal > logPageSize">
        <n-pagination
          v-model:page="logPage"
          :page-count="Math.ceil(logTotal / logPageSize)"
          @update:page="loadLogs"
        />
      </n-space>
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NH2, NCard, NSpace, NText, NButton, NSpin, NStatistic, NTag,
  NDataTable, NSelect, NPagination, useMessage,
} from 'naive-ui'
import type { DataTableColumn } from 'naive-ui'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import {
  fetchLogs, fetchLogStats, triggerEnrichKeywords,
  type LogItem, type LogStats,
} from '../api'

use([BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const message = useMessage()

// ---- Stats ----
const stats = ref<LogStats | null>(null)
const statsLoading = ref(false)
const statsHours = ref(24)

const hoursOptions = [
  { label: '最近 6 小时', value: 6 },
  { label: '最近 24 小时', value: 24 },
  { label: '最近 3 天', value: 72 },
  { label: '最近 7 天', value: 168 },
  { label: '最近 30 天', value: 720 },
]

async function loadStats() {
  statsLoading.value = true
  try {
    stats.value = await fetchLogStats(statsHours.value)
  } finally {
    statsLoading.value = false
  }
}

// ---- Chart ----
const chartOption = computed(() => {
  if (!stats.value?.timeline.length) return {}
  const timeline = stats.value.timeline
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['调用次数', 'Tokens'] },
    grid: { left: 50, right: 50, top: 30, bottom: 30 },
    xAxis: {
      type: 'category',
      data: timeline.map(t => {
        const d = new Date(t.time)
        return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:00`
      }),
    },
    yAxis: [
      { type: 'value', name: '调用', position: 'left' },
      { type: 'value', name: 'Tokens', position: 'right' },
    ],
    series: [
      {
        name: '调用次数',
        type: 'bar',
        data: timeline.map(t => t.calls),
        itemStyle: { color: '#63e2b7' },
      },
      {
        name: 'Tokens',
        type: 'line',
        yAxisIndex: 1,
        data: timeline.map(t => t.tokens),
        itemStyle: { color: '#70c0e8' },
      },
    ],
  }
})

// ---- Action Table ----
const actionColumns: DataTableColumn[] = [
  { title: '操作', key: 'action', width: 160, render: (row: any) => h(NTag, { size: 'small', type: 'info', round: true }, () => actionLabel(row.action)) },
  { title: '调用次数', key: 'calls', width: 100 },
  { title: '总 Tokens', key: 'tokens', width: 120 },
  { title: '成功', key: 'successes', width: 80 },
  { title: '失败', key: 'errors', width: 80, render: (row: any) => row.errors > 0 ? h(NText, { type: 'error' }, () => row.errors) : '0' },
  { title: '平均延迟(ms)', key: 'avg_latency_ms', width: 120 },
]

// ---- Logs ----
const logs = ref<LogItem[]>([])
const logsLoading = ref(false)
const logPage = ref(1)
const logPageSize = ref(50)
const logTotal = ref(0)
const filterAction = ref<string | null>(null)
const filterSuccess = ref<boolean | null>(null)

const actionFilterOptions = [
  { label: '关键词提取', value: 'keyword_extract' },
  { label: '批量摘要', value: 'summarize_batch' },
  { label: '单条摘要', value: 'summarize_single' },
  { label: 'Embedding', value: 'embedding' },
  { label: '批量Embedding', value: 'embedding_batch' },
  { label: '聊天', value: 'chat' },
]

const successFilterOptions = [
  { label: '成功', value: true },
  { label: '失败', value: false },
]

function actionLabel(action: string): string {
  const map: Record<string, string> = {
    keyword_extract: '关键词提取',
    summarize_batch: '批量摘要',
    summarize_single: '单条摘要',
    embedding: 'Embedding',
    embedding_batch: '批量Embedding',
    chat: '聊天',
  }
  return map[action] || action
}

const logColumns: DataTableColumn[] = [
  {
    title: '时间', key: 'created_at', width: 160,
    render: (row: any) => new Date(row.created_at).toLocaleString('zh-CN'),
  },
  {
    title: '操作', key: 'action', width: 120,
    render: (row: any) => h(NTag, { size: 'small', type: 'info', round: true }, () => actionLabel(row.action)),
  },
  {
    title: '状态', key: 'success', width: 70,
    render: (row: any) => h(NTag, { size: 'small', type: row.success ? 'success' : 'error', round: true }, () => row.success ? '成功' : '失败'),
  },
  { title: '模型', key: 'model', width: 140, ellipsis: { tooltip: true } },
  { title: 'Prompt', key: 'prompt_tokens', width: 80, render: (row: any) => row.prompt_tokens ?? '-' },
  { title: 'Completion', key: 'completion_tokens', width: 100, render: (row: any) => row.completion_tokens ?? '-' },
  { title: '总Tokens', key: 'total_tokens', width: 90, render: (row: any) => row.total_tokens ?? '-' },
  { title: '延迟(ms)', key: 'latency_ms', width: 90, render: (row: any) => row.latency_ms ?? '-' },
  { title: '提供商', key: 'provider_name', width: 120, ellipsis: { tooltip: true } },
  {
    title: '详情', key: 'detail', width: 200,
    render: (row: any) => {
      if (row.error_message) return h(NText, { type: 'error', style: 'font-size:12px' }, () => row.error_message)
      if (row.meta) return h(NText, { depth: 3, style: 'font-size:12px' }, () => JSON.stringify(row.meta))
      return '-'
    },
    ellipsis: { tooltip: true },
  },
]

async function loadLogs() {
  logsLoading.value = true
  try {
    const params: any = { hours: statsHours.value, page: logPage.value, page_size: logPageSize.value }
    if (filterAction.value) params.action = filterAction.value
    if (filterSuccess.value !== null && filterSuccess.value !== undefined) params.success = filterSuccess.value
    const res = await fetchLogs(params)
    logs.value = res.items
    logTotal.value = res.total
  } finally {
    logsLoading.value = false
  }
}

// ---- Enrich ----
const enriching = ref(false)
const enrichResult = ref<{ total: number; success: number; errors: number } | null>(null)

async function handleEnrich() {
  enriching.value = true
  enrichResult.value = null
  try {
    enrichResult.value = await triggerEnrichKeywords(50)
    if (enrichResult.value.success > 0) {
      message.success(`成功提取 ${enrichResult.value.success} 条关键词`)
    } else if (enrichResult.value.total === 0) {
      message.info('没有需要补全关键词的条目')
    } else {
      message.warning('关键词提取全部失败，请检查 AI 配置')
    }
    await loadStats()
    await loadLogs()
  } catch {
    message.error('关键词生成失败，请检查 AI 服务配置')
  } finally {
    enriching.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadStats(), loadLogs()])
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
</style>
