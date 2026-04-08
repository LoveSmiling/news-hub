<template>
  <n-space vertical :size="16">
    <div style="display: flex; justify-content: space-between; align-items: center">
      <n-h2 style="margin: 0">源管理</n-h2>
      <n-space :size="8">
        <n-button size="small" @click="handleExport">⬇ 导出</n-button>
        <n-button size="small" @click="importDialogVisible = true">⬆ 导入</n-button>
        <n-button type="primary" size="small" @click="openAddDialog">+ 新增源</n-button>
      </n-space>
    </div>

    <!-- Filters -->
    <n-space :size="12">
      <n-select
        v-model:value="filterCategory"
        placeholder="分类"
        clearable
        size="small"
        style="width: 140px"
        :options="categoryOptions"
      />
      <n-select
        v-model:value="filterType"
        placeholder="类型"
        clearable
        size="small"
        style="width: 120px"
        :options="[{ label: 'RSSHub', value: 'rsshub' }, { label: 'RSS', value: 'rss' }]"
      />
      <n-select
        v-model:value="filterStatus"
        placeholder="状态"
        clearable
        size="small"
        style="width: 120px"
        :options="[{ label: 'Active', value: 'active' }, { label: 'Pending', value: 'pending' }, { label: 'Disabled', value: 'disabled' }, { label: 'Error', value: 'error' }]"
      />
    </n-space>

    <!-- Batch action bar -->
    <n-card v-if="checkedKeys.length > 0" size="small" embedded>
      <n-space align="center" :size="12">
        <n-text>已选 {{ checkedKeys.length }} 项</n-text>
        <n-button size="tiny" type="success" @click="handleBatch('enable')">批量启用</n-button>
        <n-button size="tiny" type="warning" @click="handleBatch('disable')">批量禁用</n-button>
        <n-button size="tiny" @click="showBatchCategory = true">修改分类</n-button>
        <n-button size="tiny" type="info" :loading="batchCollecting" @click="handleBatch('collect')">批量采集</n-button>
      </n-space>
    </n-card>

    <!-- Table -->
    <n-spin :show="loading">
      <n-data-table
        :columns="columns"
        :data="filteredSources"
        :row-key="(row: any) => row.id"
        v-model:checked-row-keys="checkedKeys"
        size="small"
        :pagination="{ pageSize: 50 }"
      />
    </n-spin>

    <!-- Add/Edit Dialog -->
    <n-modal v-model:show="dialogVisible" :mask-closable="false" style="width: 600px">
      <n-card :title="editingSource ? '编辑源' : '新增源'" closable @close="dialogVisible = false">
        <n-form
          ref="formRef"
          :model="formData"
          label-placement="left"
          label-width="90"
          :rules="formRules"
        >
          <n-form-item label="标识(name)" path="name">
            <n-input v-model:value="formData.name" :disabled="!!editingSource" placeholder="唯一标识，如 v2ex" />
          </n-form-item>
          <n-form-item label="显示名称" path="display_name">
            <n-input v-model:value="formData.display_name" placeholder="显示名称，如 V2EX 热门" />
          </n-form-item>
          <n-form-item label="类型" path="type">
            <n-radio-group v-model:value="formData.type">
              <n-radio value="rsshub">RSSHub</n-radio>
              <n-radio value="rss">外部 RSS</n-radio>
            </n-radio-group>
          </n-form-item>
          <n-form-item v-if="formData.type === 'rsshub'" label="Route" path="route">
            <n-input v-model:value="formData.route" placeholder="/v2ex/topics/hot" />
          </n-form-item>
          <n-form-item v-if="formData.type === 'rss'" label="URL" path="url">
            <n-input v-model:value="formData.url" placeholder="https://example.com/feed" />
          </n-form-item>
          <n-form-item label="分类" path="category">
            <n-select
              v-model:value="formData.category"
              filterable
              tag
              placeholder="选择或输入新分类"
              :options="categoryOptions"
            />
          </n-form-item>
          <n-form-item label="采集频率" path="schedule">
            <n-input v-model:value="formData.schedule" placeholder="*/10 * * * *" />
          </n-form-item>
          <n-form-item label="最大条数" path="max_items">
            <n-input-number v-model:value="formData.max_items" :min="1" :max="200" />
          </n-form-item>
        </n-form>

        <!-- Preview results -->
        <n-card v-if="previewResult" size="small" embedded style="margin-top: 12px; max-height: 300px; overflow: auto">
          <template #header>
            <n-text v-if="previewResult.success" type="success">
              ✅ 成功获取 {{ previewResult.count }} 条 ({{ previewResult.elapsed_ms }}ms)
            </n-text>
            <n-text v-else type="error">❌ {{ previewResult.error }}</n-text>
          </template>
          <div v-if="previewResult.success">
            <div v-for="(item, i) in previewResult.items" :key="i" style="margin-bottom: 6px; font-size: 13px">
              {{ i + 1 }}. <a :href="item.url" target="_blank" style="color: var(--n-text-color)">{{ item.title }}</a>
            </div>
          </div>
        </n-card>

        <template #action>
          <n-space justify="end">
            <n-button size="small" :loading="previewing" @click="handlePreview">预览测试</n-button>
            <n-button size="small" @click="dialogVisible = false">取消</n-button>
            <n-button size="small" type="primary" :loading="saving" @click="handleSave">保存</n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>

    <!-- Batch Category Dialog -->
    <n-modal v-model:show="showBatchCategory" style="width: 400px">
      <n-card title="批量修改分类" closable @close="showBatchCategory = false">
        <n-select
          v-model:value="batchCategoryValue"
          filterable
          tag
          placeholder="选择或输入分类"
          :options="categoryOptions"
        />
        <template #action>
          <n-space justify="end">
            <n-button size="small" @click="showBatchCategory = false">取消</n-button>
            <n-button size="small" type="primary" @click="handleBatchCategory">确认</n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>

    <!-- Import Dialog -->
    <n-modal v-model:show="importDialogVisible" :mask-closable="false" style="width: 500px">
      <n-card title="导入源" closable @close="closeImportDialog">
        <n-space vertical :size="12">
          <n-upload
            accept=".json"
            :max="1"
            :default-upload="false"
            @change="handleImportFileChange"
          >
            <n-button>选择 JSON 文件</n-button>
          </n-upload>

          <n-alert v-if="importPreview !== null && importError === ''" type="info">
            即将导入 {{ importPreview }} 个源
          </n-alert>
          <n-alert v-if="importError" type="error">
            {{ importError }}
          </n-alert>

          <div v-if="importResult">
            <n-alert type="success">
              导入完成：新增 {{ importResult.created }} 个，更新 {{ importResult.updated }} 个
              <template v-if="importResult.errors.length > 0">
                ，失败 {{ importResult.errors.length }} 个
              </template>
            </n-alert>
            <div v-if="importResult.errors.length > 0" style="margin-top: 8px">
              <n-text type="error" v-for="err in importResult.errors" :key="err.name" style="display: block; font-size: 13px">
                {{ err.name }}: {{ err.error }}
              </n-text>
            </div>
          </div>
        </n-space>

        <template #action>
          <n-space justify="end">
            <n-button size="small" @click="closeImportDialog">{{ importResult ? '关闭' : '取消' }}</n-button>
            <n-button
              v-if="!importResult"
              size="small"
              type="primary"
              :disabled="!importPayload || !!importError"
              :loading="importing"
              @click="handleImport"
            >
              确认导入
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NSpace, NH2, NButton, NCard, NDataTable, NSelect, NModal, NForm, NFormItem,
  NInput, NInputNumber, NRadioGroup, NRadio, NTag, NSpin, NText, NPopconfirm,
  NUpload, NAlert,
  useMessage, type DataTableColumns, type FormInst, type FormRules, type UploadFileInfo,
} from 'naive-ui'
import {
  fetchSources, createSource, updateSource, deleteSource,
  testSource, collectSourceNow, fetchCategories, batchSourceAction,
  exportSources, importSources,
  type SourceInfo, type SourceTestResult,
  type SourceImportPayload, type SourceImportResult,
} from '../api'

