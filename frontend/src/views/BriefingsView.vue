<template>
  <n-space vertical :size="16">
    <n-h2 style="margin: 0">AI 简报</n-h2>

    <!-- Generate Panel -->
    <n-card title="生成简报" size="small">
      <n-space :size="12" align="center">
        <n-select
          v-model:value="genType"
          :options="typeOptions"
          style="width: 130px"
          size="small"
        />
        <n-select
          v-if="genType === 'source'"
          v-model:value="genSource"
          :options="sourceOptions"
          placeholder="选择来源"
          style="width: 160px"
          size="small"
        />
        <n-input
          v-if="genType === 'topic'"
          v-model:value="genKeyword"
          placeholder="关键词"
          style="width: 160px"
          size="small"
        />
        <n-input-number
          v-if="genType === 'topic'"
          v-model:value="genHours"
          :min="1"
          :max="720"
          style="width: 120px"
          size="small"
        >
          <template #suffix>小时</template>
        </n-input-number>
        <n-button type="primary" size="small" :loading="generating" @click="handleGenerate">
          生成
        </n-button>
      </n-space>
    </n-card>

    <!-- Filters -->
    <n-space :size="8">
      <n-select
        v-model:value="filterType"
        :options="[{ label: '全部类型', value: '' }, ...typeOptions]"
        style="width: 130px"
        size="small"
        @update:value="loadList"
      />
      <n-select
        v-model:value="filterStatus"
        :options="statusFilterOptions"
        style="width: 130px"
        size="small"
        @update:value="loadList"
      />
    </n-space>

    <!-- Briefing List -->
    <n-spin :show="loading">
      <div v-if="briefings.length === 0 && !loading" style="text-align: center; padding: 40px">
        <n-text depth="3">暂无简报</n-text>
      </div>
      <n-list bordered v-else>
        <n-list-item v-for="b in briefings" :key="b.id" style="cursor: pointer" @click="openDetail(b.id)">
          <template #prefix>
            <n-space :size="4" align="center">
              <n-tag :type="typeTagType(b.brief_type)" size="small">{{ typeLabel(b.brief_type) }}</n-tag>
              <n-tag v-if="b.share_token && !isShareExpired(b)" size="small" type="info" :bordered="false">🔗</n-tag>
            </n-space>
          </template>
          <n-thing :title="b.title">
            <template #description>
              <n-space :size="8" align="center">
                <n-tag :type="statusTagType(b.status)" size="small" :bordered="false">
                  <template v-if="b.status === 'generating'" #icon>
                    <n-icon><sync-icon /></n-icon>
                  </template>
                  {{ statusLabel(b.status) }}
                </n-tag>
                <n-text depth="3" style="font-size: 12px">
                  {{ formatTime(b.created_at) }}
                </n-text>
              </n-space>
            </template>
          </n-thing>
          <template #suffix>
            <n-button text type="error" size="small" @click.stop="handleDelete(b.id)">删除</n-button>
          </template>
        </n-list-item>
      </n-list>
    </n-spin>

    <!-- Detail Modal -->
    <n-modal v-model:show="showDetail">
      <n-card :title="detailData?.title || '简报详情'" closable @close="showDetail = false" style="max-width: 800px; max-height: 85vh; overflow: auto; width: 90vw">
        <n-spin :show="detailLoading">
          <div v-if="detailData">
            <n-space :size="8" style="margin-bottom: 12px">
              <n-tag :type="typeTagType(detailData.brief_type)" size="small">{{ typeLabel(detailData.brief_type) }}</n-tag>
              <n-tag :type="statusTagType(detailData.status)" size="small">{{ statusLabel(detailData.status) }}</n-tag>
              <n-text depth="3" style="font-size: 12px">{{ formatTime(detailData.created_at) }}</n-text>
            </n-space>

            <!-- Generating spinner -->
            <div v-if="detailData.status === 'generating'" style="text-align: center; padding: 40px">
              <n-spin size="large" />
              <n-text depth="3" style="display: block; margin-top: 12px">简报生成中，请稍候...</n-text>
            </div>

            <!-- Markdown content -->
            <div v-else-if="detailData.content" class="markdown-body" v-html="renderMarkdown(detailData.content)" />

            <!-- Referenced items -->
            <div v-if="detailData.items && detailData.items.length > 0" style="margin-top: 20px">
              <n-divider />
              <n-h4 style="margin: 0 0 8px 0">引用来源 ({{ detailData.items.length }})</n-h4>
              <n-list bordered size="small">
                <n-list-item v-for="item in detailData.items" :key="item.id">
                  <n-space :size="8" align="center">
                    <n-tag size="tiny" :bordered="false">{{ item.source_display_name || item.source }}</n-tag>
                    <n-a :href="item.url" target="_blank">{{ item.title }}</n-a>
                  </n-space>
                </n-list-item>
              </n-list>
            </div>

            <!-- Share & Export buttons -->
            <div v-if="detailData.status === 'done'" style="margin-top: 16px">
              <n-divider />
              <n-space :size="12">
                <n-button size="small" @click="openShareDialog">📤 分享</n-button>
                <n-button size="small" @click="handleExportMarkdown">📥 导出 Markdown</n-button>
              </n-space>
            </div>
          </div>
        </n-spin>
      </n-card>
    </n-modal>

    <!-- Share Dialog -->
    <n-modal v-model:show="showShareDialog" style="width: 460px">
      <n-card title="分享简报" closable @close="showShareDialog = false">
        <n-space vertical :size="16">
          <!-- Expiration selector -->
          <div>
            <n-text depth="2" style="font-size: 13px; margin-bottom: 8px; display: block">有效期</n-text>
            <n-radio-group v-model:value="shareExpiresIn" size="small">
              <n-radio-button value="1d">1天</n-radio-button>
              <n-radio-button value="7d">7天</n-radio-button>
              <n-radio-button value="30d">30天</n-radio-button>
              <n-radio-button :value="null">永久</n-radio-button>
            </n-radio-group>
          </div>

          <!-- Share link display -->
          <div v-if="currentShareUrl">
            <n-text depth="2" style="font-size: 13px; margin-bottom: 8px; display: block">分享链接</n-text>
            <n-input-group>
              <n-input :value="currentShareUrl" readonly size="small" />
              <n-button size="small" type="primary" @click="copyShareLink">复制</n-button>
            </n-input-group>
            <n-text v-if="currentShareExpires" depth="3" style="font-size: 12px; margin-top: 4px; display: block">
              过期时间：{{ formatTime(currentShareExpires) }}
            </n-text>
            <n-text v-else depth="3" style="font-size: 12px; margin-top: 4px; display: block">
              永久有效
            </n-text>
          </div>
        </n-space>

        <template #action>
          <n-space justify="end" :size="8">
            <n-button v-if="currentShareUrl" size="small" type="warning" :loading="shareLoading" @click="handleCancelShare">取消分享</n-button>
            <n-button size="small" type="primary" :loading="shareLoading" @click="handleCreateOrUpdateShare">
              {{ currentShareUrl ? '更新有效期' : '生成链接' }}
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import {
  NH2, NH4,
  NSpace, NCard, NButton, NSelect, NInput, NInputNumber, NInputGroup,
  NList, NListItem, NThing, NTag, NText, NSpin, NModal,
  NDivider, NIcon, NA, NRadioGroup, NRadioButton,
  useMessage,
} from 'naive-ui'
import { SyncOutline as SyncIcon } from '@vicons/ionicons5'
import axios from 'axios'
import MarkdownIt from 'markdown-it'
import { fetchSources, createShare, deleteShare } from '../api'

