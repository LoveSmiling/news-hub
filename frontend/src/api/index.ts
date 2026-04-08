import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export interface HotItem {
  id: number
  source: string
  title: string
  url: string
  rank: number | null
  hot_value: string | null
  category: string | null
  summary: string | null
  keywords: string[] | null
  collected_at: string
}

export interface SourceInfo {
  id: number
  name: string
  display_name: string
  category: string | null
  type: string
  route: string
  url: string
  schedule: string
  max_items: number
  status: string
  last_collected_at: string | null
  created_at: string | null
}

export interface GroupedHot {
  source: string
  display_name: string
  category: string | null
  items: HotItem[]
}

export async function fetchGroupedHot(category?: string): Promise<GroupedHot[]> {
  const params: Record<string, string> = {}
  if (category) params.category = category
  const { data } = await api.get('/hot', { params })
  return data
}

export async function fetchHotBySource(source: string, page = 1, size = 50): Promise<{ items: HotItem[]; total: number }> {
  const { data } = await api.get(`/hot/${source}`, { params: { page, size } })
  return data
}

export async function fetchSources(): Promise<SourceInfo[]> {
  const { data } = await api.get('/sources')
  return data
}

export interface SearchParams {
  q: string
  source?: string
  category?: string
  start_date?: string
  end_date?: string
  page?: number
  size?: number
}

export interface PaginatedResult {
  items: HotItem[]
  total: number
  page: number
  page_size: number
}

export async function searchHotItems(params: SearchParams): Promise<PaginatedResult> {
  const { data } = await api.get('/search', { params })
  return data
}

export async function fetchHistory(source: string, date: string, page = 1, size = 50): Promise<PaginatedResult> {
  const { data } = await api.get(`/history/${source}/${date}`, { params: { page, size } })
  return data
}

export async function fetchAvailableDates(source: string): Promise<{ source: string; dates: string[] }> {
  const { data } = await api.get(`/history/dates/${source}`)
  return data
}

export async function generateSummary(itemId: number): Promise<{ id: number; summary: string }> {
  const { data } = await api.post(`/ai/summary/${itemId}`)
  return data
}

export async function generateKeywords(itemId: number): Promise<{ id: number; keywords: string[] }> {
  const { data } = await api.post(`/ai/keywords/${itemId}`)
  return data
}

export async function fetchTrends(hours = 24): Promise<any> {
  const { data } = await api.get('/trends', { params: { hours } })
  return data
}

export async function fetchBursts(window = 6): Promise<any> {
  const { data } = await api.get('/trends/bursts', { params: { window } })
  return data
}

export async function fetchHotCurve(source: string, hours = 24): Promise<any> {
  const { data } = await api.get(`/trends/hot-curve/${source}`, { params: { hours } })
  return data
}

export async function fetchRecommendations(
  categories: string[],
  readItemIds: number[],
  limit = 20,
): Promise<{ items: HotItem[]; strategy: string }> {
  const { data } = await api.post('/recommend', {
    categories,
    read_item_ids: readItemIds,
    limit,
  })
  return data
}

// ---- AI Config ----

export interface AIConfigItem {
  id: number
  name: string
  provider_type: 'llm' | 'embedding'
  api_base: string
  api_key_set: boolean
  model: string
  enabled: boolean
  is_default: boolean
  extra: Record<string, any> | null
}

export interface AIConfigPayload {
  name: string
  provider_type: 'llm' | 'embedding'
  api_base: string
  api_key?: string | null
  model: string
  enabled?: boolean
  is_default?: boolean
  extra?: Record<string, any> | null
}

export interface TestResult {
  success: boolean
  message: string
  latency_ms: number | null
}

export async function fetchAIConfigs(type?: string): Promise<AIConfigItem[]> {
  const params: Record<string, string> = {}
  if (type) params.provider_type = type
  const { data } = await api.get('/ai-config', { params })
  return data
}

export async function createAIConfig(payload: AIConfigPayload): Promise<AIConfigItem> {
  const { data } = await api.post('/ai-config', payload)
  return data
}

export async function updateAIConfig(id: number, payload: Partial<AIConfigPayload>): Promise<AIConfigItem> {
  const { data } = await api.put(`/ai-config/${id}`, payload)
  return data
}

export async function deleteAIConfig(id: number): Promise<void> {
  await api.delete(`/ai-config/${id}`)
}

export async function testAIConfig(id: number): Promise<TestResult> {
  const { data } = await api.post(`/ai-config/${id}/test`, null, { timeout: 30000 })
  return data
}

export async function testAIConfigInline(payload: AIConfigPayload): Promise<TestResult> {
  const { data } = await api.post('/ai-config/test-inline', payload, { timeout: 30000 })
  return data
}

// ---- AI Usage Logs ----

export interface LogItem {
  id: number
  action: string
  provider_type: string
  provider_name: string | null
  model: string | null
  prompt_tokens: number | null
  completion_tokens: number | null
  total_tokens: number | null
  latency_ms: number | null
  success: boolean
  error_message: string | null
  meta: Record<string, any> | null
  created_at: string
}

