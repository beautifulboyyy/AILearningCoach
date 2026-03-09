// 本地存储工具

const TOKEN_KEY = 'ai_coach_token'
const REFRESH_TOKEN_KEY = 'ai_coach_refresh_token'
const USER_KEY = 'ai_coach_user'

export const storage = {
  // Token相关
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },
  
  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
  },
  
  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY)
  },
  
  // Refresh Token
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },
  
  setRefreshToken(token: string): void {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  },
  
  removeRefreshToken(): void {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
  
  // 用户信息
  getUser<T = any>(): T | null {
    const user = localStorage.getItem(USER_KEY)
    return user ? JSON.parse(user) : null
  },
  
  setUser(user: any): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  
  removeUser(): void {
    localStorage.removeItem(USER_KEY)
  },
  
  // 清除所有
  clear(): void {
    this.removeToken()
    this.removeRefreshToken()
    this.removeUser()
  },
  
  // 通用方法
  get(key: string): string | null {
    return localStorage.getItem(key)
  },
  
  set(key: string, value: string): void {
    localStorage.setItem(key, value)
  },
  
  remove(key: string): void {
    localStorage.removeItem(key)
  }
}

// 导出常用函数的快捷方式
export const getToken = () => storage.getToken()
export const setToken = (token: string) => storage.setToken(token)
export const removeToken = () => storage.removeToken()
export const getUser = () => storage.getUser()
export const setUser = (user: any) => storage.setUser(user)
