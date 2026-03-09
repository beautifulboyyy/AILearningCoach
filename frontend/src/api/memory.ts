import { request } from '@/utils/request'

// 记忆系统相关API
export const memoryApi = {
  // 获取记忆列表
  getMemories(params?: any): Promise<{ memories: any[] }> {
    return request.get('/api/v1/memories/', { params })
  },

  // 获取单个记忆
  getMemory(id: string | number): Promise<any> {
    return request.get(`/api/v1/memories/${id}`)
  },

  // 搜索记忆
  searchMemories(query: string, limit = 5): Promise<{ memories: any[] }> {
    return request.post('/api/v1/memories/search', { query, limit })
  },

  // 导出记忆
  exportMemories(format: 'json' | 'markdown' = 'json'): Promise<any> {
    return request.post('/api/v1/memories/export', { format })
  }
}
