import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: { layout: 'front' },
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/SearchView.vue'),
    meta: { layout: 'front' },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/HistoryView.vue'),
    meta: { layout: 'front' },
  },
  {
    path: '/trends',
    name: 'Trends',
    component: () => import('../views/TrendsView.vue'),
    meta: { layout: 'front' },
  },
  {
    path: '/recommend',
    name: 'Recommend',
    component: () => import('../views/RecommendView.vue'),
    meta: { layout: 'front' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { layout: 'admin' },
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('../views/LogsView.vue'),
    meta: { layout: 'admin' },
  },
  {
    path: '/briefings',
    name: 'Briefings',
    component: () => import('../views/BriefingsView.vue'),
    meta: { layout: 'admin' },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
    meta: { layout: 'admin' },
  },
  {
    path: '/knowledge-base',
    name: 'KnowledgeBase',
    component: () => import('../views/KnowledgeBaseView.vue'),
    meta: { layout: 'admin' },
  },
  {
    path: '/sources',
    name: 'Sources',
    component: () => import('../views/SourcesView.vue'),
    meta: { layout: 'admin' },
  },
  {
    path: '/share/:token',
    name: 'Share',
    component: () => import('../views/ShareView.vue'),
    meta: { layout: 'front' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
