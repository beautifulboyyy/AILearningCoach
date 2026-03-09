import { request } from '@/utils/request'
import type { UserProfile } from '@/types/user'

// 用户画像相关API
export const profileApi = {
  // 获取用户画像
  getProfile(): Promise<UserProfile> {
    return request.get('/api/v1/profile/')
  },

  // 更新用户画像
  updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    return request.put('/api/v1/profile/', data)
  },

  // 从对话生成画像
  generateProfile(data?: any): Promise<UserProfile> {
    return request.post('/api/v1/profile/generate', data || {})
  }
}
