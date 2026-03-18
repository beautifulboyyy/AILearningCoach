import { request } from '@/utils/request'
import type {
  ProgressStats,
  UpdateProgressRequest,
  WeeklyReport,
  PathProgressResponse,
  ProgressHistoryResponse,
  RecordActivityRequest,
  RecordActivityResponse,
  SyncModulesResponse
} from '@/types/progress'

// 进度相关API
export const progressApi = {
  // 获取进度统计
  getStats(): Promise<ProgressStats> {
    return request.get('/api/v1/progress/stats')
  },

  // 更新模块进度
  updateModuleProgress(module: string, data: UpdateProgressRequest): Promise<any> {
    return request.put(`/api/v1/progress/module/${module}`, data)
  },

  // 获取周报
  getWeeklyReport(): Promise<WeeklyReport> {
    return request.get('/api/v1/progress/report/weekly')
  },

  // 获取月报（如果后端有接口）
  getMonthlyReport(): Promise<any> {
    return request.get('/api/v1/progress/report/monthly')
  },

  // ============ 新增：路径进度相关API ============

  // 同步学习路径模块到进度表
  syncPathModules(pathId?: number): Promise<SyncModulesResponse> {
    const params = pathId ? { path_id: pathId } : {}
    return request.post('/api/v1/progress/sync', null, { params })
  },

  // 获取学习路径详细进度
  getPathProgress(pathId: number): Promise<PathProgressResponse> {
    return request.get(`/api/v1/progress/path/${pathId}`)
  },

  // 获取进度变更历史
  getProgressHistory(moduleKey?: string, limit: number = 50): Promise<ProgressHistoryResponse> {
    const params: any = { limit }
    if (moduleKey) {
      params.module_key = moduleKey
    }
    return request.get('/api/v1/progress/history', { params })
  },

  // 记录学习活动
  recordActivity(moduleKey: string, data: RecordActivityRequest): Promise<RecordActivityResponse> {
    return request.post(`/api/v1/progress/module/${moduleKey}/activity`, data)
  }
}
