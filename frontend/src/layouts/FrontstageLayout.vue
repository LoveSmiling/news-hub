<template>
  <div class="front-shell">
    <header class="front-header">
      <div class="front-reading-container front-header-inner">
        <div class="front-brand" @click="router.push('/')">
          <span class="brand-dot"></span>
          <span class="brand-title">NewsHub</span>
          <span class="brand-sub">实时热点阅读</span>
        </div>

        <nav class="front-nav" v-if="!isSharePage">
          <n-button text :type="isRoute('/') ? 'primary' : 'default'" @click="router.push('/')">首页</n-button>
          <n-button text :type="isRoute('/search') ? 'primary' : 'default'" @click="router.push('/search')">搜索</n-button>
          <n-button text :type="isRoute('/history') ? 'primary' : 'default'" @click="router.push('/history')">历史</n-button>
          <n-button text :type="isRoute('/trends') ? 'primary' : 'default'" @click="router.push('/trends')">趋势</n-button>
          <n-button text :type="isRoute('/recommend') ? 'primary' : 'default'" @click="router.push('/recommend')">推荐</n-button>
        </nav>

        <div class="front-actions" v-if="!isSharePage">
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
          <n-button quaternary @click="router.push('/chat')">工作台</n-button>
        </div>
      </div>
    </header>

    <main class="front-main">
      <div class="front-reading-container">
        <router-view />
      </div>
    </main>

    <n-drawer v-model:show="drawerOpen" placement="right" :width="280">
      <n-drawer-content title="阅读导航" closable>
        <div class="mobile-nav-list">
          <n-button block tertiary :type="isRoute('/') ? 'primary' : 'default'" @click="navigate('/')">首页</n-button>
          <n-button block tertiary :type="isRoute('/search') ? 'primary' : 'default'" @click="navigate('/search')">搜索</n-button>
          <n-button block tertiary :type="isRoute('/history') ? 'primary' : 'default'" @click="navigate('/history')">历史</n-button>
          <n-button block tertiary :type="isRoute('/trends') ? 'primary' : 'default'" @click="navigate('/trends')">趋势</n-button>
          <n-button block tertiary :type="isRoute('/recommend') ? 'primary' : 'default'" @click="navigate('/recommend')">推荐</n-button>
          <n-button block tertiary @click="navigate('/chat')">进入工作台</n-button>
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
const isSharePage = computed(() => route.path.startsWith('/share/'))

function isRoute(path: string) {
  return route.path === path
}

function navigate(path: string) {
  drawerOpen.value = false
  router.push(path)
}
</script>

<style scoped>
.front-shell {
  min-height: 100vh;
  color: var(--front-text);
}

.front-header {
  position: sticky;
  top: 0;
  z-index: 90;
  border-bottom: 1px solid var(--front-border);
  backdrop-filter: blur(10px);
  background: color-mix(in srgb, var(--front-surface) 90%, transparent);
}

.front-header-inner {
  min-height: 68px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.front-brand {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.brand-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--front-accent);
  box-shadow: 0 0 0 5px rgba(241, 77, 66, 0.15);
}

.brand-title {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.2px;
}

.brand-sub {
  font-size: 12px;
  color: var(--front-text-muted);
}

.front-nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.front-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.mobile-trigger {
  display: none;
}

.front-main {
  padding: 22px 0 34px;
}

.mobile-nav-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 980px) {
  .front-nav {
    display: none;
  }

  .mobile-trigger {
    display: inline-flex;
  }

  .brand-sub {
    display: none;
  }
}
</style>
