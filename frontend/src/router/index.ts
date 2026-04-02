import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/SearchView.vue'),
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/HistoryView.vue'),
  },
  {
    path: '/trends',
    name: 'Trends',
    component: () => import('../views/TrendsView.vue'),
  },
  {
    path: '/recommend',
    name: 'Recommend',
    component: () => import('../views/RecommendView.vue'),
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('../views/LogsView.vue'),
  },
  {
    path: '/briefings',
    name: 'Briefings',
    component: () => import('../views/BriefingsView.vue'),
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
  },
  {
    path: '/knowledge-base',
    name: 'KnowledgeBase',
    component: () => import('../views/KnowledgeBaseView.vue'),
  },
  {
    path: '/sources',
    name: 'Sources',
    component: () => import('../views/SourcesView.vue'),
  },
  {
    path: '/share/:token',
    name: 'Share',
    component: () => import('../views/ShareView.vue'),
    meta: { hideLayout: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
