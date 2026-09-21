import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const currentPath = ref('/dashboard')

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setCurrentPath = (path) => {
    currentPath.value = path
  }

  return {
    sidebarCollapsed,
    currentPath,
    toggleSidebar,
    setCurrentPath
  }
})
