// 任务相关类型定义
import type { Priority, TaskStatus } from './common'

export interface Task {
  id: string | number
  title: string
  description?: string
  status: TaskStatus
  priority: Priority
  due_date?: string
  completed_at?: string
  created_at?: string
  updated_at?: string
  user_id?: string | number
  learning_path_id?: string | number
}

export interface CreateTaskData {
  title: string
  description?: string
  priority?: Priority
  due_date?: string
}

export interface UpdateTaskData {
  title?: string
  description?: string
  status?: TaskStatus
  priority?: Priority
  due_date?: string
}

export interface TaskQueryParams {
  status?: TaskStatus
  priority?: Priority
  skip?: number
  limit?: number
}

export interface TaskListResponse {
  tasks: Task[]
  total?: number
}
