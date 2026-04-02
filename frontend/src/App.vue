<template>
  <AppLayout v-if="!route.meta.hideLayout" />
  <router-view v-else />
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import AppLayout from './AppLayout.vue'

const route = useRoute()
</script>

