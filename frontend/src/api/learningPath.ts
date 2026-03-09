import { request } from '@/utils/request'
import type { LearningPath, GeneratePathRequest, UpdatePathRequest } from '@/types/learning'

// 学习路径相关API
export const learningPathApi = {
  // 生成学习路径
  generatePath(data: GeneratePathRequest): Promise<LearningPath> {
    return request.post('/api/v1/learning-path/generate', data, {
      timeout: 90000 // 90秒超时
    })
  },

  // 获取当前活跃的学习路径
  getActivePath(): Promise<LearningPath> {
    return request.get('/api/v1/learning-path/active')
  },

  // 获取指定学习路径
  getPath(id: string | number): Promise<LearningPath> {
    return request.get(`/api/v1/learning-path/${id}`)
  },

  // 更新学习路径
  updatePath(id: string | number, data: UpdatePathRequest): Promise<LearningPath> {
    return request.put(`/api/v1/learning-path/${id}`, data)
  },

  // 获取所有学习路径列表（如果后端有接口）
  getPathList(): Promise<{ paths: LearningPath[] }> {
    return request.get('/api/v1/learning-path/')
  }
}