export interface LogListResponse {
  total: number
  page: number
  page_size: number
  items: LogItem[]
}

export interface LogStatsOverview {
  total_calls: number
  success_count: number
  error_count: number
  total_prompt_tokens: number
  total_completion_tokens: number
  total_tokens: number
  avg_latency_ms: number
}

export interface LogStatsAction {
  action: string
  calls: number
  tokens: number
  successes: number
  errors: number
  avg_latency_ms: number
}

export interface LogStatsTimeline {
  time: string
  calls: number
  tokens: number
}

export interface LogStats {
  hours: number
  overview: LogStatsOverview
  by_action: LogStatsAction[]
  timeline: LogStatsTimeline[]
}

export async function fetchLogs(params: {
  action?: string
  provider_type?: string
  success?: boolean
  hours?: number
  page?: number
  page_size?: number
}): Promise<LogListResponse> {
  const { data } = await api.get('/logs', { params })
  return data
}

export async function fetchLogStats(hours?: number): Promise<LogStats> {
  const params: Record<string, any> = {}
  if (hours) params.hours = hours
  const { data } = await api.get('/logs/stats', { params })
  return data
}

export async function triggerEnrichKeywords(limit?: number): Promise<{ total: number; success: number; errors: number }> {
  const params: Record<string, any> = {}
  if (limit) params.limit = limit
  const { data } = await api.post('/enrich-keywords', null, { params, timeout: 120000 })
  return data
}

// ---- Source Management ----

export interface SourceCreatePayload {
  name: string
  display_name: string
  category: string
  type: string
  route?: string
  url?: string
  schedule?: string
  max_items?: number
}

export interface SourceUpdatePayload {
  display_name?: string
  category?: string
  type?: string
  route?: string
  url?: string
  schedule?: string
  max_items?: number
}

export interface SourceTestPayload {
  type: string
  route?: string
  url?: string
  max_items?: number
}

export interface SourceTestResult {
  success: boolean
  items: { title: string; url: string; rank: number | null }[]
  count: number
  elapsed_ms: number
  error: string
}

export interface BatchActionPayload {
  ids: number[]
  action: 'enable' | 'disable' | 'set_category' | 'collect'
  category?: string
}

export async function fetchSource(id: number): Promise<SourceInfo> {
  const { data } = await api.get(`/sources/${id}`)
  return data
}

export async function createSource(payload: SourceCreatePayload): Promise<SourceInfo> {
  const { data } = await api.post('/sources', payload)
  return data
}

export async function updateSource(id: number, payload: SourceUpdatePayload): Promise<SourceInfo> {
  const { data } = await api.put(`/sources/${id}`, payload)
  return data
}

export async function deleteSource(id: number): Promise<{ detail: string }> {
  const { data } = await api.delete(`/sources/${id}`)
  return data
}

export async function testSource(payload: SourceTestPayload): Promise<SourceTestResult> {
  const { data } = await api.post('/sources/test', payload, { timeout: 30000 })
  return data
}

export async function collectSourceNow(id: number): Promise<{ detail: string; count: number }> {
  const { data } = await api.post(`/sources/${id}/collect`, null, { timeout: 60000 })
  return data
}

export async function fetchCategories(): Promise<string[]> {
  const { data } = await api.get('/sources/categories')
  return data
}

export async function batchSourceAction(payload: BatchActionPayload): Promise<{ detail: string; results: Record<string, string> }> {
  const { data } = await api.patch('/sources/batch', payload, { timeout: 120000 })
  return data
}

// ---- Source Import/Export ----

export interface SourceImportItem {
  name: string
  display_name: string
  category: string
  type: string
  route?: string
  url?: string
  schedule?: string
  max_items?: number
  status?: string
}

export interface SourceImportPayload {
  version: number
  sources: SourceImportItem[]
}

export interface SourceImportResult {
  created: number
  updated: number
  errors: { name: string; error: string }[]
}

export async function exportSources(): Promise<void> {
  const { data } = await api.get('/sources/export', { responseType: 'blob' })
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  a.href = url
  a.download = `sources_export_${today}.json`
  a.click()
  URL.revokeObjectURL(url)
}

export async function importSources(payload: SourceImportPayload): Promise<SourceImportResult> {
  const { data } = await api.post('/sources/import', payload)
  return data
}

// ---- Briefing Share ----

export interface ShareResponse {
  share_token: string
  share_url: string
  expires_at: string | null
}

export interface SharedBriefing {
  title: string
  brief_type: string
  content: string | null
  created_at: string
  completed_at: string | null
  items: { id: number; title: string; source: string; url: string }[]
}

export async function createShare(briefingId: number, expiresIn: string | null = '7d'): Promise<ShareResponse> {
  const { data } = await api.post(`/briefings/${briefingId}/share`, { expires_in: expiresIn })
  return data
}

export async function deleteShare(briefingId: number): Promise<{ detail: string }> {
  const { data } = await api.delete(`/briefings/${briefingId}/share`)
  return data
}

export async function getSharedBriefing(token: string): Promise<SharedBriefing> {
  const { data } = await api.get(`/share/${token}`)
  return data
}

export default api