const message = useMessage()

// --- Data ---
const loading = ref(false)
const sources = ref<SourceInfo[]>([])
const categories = ref<string[]>([])
const checkedKeys = ref<number[]>([])

// Filters
const filterCategory = ref<string | null>(null)
const filterType = ref<string | null>(null)
const filterStatus = ref<string | null>(null)

const categoryOptions = computed(() => {
  const defaults = ['新闻', '科技', '娱乐', '综合']
  const all = new Set([...defaults, ...categories.value])
  return Array.from(all).sort().map(c => ({ label: c, value: c }))
})

const filteredSources = computed(() => {
  return sources.value.filter(s => {
    if (filterCategory.value && s.category !== filterCategory.value) return false
    if (filterType.value && s.type !== filterType.value) return false
    if (filterStatus.value && s.status !== filterStatus.value) return false
    return true
  })
})

// --- Dialog ---
const dialogVisible = ref(false)
const editingSource = ref<SourceInfo | null>(null)
const saving = ref(false)
const previewing = ref(false)
const previewResult = ref<SourceTestResult | null>(null)
const formRef = ref<FormInst | null>(null)

const formData = ref({
  name: '',
  display_name: '',
  type: 'rsshub',
  route: '',
  url: '',
  category: '',
  schedule: '*/10 * * * *',
  max_items: 30,
})

