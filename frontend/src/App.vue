<template>
  <n-config-provider :theme="theme" :locale="zhCN" :date-locale="dateZhCN">
    <n-global-style />
    <n-message-provider>
      <n-dialog-provider>
        <FrontstageLayout v-if="layoutMode === 'front'" />
        <AdminWorkspaceLayout v-else-if="layoutMode === 'admin'" />
        <router-view v-else />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import {
  NConfigProvider,
  NGlobalStyle,
  NMessageProvider,
  NDialogProvider,
  darkTheme,
  zhCN,
  dateZhCN,
} from 'naive-ui'
import FrontstageLayout from './layouts/FrontstageLayout.vue'
import AdminWorkspaceLayout from './layouts/AdminWorkspaceLayout.vue'
import { useThemeStore } from './stores/theme'

const route = useRoute()
const themeStore = useThemeStore()

const layoutMode = computed(() => String(route.meta.layout || 'admin'))
const theme = computed(() => (themeStore.isDark ? darkTheme : null))

watchEffect(() => {
  document.documentElement.classList.toggle('dark', themeStore.isDark)
})
</script>

