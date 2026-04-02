<template>
  <n-space vertical :size="16">
    <n-h2 style="margin: 0">知识库管理</n-h2>

    <!-- Overview Stats -->
    <n-card title="索引概览" size="small">
      <n-spin :show="statsLoading">
        <n-space vertical :size="12">
          <n-space :size="24" align="center">
            <n-statistic label="总条目" :value="stats.total" />
            <n-statistic label="已索引" :value="stats.indexed" />
            <n-statistic label="覆盖率">
              <template #default>
                <n-text :type="stats.coverage_pct >= 80 ? 'success' : stats.coverage_pct >= 50 ? 'warning' : 'error'">
                  {{ stats.coverage_pct.toFixed(1) }}%
                </n-text>
              </template>
            </n-statistic>
          </n-space>
          <n-progress
            type="line"
            :percentage="stats.coverage_pct"
            :status="stats.coverage_pct >= 80 ? 'success' : stats.coverage_pct >= 50 ? 'warning' : 'error'"
            :height="8"
            :show-indicator="false"
          />
          <!-- Per-source breakdown -->
          <n-collapse v-if="stats.by_source.length > 0">
            <n-collapse-item title="按来源查看" name="sources">
              <n-data-table
                :columns="sourceColumns"
                :data="stats.by_source"
                :bordered="false"
                size="small"
                :pagination="false"
                max-height="300"
              />
            </n-collapse-item>
          </n-collapse>
        </n-space>
      </n-spin>
    </n-card>

    <!-- Build Operations -->
    <n-card title="构建操作" size="small">
      <n-space vertical :size="12">
        <n-space :size="12" align="center">
          <n-button type="primary" size="small" :loading="taskRunning" @click="startTask('incremental')">
            增量更新
          </n-button>
          <n-button type="warning" size="small" :loading="taskRunning" @click="confirmFullRebuild">
            全量重建
          </n-button>
          <n-text v-if="taskRunning" depth="3" style="font-size: 13px">
            任务进行中...
          </n-text>
        </n-space>
        <!-- Task progress -->
        <template v-if="currentTask">
          <n-space vertical :size="4">
            <n-space :size="8" align="center">
              <n-tag :type="taskStatusType" size="small">{{ taskStatusLabel }}</n-tag>
              <n-text depth="3" style="font-size: 12px">
                {{ currentTask.progress }} / {{ currentTask.total || '?' }}
              </n-text>
            </n-space>
            <n-progress
              type="line"
              :percentage="taskPercentage"
              :status="currentTask.status === 'failed' ? 'error' : 'success'"
              :height="6"
            />
            <n-text v-if="currentTask.error" type="error" style="font-size: 12px">
              {{ currentTask.error }}
            </n-text>
          </n-space>
        </template>
      </n-space>
    </n-card>

    <!-- Semantic Search -->
    <n-card title="语义搜索" size="small">
      <n-space vertical :size="12">
        <n-space :size="8" align="center">
          <n-input
            v-model:value="searchQuery"
            placeholder="输入搜索内容..."
            style="width: 400px"
            size="small"
            clearable
            @keydown.enter="handleSearch"
          />
          <n-input-number
            v-model:value="searchLimit"
            :min="1"
            :max="50"
            style="width: 100px"
            size="small"
          >
            <template #suffix>条</template>
          </n-input-number>
          <n-button type="primary" size="small" :loading="searchLoading" @click="handleSearch">
            搜索
          </n-button>
        </n-space>

        <!-- Search Results -->
        <n-spin :show="searchLoading">
          <n-list v-if="searchResults.length > 0" bordered>
            <n-list-item v-for="item in searchResults" :key="item.id">
              <n-thing>
                <template #header>
                  <n-space :size="8" align="center">
                    <n-a :href="item.url" target="_blank">{{ item.title }}</n-a>
                    <n-tag type="info" size="small" round>
                      {{ (item.score * 100).toFixed(1) }}%
                    </n-tag>
                  </n-space>
                </template>
                <template #header-extra>
                  <n-tag size="small">{{ item.source }}</n-tag>
                </template>
                <template #description>
                  <n-text depth="3" style="font-size: 12px">
                    {{ formatTime(item.collected_at) }}
                    <template v-if="item.keywords">
                      &nbsp;·&nbsp;{{ item.keywords }}
                    </template>
                  </n-text>
                </template>
                <n-ellipsis :line-clamp="2" v-if="item.summary">
                  {{ item.summary }}
                </n-ellipsis>
              </n-thing>
            </n-list-item>
          </n-list>
          <n-empty v-else-if="searchDone" description="未找到相关结果" />
        </n-spin>
      </n-space>
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import {
  NH2, NCard, NSpace, NStatistic, NProgress, NButton, NInput, NInputNumber,
  NList, NListItem, NThing, NTag, NText, NA, NEllipsis, NEmpty, NSpin,
  NCollapse, NCollapseItem, NDataTable, useMessage, useDialog,
  type DataTableColumns,
} from 'naive-ui'