const formRules: FormRules = {
  name: { required: true, message: '请输入标识', trigger: 'blur' },
  display_name: { required: true, message: '请输入显示名称', trigger: 'blur' },
  category: { required: true, message: '请选择分类', trigger: 'blur' },
  schedule: { required: true, message: '请输入 cron 表达式', trigger: 'blur' },
}

// Batch category
const showBatchCategory = ref(false)
const batchCategoryValue = ref('')
const batchCollecting = ref(false)

// Collecting state
const collectingIds = ref<Set<number>>(new Set())

// --- Schedule display ---
function cronToText(cron: string): string {
  const parts = cron.split(' ')
  if (parts.length !== 5) return cron
  const [min, hour] = parts
  if (min.startsWith('*/') && hour === '*') return `每${min.slice(2)}分钟`
  if (min === '0' && hour === '*') return '每小时'
  if (min === '0' && hour.startsWith('*/')) return `每${hour.slice(2)}小时`
  return cron
}

// --- Status Tag ---
const statusMap: Record<string, { type: 'success' | 'warning' | 'default' | 'error'; label: string }> = {
  active: { type: 'success', label: 'Active' },
  pending: { type: 'warning', label: 'Pending' },
  disabled: { type: 'default', label: 'Disabled' },
  error: { type: 'error', label: 'Error' },
}

// --- Table Columns ---
const columns: DataTableColumns<SourceInfo> = [
  { type: 'selection' },
  { title: '名称', key: 'display_name', width: 160, ellipsis: { tooltip: true } },
  { title: '类型', key: 'type', width: 80, render: (row) => h(NTag, { size: 'small', bordered: false }, () => row.type === 'rss' ? 'RSS' : 'RSSHub') },
  { title: '分类', key: 'category', width: 80 },
  { title: '采集频率', key: 'schedule', width: 100, render: (row) => cronToText(row.schedule) },
  {
    title: '状态', key: 'status', width: 90,
    render: (row) => {
      const s = statusMap[row.status] || { type: 'default' as const, label: row.status }
      return h(NTag, { size: 'small', type: s.type, round: true }, () => s.label)
    }
  },
  {
    title: '最近采集', key: 'last_collected_at', width: 160,
    render: (row) => row.last_collected_at ? new Date(row.last_collected_at).toLocaleString('zh-CN') : '-'
  },
  {
    title: '操作', key: 'actions', width: 180,
    render: (row) => h(NSpace, { size: 4 }, () => [
      h(NButton, { size: 'tiny', onClick: () => openEditDialog(row) }, () => '编辑'),
      h(NButton, {
        size: 'tiny', type: 'info',
        loading: collectingIds.value.has(row.id),
        onClick: () => handleCollectNow(row),
      }, () => '采集'),
      h(NPopconfirm, { onPositiveClick: () => handleDelete(row) }, {
        trigger: () => h(NButton, { size: 'tiny', type: 'error' }, () => '删除'),
        default: () => row.status === 'pending' ? '确认删除？此操作不可恢复。' : '确认禁用此源？历史数据将保留。',
      }),
    ]),
  },
]

// --- Actions ---
async function loadData() {
  loading.value = true
  try {
    const [s, c] = await Promise.all([fetchSources(), fetchCategories()])
    sources.value = s
    categories.value = c
  } finally {
    loading.value = false
  }
}

