<template>
  <div class="share-page">
    <div class="share-container">
      <!-- Loading -->
      <div v-if="loading" class="share-loading">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- Error: expired -->
      <div v-else-if="error === 'expired'" class="share-error">
        <div class="error-icon">⏰</div>
        <h2>此简报链接已失效</h2>
        <p>该分享链接已过期或已被取消。</p>
      </div>

      <!-- Error: not found -->
      <div v-else-if="error" class="share-error">
        <div class="error-icon">🔗</div>
        <h2>链接无效</h2>
        <p>该分享链接不存在或已被删除。</p>
      </div>

      <!-- Content -->
      <article v-else-if="briefing" class="share-article">
        <header class="share-header">
          <div class="share-dots">·  ·  ·</div>
          <h1>{{ briefing.title }}</h1>
          <div class="share-meta">
            {{ formatDate(briefing.created_at) }} · {{ typeLabel(briefing.brief_type) }}
          </div>
          <hr />
        </header>

        <div class="share-content" v-html="renderMarkdown(briefing.content || '')"></div>

        <div v-if="briefing.items && briefing.items.length > 0" class="share-references">
          <hr />
          <h2>引用来源</h2>
          <ol>
            <li v-for="(item, i) in briefing.items" :key="i">
              <a :href="item.url" target="_blank" rel="noopener">{{ item.title }}</a>
              <span class="ref-source"> — {{ item.source_display_name || item.source }}</span>
            </li>
          </ol>
        </div>
      </article>

      <!-- Footer -->
      <footer class="share-footer">
        <hr />
        <div class="footer-brand">
          <span class="footer-icon">🔥</span>
          <span>Powered by <a href="/" class="brand-link">NewsHub</a></span>
          <span class="footer-sep">·</span>
          <a href="/" class="brand-link">查看更多热点简报 →</a>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'
import { getSharedBriefing, type SharedBriefing } from '../api'

const route = useRoute()
const md = new MarkdownIt()

const loading = ref(true)
const error = ref('')
const briefing = ref<SharedBriefing | null>(null)

function typeLabel(t: string) {
  const m: Record<string, string> = { source: '单来源简报', daily: '每日汇总', topic: '主题简报', custom: '自选简报' }
  return m[t] || t
}

function formatDate(t: string) {
  if (!t) return ''
  return new Date(t).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

function renderMarkdown(text: string) {
  const cleaned = (text || '').replace(/<think>[\s\S]*?<\/think>/g, '').trimStart()
  return md.render(cleaned)
}

onMounted(async () => {
  const token = route.params.token as string
  try {
    briefing.value = await getSharedBriefing(token)
  } catch (e: any) {
    if (e.response?.status === 410) {
      error.value = 'expired'
    } else {
      error.value = 'not_found'
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.share-page {
  min-height: 100vh;
  background: #fafafa;
  color: #1a1a1a;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

.share-container {
  max-width: 720px;
  margin: 0 auto;
  padding: 48px 24px 64px;
}

/* Loading */
.share-loading {
  text-align: center;
  padding: 120px 0;
  color: #999;
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e0e0e0;
  border-top-color: #333;
  border-radius: 50%;
  margin: 0 auto 16px;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Error */
.share-error {
  text-align: center;
  padding: 100px 0;
}
.error-icon {
  font-size: 48px;
  margin-bottom: 20px;
}
.share-error h2 {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 12px;
  color: #333;
}
.share-error p {
  font-size: 15px;
  color: #888;
}

/* Article */
.share-article {
  line-height: 1.8;
}

.share-header {
  text-align: center;
  margin-bottom: 32px;
}
.share-dots {
  color: #ccc;
  font-size: 18px;
  letter-spacing: 8px;
  margin-bottom: 24px;
}
.share-header h1 {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 12px;
  line-height: 1.4;
  color: #111;
}
.share-meta {
  font-size: 14px;
  color: #888;
  margin-bottom: 24px;
}
.share-header hr {
  border: none;
  border-top: 1px solid #e5e5e5;
}

/* Content */
.share-content {
  font-size: 16px;
  color: #333;
}
.share-content :deep(h2) {
  font-size: 20px;
  font-weight: 600;
  margin: 32px 0 16px;
  color: #111;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}
.share-content :deep(h3) {
  font-size: 17px;
  font-weight: 600;
  margin: 24px 0 12px;
  color: #222;
}
.share-content :deep(p) {
  margin: 12px 0;
}
.share-content :deep(ul),
.share-content :deep(ol) {
  padding-left: 24px;
  margin: 12px 0;
}
.share-content :deep(li) {
  margin: 6px 0;
}
.share-content :deep(blockquote) {
  border-left: 3px solid #ddd;
  padding-left: 16px;
  margin: 16px 0;
  color: #666;
}

/* References */
.share-references {
  margin-top: 40px;
}
.share-references hr {
  border: none;
  border-top: 1px solid #e5e5e5;
  margin-bottom: 24px;
}
.share-references h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px;
  color: #111;
}
.share-references ol {
  padding-left: 24px;
}
.share-references li {
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.6;
}
.share-references a {
  color: #1a73e8;
  text-decoration: none;
}
.share-references a:hover {
  text-decoration: underline;
}
.ref-source {
  color: #999;
  font-size: 13px;
}

/* Footer */
.share-footer {
  margin-top: 48px;
}
.share-footer hr {
  border: none;
  border-top: 1px solid #e5e5e5;
  margin-bottom: 24px;
}
.footer-brand {
  text-align: center;
  font-size: 14px;
  color: #999;
}
.footer-icon {
  font-size: 16px;
}
.footer-sep {
  margin: 0 8px;
}
.brand-link {
  color: #1a73e8;
  text-decoration: none;
  font-weight: 500;
}
.brand-link:hover {
  text-decoration: underline;
}
</style>
