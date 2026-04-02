import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(localStorage.getItem('theme') === 'dark')

  function setDark(val: boolean) {
    isDark.value = val
    localStorage.setItem('theme', val ? 'dark' : 'light')
  }

  return { isDark, setDark }
})