function openAddDialog() {
  editingSource.value = null
  formData.value = { name: '', display_name: '', type: 'rsshub', route: '', url: '', category: '', schedule: '*/10 * * * *', max_items: 30 }
  previewResult.value = null
  dialogVisible.value = true
}

function openEditDialog(source: SourceInfo) {
  editingSource.value = source
  formData.value = {
    name: source.name,
    display_name: source.display_name,
    type: source.type,
    route: source.route,
    url: source.url,
    category: source.category || '',
    schedule: source.schedule,
    max_items: source.max_items,
  }
  previewResult.value = null
  dialogVisible.value = true
}

async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch { return }

  saving.value = true
  try {
    if (editingSource.value) {
      await updateSource(editingSource.value.id, {
        display_name: formData.value.display_name,
        category: formData.value.category,
        type: formData.value.type,
        route: formData.value.route,
        url: formData.value.url,
        schedule: formData.value.schedule,
        max_items: formData.value.max_items,
      })
      message.success('源已更新')
    } else {
      await createSource(formData.value)
      message.success('源已创建')
    }
    dialogVisible.value = false
    await loadData()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handlePreview() {
  previewing.value = true
  previewResult.value = null
  try {
    previewResult.value = await testSource({
      type: formData.value.type,
      route: formData.value.route,
      url: formData.value.url,
      max_items: Math.min(formData.value.max_items, 10),
    })
  } catch (e: any) {
    previewResult.value = { success: false, items: [], count: 0, elapsed_ms: 0, error: e.message }
  } finally {
    previewing.value = false
  }
}

async function handleDelete(source: SourceInfo) {
  try {
    const result = await deleteSource(source.id)
    message.success(result.detail)
    await loadData()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '删除失败')
  }
}

async function handleCollectNow(source: SourceInfo) {
  collectingIds.value.add(source.id)
  try {
    const result = await collectSourceNow(source.id)
    message.success(result.detail)
    await loadData()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '采集失败')
  } finally {
    collectingIds.value.delete(source.id)
  }
}

async function handleBatch(action: 'enable' | 'disable' | 'collect') {
  if (action === 'collect') batchCollecting.value = true
  try {
    const result = await batchSourceAction({ ids: checkedKeys.value, action })
    message.success(result.detail)
    checkedKeys.value = []
    await loadData()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '批量操作失败')
  } finally {
    batchCollecting.value = false
  }
}

async function handleBatchCategory() {
  if (!batchCategoryValue.value) {
    message.warning('请选择分类')
    return
  }
  try {
    const result = await batchSourceAction({
      ids: checkedKeys.value,
      action: 'set_category',
      category: batchCategoryValue.value,
    })
    message.success(result.detail)
    showBatchCategory.value = false
    checkedKeys.value = []
    await loadData()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  }
}

// --- Import / Export ---
const importDialogVisible = ref(false)
const importing = ref(false)
const importPreview = ref<number | null>(null)
const importError = ref('')
const importPayload = ref<SourceImportPayload | null>(null)
const importResult = ref<SourceImportResult | null>(null)

async function handleExport() {
  try {
    await exportSources()
    message.success('导出成功')
  } catch (e: any) {
    message.error(e.message || '导出失败')
  }
}

function handleImportFileChange(options: { fileList: UploadFileInfo[] }) {
  importError.value = ''
  importPreview.value = null
  importPayload.value = null
  importResult.value = null

  const fileInfo = options.fileList[0]
  if (!fileInfo?.file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const json = JSON.parse(e.target?.result as string)
      if (!json.version || !Array.isArray(json.sources)) {
        importError.value = '文件格式错误：缺少 version 或 sources 字段'
        return
      }
      importPreview.value = json.sources.length
      importPayload.value = json
    } catch {
      importError.value = '文件解析失败：不是有效的 JSON 文件'
    }
  }
  reader.readAsText(fileInfo.file)
}

async function handleImport() {
  if (!importPayload.value) return
  importing.value = true
  try {
    importResult.value = await importSources(importPayload.value)
    await loadData()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

function closeImportDialog() {
  importDialogVisible.value = false
  importPreview.value = null
  importError.value = ''
  importPayload.value = null
  importResult.value = null
}

onMounted(loadData)
</script>