const message = useMessage()
const md = new MarkdownIt()

// ── Sources (dynamic from API) ──
const sourceOptions = ref<{ label: string; value: string }[]>([])
async function loadSourceOptions() {
  try {
    const list = await fetchSources()
    sourceOptions.value = list
      .filter((s: any) => s.status !== 'disabled')
      .map((s: any) => ({ label: s.display_name, value: s.name }))
  } catch {
    sourceOptions.value = []
  }
}

const typeOptions = [
  { label: '单来源', value: 'source' },
  { label: '每日汇总', value: 'daily' },
  { label: '主题', value: 'topic' },
]

const statusFilterOptions = [
  { label: '全部状态', value: '' },
  { label: '已完成', value: 'done' },
  { label: '生成中', value: 'generating' },
  { label: '等待中', value: 'pending' },
  { label: '失败', value: 'failed' },
]

// ── State ──
const briefings = ref<any[]>([])
const loading = ref(false)
const filterType = ref('')
const filterStatus = ref('')

const genType = ref('source')
const genSource = ref('')
const genKeyword = ref('')
const genHours = ref(72)
const generating = ref(false)

const showDetail = ref(false)
const detailData = ref<any>(null)
const detailLoading = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

// ── Helpers ──
function typeLabel(t: string) {
  const m: Record<string, string> = { source: '来源', daily: '每日', topic: '主题', custom: '自选' }
  return m[t] || t
}
function typeTagType(t: string) {
  const m: Record<string, string> = { source: 'info', daily: 'success', topic: 'warning', custom: 'default' }
  return m[t] || 'default'
}
function statusLabel(s: string) {
  const m: Record<string, string> = { done: '已完成', generating: '生成中', pending: '等待中', failed: '失败' }
  return m[s] || s
}
function statusTagType(s: string) {
  const m: Record<string, string> = { done: 'success', generating: 'info', pending: 'default', failed: 'error' }
  return m[s] || 'default'
}
function formatTime(t: string) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}
function renderMarkdown(text: string) {
  // Strip <think>...</think> blocks from reasoning models
  const cleaned = (text || '').replace(/<think>[\s\S]*?<\/think>/g, '').trimStart()
  return md.render(cleaned)
}

// ── API calls ──
async function loadList() {
  loading.value = true
  try {
    const params: any = { limit: 50, offset: 0 }
    if (filterType.value) params.type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    const { data } = await axios.get('/api/briefings', { params })
    briefings.value = data.items
  } catch (e: any) {
    message.error('加载简报列表失败')
  } finally {
    loading.value = false
  }
}

