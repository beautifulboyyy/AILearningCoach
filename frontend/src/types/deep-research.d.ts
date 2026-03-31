export type DeepResearchStatus =
  | 'pending'
  | 'awaiting_feedback'
  | 'running'
  | 'completed'
  | 'failed'

export type DeepResearchAction = 'approve' | 'regenerate'

export type DeepResearchStage =
  | 'idle'
  | 'creating_analysts'
  | 'awaiting_feedback'
  | 'running'
  | 'searching'
  | 'interviewing'
  | 'writing_sections'
  | 'writing_report'
  | 'finalizing_report'

export interface DeepResearchAnalyst {
  name: string
  affiliation: string
  role: string
  description: string
}

export interface DeepResearchTask {
  id: string
  thread_id: string
  topic: string
  status: DeepResearchStatus
  max_analysts: number
  max_turns: number
  analysts?: DeepResearchAnalyst[] | null
  final_report?: string | null
  created_at: string
  updated_at: string
}

export interface DeepResearchProgress {
  thread_id: string
  stage: DeepResearchStage | string
  message: string
  updated_at: string
}

export interface StartDeepResearchRequest {
  topic: string
  max_analysts: number
  analyst_directions?: string[]
}

export interface GenerateAnalystsResponse {
  status: string
  thread_id: string
  analysts: DeepResearchAnalyst[]
  interrupt_required: boolean
}

export interface DeepResearchFeedbackRequest {
  action: DeepResearchAction
  feedback?: string
}

export interface DeepResearchTaskOperationResponse {
  status: string
  thread_id: string
  message: string
  analysts?: DeepResearchAnalyst[] | null
  final_report: string
  sections_count: number
  error: string
}
