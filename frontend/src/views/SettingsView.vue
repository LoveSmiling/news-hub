<template>
  <n-space vertical :size="16">
    <n-h2 style="margin: 0">设置</n-h2>

    <!-- AI Provider Config -->
    <n-card title="AI 服务配置" size="small">
      <template #header-extra>
        <n-button size="small" type="primary" @click="openAddDialog()">添加配置</n-button>
      </template>

      <n-tabs type="line" v-model:value="activeTab">
        <n-tab-pane name="llm" tab="LLM 大模型">
          <n-spin :show="loading">
            <n-empty v-if="llmConfigs.length === 0 && !loading" description="暂未配置 LLM 服务" />
            <div v-else class="config-list">
              <n-card
                v-for="cfg in llmConfigs"
                :key="cfg.id"
                size="small"
                embedded
                class="config-item"
              >
                <div class="config-row">
                  <div class="config-info">
                    <n-space align="center" :size="8">
                      <n-text strong>{{ cfg.name }}</n-text>
                      <n-tag v-if="cfg.is_default" type="success" size="tiny" round>默认</n-tag>
                      <n-tag v-if="!cfg.enabled" type="warning" size="tiny" round>已禁用</n-tag>
                      <n-tag v-if="cfg.api_key_set" size="tiny" round>Key 已设置</n-tag>
                    </n-space>
                    <n-text depth="3" style="font-size: 12px; display: block; margin-top: 4px">
                      {{ cfg.api_base }} · {{ cfg.model }}
                    </n-text>
                  </div>
                  <n-space :size="4">
                    <n-button size="tiny" :type="testResults[cfg.id]?.success === true ? 'success' : testResults[cfg.id]?.success === false ? 'error' : 'default'" :loading="testingId === cfg.id" @click="handleTest(cfg.id)">
                      {{ testResults[cfg.id] ? (testResults[cfg.id].success ? '可用' : '不可用') : '测试' }}
                    </n-button>
                    <n-button size="tiny" @click="openEditDialog(cfg)">编辑</n-button>
                    <n-button size="tiny" v-if="!cfg.is_default" @click="handleSetDefault(cfg)">设为默认</n-button>
                    <n-popconfirm @positive-click="handleDelete(cfg.id)">
                      <template #trigger>
                        <n-button size="tiny" type="error">删除</n-button>
                      </template>
                      确认删除此配置？
                    </n-popconfirm>
                  </n-space>
                </div>
                <n-text v-if="testResults[cfg.id]" :depth="testResults[cfg.id]?.success ? 3 : 1" :type="testResults[cfg.id]?.success ? 'success' : 'error'" style="font-size: 12px; display: block; margin-top: 6px">
                  {{ testResults[cfg.id]?.message }}
                  <span v-if="testResults[cfg.id]?.latency_ms"> ({{ testResults[cfg.id]?.latency_ms }}ms)</span>
                </n-text>
              </n-card>
            </div>
          </n-spin>
        </n-tab-pane>

        <n-tab-pane name="embedding" tab="Embedding 向量">
          <n-spin :show="loading">
            <n-empty v-if="embeddingConfigs.length === 0 && !loading" description="暂未配置 Embedding 服务" />
            <div v-else class="config-list">
              <n-card
                v-for="cfg in embeddingConfigs"
                :key="cfg.id"
                size="small"
                embedded
                class="config-item"
              >
                <div class="config-row">
                  <div class="config-info">
                    <n-space align="center" :size="8">
                      <n-text strong>{{ cfg.name }}</n-text>
                      <n-tag v-if="cfg.is_default" type="success" size="tiny" round>默认</n-tag>
                      <n-tag v-if="!cfg.enabled" type="warning" size="tiny" round>已禁用</n-tag>
                    </n-space>
                    <n-text depth="3" style="font-size: 12px; display: block; margin-top: 4px">
                      {{ cfg.api_base }} · {{ cfg.model }}
                    </n-text>
                  </div>
                  <n-space :size="4">
                    <n-button size="tiny" :type="testResults[cfg.id]?.success === true ? 'success' : testResults[cfg.id]?.success === false ? 'error' : 'default'" :loading="testingId === cfg.id" @click="handleTest(cfg.id)">
                      {{ testResults[cfg.id] ? (testResults[cfg.id].success ? '可用' : '不可用') : '测试' }}
                    </n-button>
                    <n-button size="tiny" @click="openEditDialog(cfg)">编辑</n-button>
                    <n-button size="tiny" v-if="!cfg.is_default" @click="handleSetDefault(cfg)">设为默认</n-button>
                    <n-popconfirm @positive-click="handleDelete(cfg.id)">
                      <template #trigger>
                        <n-button size="tiny" type="error">删除</n-button>
                      </template>
                      确认删除此配置？
                    </n-popconfirm>
                  </n-space>
                </div>
                <n-text v-if="testResults[cfg.id]" :depth="testResults[cfg.id]?.success ? 3 : 1" :type="testResults[cfg.id]?.success ? 'success' : 'error'" style="font-size: 12px; display: block; margin-top: 6px">
                  {{ testResults[cfg.id]?.message }}
                  <span v-if="testResults[cfg.id]?.latency_ms"> ({{ testResults[cfg.id]?.latency_ms }}ms)</span>
                </n-text>
              </n-card>
            </div>
          </n-spin>
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <!-- Category Preferences -->
    <n-card title="分类偏好" size="small">
      <n-text depth="3" style="font-size: 13px; display: block; margin-bottom: 12px">
        选择你感兴趣的分类，用于个性化推荐
      </n-text>
      <n-space>
        <n-tag
          v-for="cat in allCategories"
          :key="cat"
          :type="isPreferred(cat) ? 'success' : 'default'"
          :bordered="!isPreferred(cat)"
          round
          checkable
          :checked="isPreferred(cat)"
          @update:checked="prefStore.toggleCategory(cat)"
          style="cursor: pointer"
        >
          {{ cat }}
        </n-tag>
      </n-space>
    </n-card>

    <!-- Reading History -->
    <n-card title="阅读历史" size="small">
      <template #header-extra>
        <n-button
          v-if="prefStore.readHistory.length > 0"
          size="tiny"
          type="error"
          @click="prefStore.clearHistory()"
        >
          清空历史
        </n-button>
      </template>
      <n-text depth="3" v-if="prefStore.readHistory.length === 0">
        暂无阅读记录
      </n-text>
      <n-text v-else depth="3" style="font-size: 13px">
        已记录 {{ prefStore.readHistory.length }} 条阅读，用于推荐
      </n-text>
    </n-card>

    <!-- Add/Edit Dialog -->
    <n-modal v-model:show="showDialog" preset="card" :title="editingId ? '编辑 AI 配置' : '添加 AI 配置'" style="width: 520px" :mask-closable="false">
      <n-form label-placement="left" label-width="90" :model="form">
        <n-form-item label="名称" required>
          <n-input v-model:value="form.name" placeholder="如: GPT-4o, 本地Ollama" />
        </n-form-item>
        <n-form-item label="类型" required>
          <n-select
            v-model:value="form.provider_type"
            :options="[{ label: 'LLM 大模型', value: 'llm' }, { label: 'Embedding 向量', value: 'embedding' }]"
            :disabled="!!editingId"
          />
        </n-form-item>
        <n-form-item label="API 地址" required>
          <n-input v-model:value="form.api_base" placeholder="http://192.168.1.100:11434" />
        </n-form-item>
        <n-form-item label="API Key">
          <n-input v-model:value="form.api_key" placeholder="留空则不使用 Key (如本地 Ollama)" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="模型名称" required>
          <n-input v-model:value="form.model" placeholder="qwen2.5:7b / gpt-4o / bge-m3" />
        </n-form-item>
        <n-form-item label="启用">
          <n-switch v-model:value="form.enabled" />
        </n-form-item>
        <n-form-item label="设为默认">
          <n-switch v-model:value="form.is_default" />
        </n-form-item>
      </n-form>

      <n-space justify="space-between" style="margin-top: 8px">
        <n-button @click="handleTestInline" :loading="inlineTesting" :type="inlineTestResult?.success === true ? 'success' : inlineTestResult?.success === false ? 'error' : 'default'">
          {{ inlineTestResult ? (inlineTestResult.success ? '连接成功' : '连接失败') : '测试连接' }}
        </n-button>
        <n-space>
          <n-button @click="showDialog = false">取消</n-button>
          <n-button type="primary" @click="handleSave" :loading="saving">保存</n-button>
        </n-space>
      </n-space>
      <n-text v-if="inlineTestResult" :type="inlineTestResult.success ? 'success' : 'error'" style="font-size: 12px; display: block; margin-top: 8px">
        {{ inlineTestResult.message }}
        <span v-if="inlineTestResult.latency_ms"> ({{ inlineTestResult.latency_ms }}ms)</span>
      </n-text>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NH2, NCard, NSpace, NTag, NButton, NText, NTabs, NTabPane, NSpin,
  NEmpty, NModal, NForm, NFormItem, NInput, NSelect, NSwitch, NPopconfirm,
  useMessage,
} from 'naive-ui'
import { usePreferenceStore } from '../stores/preference'
import {
  fetchAIConfigs, createAIConfig, updateAIConfig, deleteAIConfig,
  testAIConfig, testAIConfigInline,
  type AIConfigItem, type AIConfigPayload, type TestResult,
} from '../api'