async function openDetail(id: number) {
  showDetail.value = true
  detailLoading.value = true
  detailData.value = null
  stopPoll()
  try {
    const { data } = await axios.get(`/api/briefings/${id}`)
    detailData.value = data
    if (data.status === 'generating') {
      startPoll(id)
    }
  } catch {
    message.error('加载简报详情失败')
  } finally {
    detailLoading.value = false
  }
}

function startPoll(id: number) {
  pollTimer = setInterval(async () => {
    try {
      const { data } = await axios.get(`/api/briefings/${id}`)
      detailData.value = data
      if (data.status !== 'generating') {
        stopPoll()
        loadList()  // refresh list too
      }
    } catch { /* ignore poll errors */ }
  }, 3000)
}

function stopPoll() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function handleGenerate() {
  const body: any = { type: genType.value }
  if (genType.value === 'source') {
    if (!genSource.value) { message.warning('请选择来源'); return }
    body.source = genSource.value
  } else if (genType.value === 'topic') {
    if (!genKeyword.value) { message.warning('请输入关键词'); return }
    body.keyword = genKeyword.value
    body.hours = genHours.value
  }

  generating.value = true
  try {
    await axios.post('/api/briefings/generate', body)
    message.success('简报生成已触发')
    await loadList()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '触发生成失败')
  } finally {
    generating.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await axios.delete(`/api/briefings/${id}`)
    message.success('已删除')
    briefings.value = briefings.value.filter(b => b.id !== id)
  } catch {
    message.error('删除失败')
  }
}

// ── Share ──
const showShareDialog = ref(false)
const shareExpiresIn = ref<string | null>('7d')
const shareLoading = ref(false)
const currentShareUrl = ref('')
const currentShareExpires = ref<string | null>(null)

function isShareExpired(b: any): boolean {
  if (!b.share_token) return true
  if (!b.share_expires) return false
  return new Date(b.share_expires) <= new Date()
}

function openShareDialog() {
  if (!detailData.value) return
  if (detailData.value.share_token && !isShareExpired(detailData.value)) {
    currentShareUrl.value = `${window.location.origin}/share/${detailData.value.share_token}`
    currentShareExpires.value = detailData.value.share_expires
  } else {
    currentShareUrl.value = ''
    currentShareExpires.value = null
  }
  shareExpiresIn.value = '7d'
  showShareDialog.value = true
}

async function handleCreateOrUpdateShare() {
  if (!detailData.value) return
  shareLoading.value = true
  try {
    const res = await createShare(detailData.value.id, shareExpiresIn.value)
    currentShareUrl.value = `${window.location.origin}${res.share_url}`
    currentShareExpires.value = res.expires_at
    detailData.value.share_token = res.share_token
    detailData.value.share_expires = res.expires_at
    message.success(detailData.value.share_token ? '有效期已更新' : '分享链接已生成')
    loadList()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally {
    shareLoading.value = false
  }
}

async function handleCancelShare() {
  if (!detailData.value) return
  shareLoading.value = true
  try {
    await deleteShare(detailData.value.id)
    currentShareUrl.value = ''
    currentShareExpires.value = null
    detailData.value.share_token = null
    detailData.value.share_expires = null
    showShareDialog.value = false
    message.success('分享已取消')
    loadList()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally {
    shareLoading.value = false
  }
}

function copyShareLink() {
  navigator.clipboard.writeText(currentShareUrl.value)
  message.success('链接已复制')
}

// ── Export Markdown ──
function handleExportMarkdown() {
  if (!detailData.value) return
  const d = detailData.value
  const typeMap: Record<string, string> = { source: '单来源', daily: '每日汇总', topic: '主题', custom: '自选' }

  let mdContent = `# ${d.title}\n\n`
  mdContent += `> 生成时间：${formatTime(d.created_at)} · 类型：${typeMap[d.brief_type] || d.brief_type}\n\n`
  mdContent += (d.content || '') + '\n'

  if (d.items && d.items.length > 0) {
    mdContent += '\n---\n\n## 引用来源\n\n'
    d.items.forEach((item: any, i: number) => {
      mdContent += `${i + 1}. [${item.title}](${item.url}) — ${item.source}\n`
    })
  }

  // Sanitize filename
  const safeName = d.title.replace(/[/\\:*?"<>|]/g, '_')
  const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${safeName}.md`
  a.click()
  URL.revokeObjectURL(url)
  message.success('已导出')
}

onMounted(() => {
  loadList()
  loadSourceOptions()
})

onUnmounted(() => {
  stopPoll()
})
</script>

<style scoped>
.markdown-body {
  line-height: 1.7;
  font-size: 14px;
}
.markdown-body :deep(h2) {
  margin: 16px 0 8px;
  font-size: 18px;
  border-bottom: 1px solid var(--n-border-color);
  padding-bottom: 4px;
}
.markdown-body :deep(h3) {
  margin: 12px 0 6px;
  font-size: 16px;
}
.markdown-body :deep(ul) {
  padding-left: 20px;
}
.markdown-body :deep(li) {
  margin: 4px 0;
}
.markdown-body :deep(p) {
  margin: 8px 0;
}
</style>
