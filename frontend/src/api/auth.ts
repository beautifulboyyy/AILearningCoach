import { request } from '@/utils/request'
import type { LoginData, RegisterData, AuthResponse, User } from '@/types/user'

// 认证相关API
export const authApi = {
  // 用户注册
  register(data: RegisterData): Promise<User> {
    return request.post('/api/v1/auth/register', data)
  },

  // 用户登录
  login(data: LoginData): Promise<AuthResponse> {
    return request.post('/api/v1/auth/login', data)
  },

  // 获取当前用户信息
  getCurrentUser(): Promise<User> {
    return request.get('/api/v1/auth/me')
  },

  // 刷新Token
  refreshToken(refreshToken: string): Promise<AuthResponse> {
    return request.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
  },

  // 登出（如果后端有接口）
  logout(): Promise<void> {
    return request.post('/api/v1/auth/logout')
  }
}
