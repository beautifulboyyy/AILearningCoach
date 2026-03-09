// 通用类型定义

export interface ApiResponse<T = any> {
  code?: number
  message?: string
  data?: T
  detail?: string
}

export interface PaginationParams {
  page?: number
  page_size?: number
  skip?: number
  limit?: number
}

export interface PaginationResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export type Priority = 'low' | 'medium' | 'high' | 'urgent'
export type TaskStatus = 'todo' | 'in_progress' | 'completed' | 'cancelled'
export type LearningGoal = 'job_hunting' | 'skill_improvement' | 'hobby_learning' | 'exam_preparation'
export type LearningStyle = 'project_driven' | 'theory_first' | 'practice_first'
