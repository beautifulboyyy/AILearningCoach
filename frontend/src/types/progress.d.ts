// 进度相关类型定义

export type ProgressStatus = 'not_started' | 'in_progress' | 'completed'
export type ProgressTriggerType = 'manual' | 'conversation' | 'task' | 'time' | 'quiz' | 'ai' | 'system'
export type ActivityType = 'study' | 'practice' | 'review'

export interface WeeklyTrend {
  week: string
  completion: number
}

export interface ProgressStats {
  // 模块统计
  total_modules: number
  completed_modules: number
  in_progress_modules: number
  not_started_modules: number
  overall_completion: number
  current_module?: string
  // 学习统计
  total_study_hours: number
  completed_tasks: number
  learning_days: number
  average_daily_hours: number
  week_change_percent: number
  // 图表数据
  daily_hours: Record<string, number>  // {"周一": 2.5, "周二": 3.0, ...}
  weekly_trend: WeeklyTrend[]  // [{week: "W1", completion: 40}, ...]
}

export interface ModuleProgress {
  module: string
  completed: boolean
  progress_percentage: number
  study_hours: number
}

export interface UpdateProgressRequest {
  status?: ProgressStatus
  completion_percentage?: number
  actual_hours?: number
  notes?: string
}

export interface WeeklyReport {
  week_start: string
  week_end: string
  total_hours: number
  completed_tasks: number
  summary: string
  highlights?: string[]
  daily_hours?: Record<string, number> // 每日学习时长，例如 {"2024-01-22": 2.5}
  module_progress?: Record<string, number>
}

export interface StudyRecord {
  date: string
  hours: number
  tasks_completed?: number
  modules?: string[]
}

// ============ 新增：路径进度相关类型 ============

export interface ModuleProgressDetail {
  module_key: string
  module_name: string
  phase_index: number
  phase_title?: string
  completion_percentage: number
  actual_hours: number
  estimated_hours: number
  status: ProgressStatus
  started_at?: string
  completed_at?: string
  last_activity?: string
}

export interface PhaseProgressDetail {
  phase_index: number
  phase_title: string
  weeks: string
  goal: string
  completion_percentage: number
  modules: ModuleProgressDetail[]
  completed_modules: number
  total_modules: number
}

export interface PathProgressResponse {
  path_id: number
  path_title: string
  overall_completion: number
  status: string
  phases: PhaseProgressDetail[]
  total_study_hours: number
  estimated_total_hours: number
  current_module?: ModuleProgressDetail
  next_module?: ModuleProgressDetail
  completed_modules_count: number
  total_modules_count: number
}

// ============ 新增：进度历史相关类型 ============

export interface ProgressHistoryItem {
  id: number
  module_name: string
  module_key?: string
  old_percentage: number
  new_percentage: number
  old_status?: ProgressStatus
  new_status?: ProgressStatus
  trigger_type: ProgressTriggerType
  trigger_source?: string
  created_at: string
}

export interface ProgressHistoryResponse {
  items: ProgressHistoryItem[]
  total: number
}

// ============ 新增：学习活动相关类型 ============

export interface RecordActivityRequest {
  activity_type: ActivityType
  duration_minutes: number
  notes?: string
}

export interface RecordActivityResponse {
  module_key: string
  old_progress: number
  new_progress: number
  progress_change: number
  message: string
}

// ============ 新增：同步相关类型 ============

export interface SyncModulesResponse {
  message: string
  path_id: number
  synced_modules: number
}
