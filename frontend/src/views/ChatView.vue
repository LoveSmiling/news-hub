<template>
  <div class="chat-container">
    <!-- Sidebar -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <n-button type="primary" block @click="createSession">
          <template #icon><n-icon><add-icon /></n-icon></template>
          新建对话
        </n-button>
      </div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: s.id === currentSessionId }"
          @click="selectSession(s.id)"
        >
          <div class="session-info">
            <div class="session-title">{{ s.title }}</div>
            <div class="session-meta">{{ s.message_count }} 条消息</div>
          </div>
          <n-button
            text
            type="error"
            size="tiny"
            class="session-delete"
            @click.stop="confirmDelete(s.id)"
          >
            <template #icon><n-icon><trash-icon /></n-icon></template>
          </n-button>
        </div>
        <n-empty v-if="sessions.length === 0" description="暂无对话" style="margin-top: 40px" />
      </div>
    </div>

    <!-- Main Area -->
    <div class="chat-main">
      <template v-if="currentSessionId">
        <!-- Messages -->
        <div ref="messagesRef" class="messages-area">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="message-row"
            :class="msg.role"
          >
            <div class="message-bubble" :class="msg.role">
              <div v-if="msg.role === 'assistant'" class="md-content" v-html="renderMd(msg.content)"></div>
              <div v-else class="plain-content">{{ msg.content }}</div>
            </div>
          </div>
          <div v-if="streaming" class="message-row assistant">
            <div class="message-bubble assistant">
              <div class="md-content" v-html="renderMd(streamContent)"></div>
              <span class="typing-cursor">▌</span>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="input-area">
          <n-input
            v-model:value="inputText"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="输入消息，Enter 发送，Shift+Enter 换行"
            :disabled="streaming"
            @keydown="handleKeydown"
          />
          <n-button
            type="primary"
            :disabled="!inputText.trim() || streaming"
            :loading="streaming"
            @click="sendMessage"
          >
            发送
          </n-button>
        </div>
      </template>

      <div v-else class="empty-state">
        <n-empty description="选择或新建一个对话开始聊天">
          <template #extra>
            <n-button type="primary" @click="createSession">新建对话</n-button>
          </template>
        </n-empty>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { NButton, NIcon, NInput, NEmpty, useMessage, useDialog } from 'naive-ui'
import { AddCircleOutline as AddIcon, TrashOutline as TrashIcon } from '@vicons/ionicons5'
import MarkdownIt from 'markdown-it'
import axios from 'axios'

const message = useMessage()
const dialog = useDialog()

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

interface Session {
  id: number
  title: string
  message_count: number
}

interface Message {
  role: string
  content: string
}

const sessions = ref<Session[]>([])
const currentSessionId = ref<number | null>(null)
const messages = ref<Message[]>([])
const inputText = ref('')
const streaming = ref(false)
const streamContent = ref('')
const messagesRef = ref<HTMLElement | null>(null)

// ── Helpers ──

function renderMd(text: string): string {
  // Strip <think>...</think> blocks
  const cleaned = text.replace(/<think>[\s\S]*?<\/think>/g, '')
  return md.render(cleaned)
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// ── Session Management ──

async function loadSessions() {
  try {
    const { data } = await axios.get('/api/chat/sessions')
    sessions.value = data
  } catch {
    message.error('加载对话列表失败')
  }
}

async function createSession() {
  try {
    const { data } = await axios.post('/api/chat/sessions', {})
    sessions.value.unshift(data)
    selectSession(data.id)
  } catch {
    message.error('创建对话失败')
  }
}

async function selectSession(id: number) {
  currentSessionId.value = id
  try {
    const { data } = await axios.get(`/api/chat/sessions/${id}`)
    messages.value = data.messages.map((m: any) => ({ role: m.role, content: m.content }))
    scrollToBottom()
  } catch {
    message.error('加载对话消息失败')
  }
}

function confirmDelete(id: number) {
  dialog.warning({
    title: '删除对话',
    content: '确定要删除这个对话吗？',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => deleteSession(id),
  })
}

async function deleteSession(id: number) {
  try {
    await axios.delete(`/api/chat/sessions/${id}`)
    sessions.value = sessions.value.filter((s) => s.id !== id)
    if (currentSessionId.value === id) {
      currentSessionId.value = null
      messages.value = []
    }
  } catch {
    message.error('删除对话失败')
  }
}

// ── Send Message + SSE ──

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    if (inputText.value.trim() && !streaming.value) {
      sendMessage()
    }
  }
}

async function sendMessage() {
  const content = inputText.value.trim()
  if (!content || !currentSessionId.value) return

  inputText.value = ''
  messages.value.push({ role: 'user', content })
  scrollToBottom()

  streaming.value = true
  streamContent.value = ''

  try {
    const response = await fetch(`/api/chat/sessions/${currentSessionId.value}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    })

    if (!response.ok || !response.body) {
      throw new Error('Stream failed')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const payload = line.slice(6).trim()
        if (payload === '[DONE]') break
        try {
          const parsed = JSON.parse(payload)
          if (parsed.content) {
            streamContent.value += parsed.content
            scrollToBottom()
          }
          if (parsed.error) {
            message.error(parsed.error)
          }
        } catch {
          // skip malformed JSON
        }
      }
    }

    // Save streamed message to local list
    if (streamContent.value) {
      messages.value.push({ role: 'assistant', content: streamContent.value })
    }
  } catch {
    message.error('发送消息失败')
  } finally {
    streaming.value = false
    streamContent.value = ''
    scrollToBottom()
    // Refresh session list to get updated title
    loadSessions()
  }
}

// ── Init ──

onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.chat-container {
  display: flex;
  min-height: calc(100vh - 160px);
  border: 1px solid var(--admin-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: color-mix(in srgb, var(--admin-surface) 92%, transparent);
}

.chat-sidebar {
  width: 280px;
  min-width: 280px;
  border-right: 1px solid var(--admin-border);
  display: flex;
  flex-direction: column;
  background: color-mix(in srgb, var(--admin-surface) 96%, transparent);
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--admin-border);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.session-item:hover {
  background: rgba(128, 128, 128, 0.1);
}

.session-item.active {
  background: rgba(24, 160, 88, 0.15);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  font-size: 12px;
  opacity: 0.5;
  margin-top: 2px;
}

.session-delete {
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-delete {
  opacity: 1;
}

/* Main area */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: inherit;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
}

.message-row {
  display: flex;
  margin-bottom: 16px;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 75%;
  padding: 10px 16px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.message-bubble.user {
  background: linear-gradient(135deg, #1fa96a, #178f6a);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-bubble.assistant {
  background: color-mix(in srgb, var(--admin-text-muted) 20%, transparent);
  border-bottom-left-radius: 4px;
}

.md-content :deep(p) {
  margin: 0 0 8px 0;
}

.md-content :deep(p:last-child) {
  margin-bottom: 0;
}

.md-content :deep(pre) {
  background: color-mix(in srgb, var(--admin-text-muted) 22%, transparent);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.md-content :deep(code) {
  font-size: 13px;
}

.md-content :deep(ul),
.md-content :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}

.typing-cursor {
  display: inline-block;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Input area */
.input-area {
  padding: 14px 16px;
  border-top: 1px solid var(--admin-border);
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-area .n-input {
  flex: 1;
}

/* Empty state */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.plain-content {
  white-space: pre-wrap;
}

@media (max-width: 900px) {
  .chat-container {
    flex-direction: column;
    min-height: auto;
  }

  .chat-sidebar {
    width: 100%;
    min-width: 0;
    max-height: 220px;
  }
}
</style>
