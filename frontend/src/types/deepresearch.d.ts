export type DeepResearchStatus =
  | 'pending'
  | 'drafting_analysts'
  | 'waiting_feedback'
  | 'running_research'
  | 'completed'
  | 'failed'

export type DeepResearchPhase =
  | 'analyst_generation'
  | 'analyst_feedback'
  | 'research_execution'
  | 'report_finalization'
  | null

export interface DeepResearchAnalyst {
  affiliation: string
  name: string
  role: string
  description: string
}

export interface DeepResearchTaskSummary {
  id: number
  user_id: number
  topic: string
  status: DeepResearchStatus
  phase: DeepResearchPhase
  progress_percent: number
  progress_message?: string | null
  current_revision: number
  feedback_round_used: number
  max_feedback_rounds: number
  selected_revision?: number | null
  created_at: string
  updated_at: string
}

export interface DeepResearchTaskDetail extends DeepResearchTaskSummary {
  requirements?: string | null
  remaining_feedback_rounds: number
  analysts: DeepResearchAnalyst[]
  report_available: boolean
  error_message?: string | null
}

export interface DeepResearchTaskListResponse {
  tasks: DeepResearchTaskSummary[]
  total: number
}

export interface DeepResearchReportResponse {
  task_id: number
  topic: string
  report_markdown: string
}

export interface CreateDeepResearchTaskData {
  topic: string
  requirements?: string
  max_analysts?: number
}

export interface SubmitDeepResearchFeedbackData {
  feedback: string
}

export interface StartDeepResearchData {
  selected_revision: number
}
