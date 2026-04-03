import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { GroupedHot } from '../api'

const STORAGE_KEY = 'newshub-card-order'

export const useCardOrderStore = defineStore('cardOrder', () => {
  const orderedSources = ref<string[]>(loadFromStorage())

  function loadFromStorage(): string[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? JSON.parse(raw) : []
    } catch {
      return []
    }
  }

  function saveToStorage() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(orderedSources.value))
  }

  function sortGroups(groups: GroupedHot[]): GroupedHot[] {
    const saved = orderedSources.value
    if (saved.length === 0) {
      // First visit: use API order and save it
      orderedSources.value = groups.map(g => g.source)
      saveToStorage()
      return groups
    }

    const groupMap = new Map(groups.map(g => [g.source, g]))

    // Ordered groups: follow saved order, skip missing
    const result: GroupedHot[] = []
    const seen = new Set<string>()

    for (const source of saved) {
      const group = groupMap.get(source)
      if (group) {
        result.push(group)
        seen.add(source)
      }
    }

    // Append new sources not in saved order
    for (const group of groups) {
      if (!seen.has(group.source)) {
        result.push(group)
      }
    }

    // Clean up: update orderedSources to reflect current reality
    orderedSources.value = result.map(g => g.source)
    saveToStorage()

    return result
  }

  function updateOrder(sources: string[]) {
    orderedSources.value = sources
    saveToStorage()
  }

  return { orderedSources, sortGroups, updateOrder }
})
