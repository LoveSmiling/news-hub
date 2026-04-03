<template>
  <div class="admin-shell">
    <header class="admin-header">
      <div class="layout-content-container admin-header-inner">
        <div class="admin-brand" @click="router.push('/chat')">
          <span class="brand-badge">Studio</span>
          <span class="brand-name">NewsHub 工作台</span>
        </div>

        <nav class="admin-nav desktop-nav">
          <n-button text :type="isRoute('/chat') ? 'primary' : 'default'" @click="router.push('/chat')">对话</n-button>
          <n-button text :type="isRoute('/briefings') ? 'primary' : 'default'" @click="router.push('/briefings')">简报</n-button>
          <n-button text :type="isRoute('/knowledge-base') ? 'primary' : 'default'" @click="router.push('/knowledge-base')">知识库</n-button>
          <n-button text :type="isRoute('/sources') ? 'primary' : 'default'" @click="router.push('/sources')">源管理</n-button>
          <n-button text :type="isRoute('/logs') ? 'primary' : 'default'" @click="router.push('/logs')">日志</n-button>
          <n-button text :type="isRoute('/settings') ? 'primary' : 'default'" @click="router.push('/settings')">设置</n-button>
        </nav>

        <div class="admin-actions">
          <n-button quaternary circle class="mobile-trigger" @click="drawerOpen = true">
            <template #icon>
              <n-icon><menu-icon /></n-icon>
            </template>
          </n-button>
          <n-switch :value="isDark" @update:value="themeStore.setDark">
            <template #checked>
              <n-icon><moon-icon /></n-icon>
            </template>
            <template #unchecked>
              <n-icon><sunny-icon /></n-icon>
            </template>
          </n-switch>
          <n-button quaternary @click="router.push('/')">返回前台</n-button>
        </div>
      </div>
    </header>

    <main class="admin-main">
      <div class="layout-content-container admin-content-wrap">
        <router-view />
      </div>
    </main>

    <n-drawer v-model:show="drawerOpen" placement="right" :width="300">
      <n-drawer-content title="工作台导航" closable>
        <div class="mobile-nav-list">
          <n-button block tertiary :type="isRoute('/chat') ? 'primary' : 'default'" @click="navigate('/chat')">对话</n-button>
          <n-button block tertiary :type="isRoute('/briefings') ? 'primary' : 'default'" @click="navigate('/briefings')">简报</n-button>
          <n-button block tertiary :type="isRoute('/knowledge-base') ? 'primary' : 'default'" @click="navigate('/knowledge-base')">知识库</n-button>
          <n-button block tertiary :type="isRoute('/sources') ? 'primary' : 'default'" @click="navigate('/sources')">源管理</n-button>
          <n-button block tertiary :type="isRoute('/logs') ? 'primary' : 'default'" @click="navigate('/logs')">日志</n-button>
          <n-button block tertiary :type="isRoute('/settings') ? 'primary' : 'default'" @click="navigate('/settings')">设置</n-button>
          <n-button block tertiary @click="navigate('/')">返回前台</n-button>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton,
  NIcon,
  NSwitch,
  NDrawer,
  NDrawerContent,
} from 'naive-ui'
import {
  MenuOutline as MenuIcon,
  Moon as MoonIcon,
  Sunny as SunnyIcon,
} from '@vicons/ionicons5'
import { useThemeStore } from '../stores/theme'

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()
const drawerOpen = ref(false)

const isDark = computed(() => themeStore.isDark)

function isRoute(path: string) {
  return route.path === path
}

function navigate(path: string) {
  drawerOpen.value = false
  router.push(path)
}
</script>

<style scoped>
.admin-shell {
  min-height: 100vh;
  color: var(--admin-text);
}

.admin-header {
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid var(--admin-border);
  background: color-mix(in srgb, var(--admin-surface) 92%, transparent);
  backdrop-filter: blur(10px);
}

.admin-header-inner {
  min-height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.admin-brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.brand-badge {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  padding: 2px 8px;
  border-radius: 999px;
  background: linear-gradient(135deg, #ff6f61, #f14d42);
}

.brand-name {
  font-size: 18px;
  font-weight: 700;
}

.admin-nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.admin-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.mobile-trigger {
  display: none;
}

.admin-main {
  padding: 18px 0 30px;
}

.admin-content-wrap {
  background: color-mix(in srgb, var(--admin-surface) 88%, transparent);
  border: 1px solid var(--admin-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--admin-shadow);
  padding: 18px;
}

.mobile-nav-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 1060px) {
  .desktop-nav {
    display: none;
  }

  .mobile-trigger {
    display: inline-flex;
  }
}

@media (max-width: 768px) {
  .admin-content-wrap {
    border-radius: var(--radius-md);
    padding: 14px;
  }

  .brand-name {
    font-size: 16px;
  }
}
</style>
