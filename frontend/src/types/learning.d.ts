// 学习路径相关类型定义
import type { LearningGoal } from './common'

export interface Module {
  name: string
  description?: string
  duration_hours?: number
  tasks?: number
  progress?: number
  status?: 'not_started' | 'in_progress' | 'completed'
}

export interface Phase {
  phase?: number  // 后端返回的阶段编号
  weeks?: string  // 周数范围，如 "1-2"
  title?: string  // 后端返回的标题字段
  name?: string   // 兼容字段
  description?: string
  modules: Module[] | string[]  // 可以是对象数组或字符串数组
  goal?: string   // 后端返回的目标字段
  duration_hours?: number
  progress?: number
  status?: 'not_started' | 'in_progress' | 'completed'
}

export interface LearningPath {
  id: string | number
  user_id?: string | number
  title?: string  // 后端返回的标题
  description?: string  // 后端返回的描述
  learning_goal?: LearningGoal
  status: 'active' | 'completed' | 'archived'
  phases: Phase[]
  total_duration_hours?: number
  progress_percentage?: number
  created_at?: string
  updated_at?: string
}

export interface GeneratePathRequest {
  learning_goal: LearningGoal
  available_hours_per_week?: number
  current_level?: string
  specific_topics?: string[]
}

export interface UpdatePathRequest {
  status?: 'active' | 'completed' | 'archived'
  progress_percentage?: number
}