const prefStore = usePreferenceStore()
const message = useMessage()

const allCategories = ['综合', '科技', '娱乐', '新闻']
function isPreferred(cat: string) {
  return prefStore.preferredCategories.includes(cat)
}

// ---- AI Config state ----
const loading = ref(false)
const configs = ref<AIConfigItem[]>([])
const activeTab = ref<string>('llm')
const testResults = ref<Record<number, TestResult>>({})
const testingId = ref<number | null>(null)

const llmConfigs = computed(() => configs.value.filter(c => c.provider_type === 'llm'))
const embeddingConfigs = computed(() => configs.value.filter(c => c.provider_type === 'embedding'))

async function loadConfigs() {
  loading.value = true
  try {
    configs.value = await fetchAIConfigs()
  } finally {
    loading.value = false
  }
}

async function handleTest(id: number) {
  testingId.value = id
  try {
    testResults.value[id] = await testAIConfig(id)
  } finally {
    testingId.value = null
  }
}

async function handleSetDefault(cfg: AIConfigItem) {
  await updateAIConfig(cfg.id, { is_default: true })
  message.success(`已将 "${cfg.name}" 设为默认`)
  await loadConfigs()
}

async function handleDelete(id: number) {
  await deleteAIConfig(id)
  message.success('已删除')
  await loadConfigs()
}