const message = useMessage()
const dialog = useDialog()

// ---- Stats ----
interface SourceStat { source: string; total: number; indexed: number }
interface KBStats { total: number; indexed: number; coverage_pct: number; by_source: SourceStat[] }

const stats = ref<KBStats>({ total: 0, indexed: 0, coverage_pct: 0, by_source: [] })
const statsLoading = ref(false)

const sourceColumns: DataTableColumns<SourceStat> = [
  { title: '来源', key: 'source', width: 160 },
  { title: '总数', key: 'total', width: 80, align: 'right' },
  { title: '已索引', key: 'indexed', width: 80, align: 'right' },
  {
    title: '覆盖率', key: 'coverage', width: 100, align: 'right',
    render: (row) => {
      const pct = row.total > 0 ? (row.indexed / row.total * 100) : 0
      return h(NText, { type: pct >= 80 ? 'success' : pct >= 50 ? 'warning' : 'error' }, () => pct.toFixed(1) + '%')
    },
  },
]

async function fetchStats() {
  statsLoading.value = true
  try {
    const res = await fetch('/api/kb/stats')
    if (res.ok) stats.value = await res.json()
  } catch { /* ignore */ }
  statsLoading.value = false
}

// ---- Tasks ----
interface TaskInfo {
  task_id: string; type: string; status: string
  progress: number; total: number; created_at: string; error: string | null
}

const currentTask = ref<TaskInfo | null>(null)
const taskRunning = computed(() => currentTask.value?.status === 'pending' || currentTask.value?.status === 'running')
const taskPercentage = computed(() => {
  if (!currentTask.value || !currentTask.value.total) return 0
  return Math.round(currentTask.value.progress / currentTask.value.total * 100)
})
const taskStatusType = computed(() => {
  const s = currentTask.value?.status
  if (s === 'done') return 'success'
  if (s === 'failed') return 'error'
  if (s === 'running') return 'info'
  return 'default'
})
const taskStatusLabel = computed(() => {
  const m: Record<string, string> = { pending: '等待中', running: '运行中', done: '已完成', failed: '失败' }
  return m[currentTask.value?.status || ''] || currentTask.value?.status || ''
})

let pollTimer: ReturnType<typeof setInterval> | null = null

function startPolling(taskId: string) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`/api/kb/tasks/${taskId}`)
      if (res.ok) {
        const data: TaskInfo = await res.json()
        currentTask.value = data
        if (data.status === 'done' || data.status === 'failed') {
          stopPolling()
          if (data.status === 'done') {
            message.success('任务完成')
            fetchStats()
          } else {
            message.error('任务失败: ' + (data.error || '未知错误'))
          }
        }
      }
    } catch { /* ignore */ }
  }, 2000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function startTask(type: string) {
  try {
    const res = await fetch('/api/kb/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type }),
    })
    if (res.status === 202) {
      const data: TaskInfo = await res.json()
      currentTask.value = data
      message.info(`${type === 'incremental' ? '增量更新' : '全量重建'}任务已启动`)
      startPolling(data.task_id)
    } else if (res.status === 409) {
      message.warning('已有任务在运行中，请等待完成')
    } else {
      message.error('启动任务失败')
    }
  } catch {
    message.error('网络错误')
  }
}

function confirmFullRebuild() {
  dialog.warning({
    title: '确认全量重建',
    content: '全量重建将清除所有现有向量索引并重新生成，耗时较长。确认继续？',
    positiveText: '确认重建',
    negativeText: '取消',
    onPositiveClick: () => startTask('full_rebuild'),
  })
}

// ---- Search ----
interface SearchItem {
  id: number; title: string; source: string; url: string
  summary: string; score: number; keywords: string | null; collected_at: string
}

const searchQuery = ref('')
const searchLimit = ref(20)
const searchResults = ref<SearchItem[]>([])
const searchLoading = ref(false)
const searchDone = ref(false)

async function handleSearch() {
  const q = searchQuery.value.trim()
  if (!q) { message.warning('请输入搜索内容'); return }
  searchLoading.value = true
  searchDone.value = false
  try {
    const res = await fetch('/api/kb/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q, limit: searchLimit.value }),
    })
    if (res.ok) {
      const data = await res.json()
      searchResults.value = data.items || []
    } else {
      message.error('搜索失败')
      searchResults.value = []
    }
  } catch {
    message.error('网络错误')
    searchResults.value = []
  }
  searchLoading.value = false
  searchDone.value = true
}

function formatTime(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// ---- Lifecycle ----
onMounted(() => { fetchStats() })
onUnmounted(() => { stopPolling() })
</script>
