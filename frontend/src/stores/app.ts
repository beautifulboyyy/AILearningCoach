import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 侧边栏状态
  const sidebarCollapsed = ref(false)
  
  // 加载状态
  const globalLoading = ref(false)
  
  // 主题
  const theme = ref<'light' | 'dark'>('light')
  
  // 切换侧边栏
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  
  // 设置加载状态
  const setLoading = (loading: boolean) => {
    globalLoading.value = loading
  }
  
  // 切换主题
  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    document.documentElement.classList.toggle('dark')
  }

  return {
    sidebarCollapsed,
    globalLoading,
    theme,
    toggleSidebar,
    setLoading,
    toggleTheme
  }
})
