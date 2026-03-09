import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import { storage } from '@/utils/storage'
import type { User, LoginData, RegisterData } from '@/types/user'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(storage.getToken())
  const user = ref<User | null>(storage.getUser())
  const loading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)

  // 登录
  const login = async (data: LoginData) => {
    loading.value = true
    try {
      const res = await authApi.login(data)
      token.value = res.access_token
      storage.setToken(res.access_token)
      
      if (res.refresh_token) {
        storage.setRefreshToken(res.refresh_token)
      }
      
      // 获取用户信息
      await fetchUserInfo()
      
      return res
    } finally {
      loading.value = false
    }
  }

  // 注册
  const register = async (data: RegisterData) => {
    loading.value = true
    try {
      const res = await authApi.register(data)
      return res
    } finally {
      loading.value = false
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const userData = await authApi.getCurrentUser()
      user.value = userData
      storage.setUser(userData)
      return userData
    } catch (error) {
      console.error('Failed to fetch user info:', error)
      throw error
    }
  }

  // 登出
  const logout = () => {
    token.value = null
    user.value = null
    storage.clear()
  }

  // 检查认证状态
  const checkAuth = async () => {
    if (token.value && !user.value) {
      try {
        await fetchUserInfo()
      } catch (error) {
        // Token无效，清除登录状态
        logout()
      }
    }
  }

  // 刷新Token
  const refreshToken = async () => {
    const refreshTok = storage.getRefreshToken()
    if (!refreshTok) {
      throw new Error('No refresh token')
    }
    
    try {
      const res = await authApi.refreshToken(refreshTok)
      token.value = res.access_token
      storage.setToken(res.access_token)
      
      if (res.refresh_token) {
        storage.setRefreshToken(res.refresh_token)
      }
      
      return res
    } catch (error) {
      logout()
      throw error
    }
  }

  return {
    token,
    user,
    loading,
    isLoggedIn,
    login,
    register,
    logout,
    fetchUserInfo,
    checkAuth,
    refreshToken
  }
})
