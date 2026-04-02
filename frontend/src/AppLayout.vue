<template>
  <n-config-provider :theme="theme" :locale="zhCN" :date-locale="dateZhCN">
    <n-global-style />
    <n-message-provider>
    <n-dialog-provider>
    <n-layout class="app-layout">
      <n-layout-header bordered class="app-header">
        <div class="header-content">
          <div class="logo" @click="router.push('/')">
            <n-icon size="24"><flame-icon /></n-icon>
            <span class="logo-text">NewsHub</span>
          </div>
          <div class="header-nav">
            <n-button text :type="isRoute('/') ? 'primary' : 'default'" @click="router.push('/')">热榜</n-button>
            <n-button text :type="isRoute('/search') ? 'primary' : 'default'" @click="router.push('/search')">搜索</n-button>
            <n-button text :type="isRoute('/history') ? 'primary' : 'default'" @click="router.push('/history')">历史</n-button>
            <n-button text :type="isRoute('/trends') ? 'primary' : 'default'" @click="router.push('/trends')">趋势</n-button>
            <n-button text :type="isRoute('/recommend') ? 'primary' : 'default'" @click="router.push('/recommend')">推荐</n-button>
            <n-button text :type="isRoute('/settings') ? 'primary' : 'default'" @click="router.push('/settings')">设置</n-button>
            <n-button text :type="isRoute('/logs') ? 'primary' : 'default'" @click="router.push('/logs')">日志</n-button>
            <n-button text :type="isRoute('/chat') ? 'primary' : 'default'" @click="router.push('/chat')">对话</n-button>
            <n-button text :type="isRoute('/briefings') ? 'primary' : 'default'" @click="router.push('/briefings')">简报</n-button>
            <n-button text :type="isRoute('/knowledge-base') ? 'primary' : 'default'" @click="router.push('/knowledge-base')">知识库</n-button>
            <n-button text :type="isRoute('/sources') ? 'primary' : 'default'" @click="router.push('/sources')">源管理</n-button>
          </div>
          <div class="header-actions">
            <n-switch :value="isDark" @update:value="toggleDark">
              <template #checked>
                <n-icon><moon-icon /></n-icon>
              </template>
              <template #unchecked>
                <n-icon><sunny-icon /></n-icon>
              </template>
            </n-switch>
          </div>
        </div>
      </n-layout-header>
      <n-layout-content class="app-content">
        <router-view />
      </n-layout-content>
    </n-layout>
    </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NConfigProvider,
  NGlobalStyle,
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NIcon,
  NSwitch,
  NButton,
  NMessageProvider,
  NDialogProvider,
  darkTheme,
  zhCN,
  dateZhCN,
} from 'naive-ui'
import { Flame as FlameIcon, Moon as MoonIcon, Sunny as SunnyIcon } from '@vicons/ionicons5'
import { useThemeStore } from './stores/theme'

const router = useRouter()
const route = useRoute()
const themeStore = useThemeStore()

const isDark = computed(() => themeStore.isDark)
const theme = computed(() => (isDark.value ? darkTheme : null))

function isRoute(path: string) {
  return route.path === path
}

function toggleDark(val: boolean) {
  themeStore.setDark(val)
}
</script>

<style>
body {
  margin: 0;
  padding: 0;
}

.app-layout {
  min-height: 100vh;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #f5222d, #fa8c16);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 20px;
  font-size: 15px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}
</style>
