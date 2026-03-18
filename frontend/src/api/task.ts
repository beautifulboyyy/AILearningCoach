import { request } from '@/utils/request'
import type { Task, CreateTaskData, UpdateTaskData, TaskQueryParams, TaskListResponse } from '@/types/task'

// 任务相关API
export const taskApi = {
  // 获取任务列表
  getTasks(params?: TaskQueryParams): Promise<TaskListResponse> {
    const queryParams = { ...(params || {}) } as any
    if (queryParams.status) {
      queryParams.status_filter = queryParams.status
      delete queryParams.status
    }
    if (typeof queryParams.skip === 'number') {
      queryParams.offset = queryParams.skip
      delete queryParams.skip
    }
    return request.get('/api/v1/tasks/', { params: queryParams })
  },

  // 创建任务
  createTask(data: CreateTaskData): Promise<Task> {
    return request.post('/api/v1/tasks/', data)
  },

  // 获取单个任务
  getTask(id: string | number): Promise<Task> {
    return request.get(`/api/v1/tasks/${id}`)
  },

  // 更新任务
  updateTask(id: string | number, data: UpdateTaskData): Promise<Task> {
    return request.put(`/api/v1/tasks/${id}`, data)
  },

  // 删除任务
  deleteTask(id: string | number): Promise<void> {
    return request.delete(`/api/v1/tasks/${id}`)
  },

  // 完成任务
  completeTask(id: string | number): Promise<Task> {
    return request.post(`/api/v1/tasks/${id}/complete`)
  }
}
