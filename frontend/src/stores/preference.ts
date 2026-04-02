import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const usePreferenceStore = defineStore('preference', () => {
  const preferredCategories = ref<string[]>(
    JSON.parse(localStorage.getItem('preferredCategories') || '[]')
  )
  const readHistory = ref<number[]>(
    JSON.parse(localStorage.getItem('readHistory') || '[]')
  )

  watch(preferredCategories, (val) => {
    localStorage.setItem('preferredCategories', JSON.stringify(val))
  }, { deep: true })

  watch(readHistory, (val) => {
    localStorage.setItem('readHistory', JSON.stringify(val))
  }, { deep: true })

  function toggleCategory(cat: string) {
    const idx = preferredCategories.value.indexOf(cat)
    if (idx >= 0) {
      preferredCategories.value.splice(idx, 1)
    } else {
      preferredCategories.value.push(cat)
    }
  }

  function recordRead(itemId: number) {
    // Keep latest 200 items to avoid localStorage bloat
    if (!readHistory.value.includes(itemId)) {
      readHistory.value.unshift(itemId)
      if (readHistory.value.length > 200) {
        readHistory.value = readHistory.value.slice(0, 200)
      }
    }
  }

  function clearHistory() {
    readHistory.value = []
  }

  return {
    preferredCategories,
    readHistory,
    toggleCategory,
    recordRead,
    clearHistory,
  }
})