// ---- Dialog ----
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const inlineTesting = ref(false)
const inlineTestResult = ref<TestResult | null>(null)

const form = ref<AIConfigPayload>({
  name: '',
  provider_type: 'llm',
  api_base: '',
  api_key: '',
  model: '',
  enabled: true,
  is_default: false,
})

function openAddDialog() {
  editingId.value = null
  form.value = { name: '', provider_type: activeTab.value as 'llm' | 'embedding', api_base: '', api_key: '', model: '', enabled: true, is_default: false }
  inlineTestResult.value = null
  showDialog.value = true
}

function openEditDialog(cfg: AIConfigItem) {
  editingId.value = cfg.id
  form.value = {
    name: cfg.name,
    provider_type: cfg.provider_type,
    api_base: cfg.api_base,
    api_key: '',  // don't prefill for security
    model: cfg.model,
    enabled: cfg.enabled,
    is_default: cfg.is_default,
  }
  inlineTestResult.value = null
  showDialog.value = true
}

async function handleTestInline() {
  if (!form.value.api_base || !form.value.model) {
    message.warning('请先填写 API 地址和模型名称')
    return
  }
  inlineTesting.value = true
  inlineTestResult.value = null
  try {
    inlineTestResult.value = await testAIConfigInline(form.value)
  } finally {
    inlineTesting.value = false
  }
}

async function handleSave() {
  if (!form.value.name || !form.value.api_base || !form.value.model) {
    message.warning('请填写必要字段')
    return
  }
  saving.value = true
  try {
    const payload: any = { ...form.value }
    // If api_key is empty string, don't send it (keep existing)
    if (editingId.value && !payload.api_key) {
      delete payload.api_key
    }
    if (editingId.value) {
      await updateAIConfig(editingId.value, payload)
      message.success('已更新')
    } else {
      await createAIConfig(payload)
      message.success('已创建')
    }
    showDialog.value = false
    await loadConfigs()
  } finally {
    saving.value = false
  }
}

onMounted(loadConfigs)
</script>

<style scoped>
.config-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-item {
  margin: 0;
}

.config-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.config-info {
  flex: 1;
  min-width: 0;
}
</style>
