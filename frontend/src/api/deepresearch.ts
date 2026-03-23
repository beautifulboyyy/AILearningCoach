import { request } from '@/utils/request'
import type {
  CreateDeepResearchTaskData,
  DeepResearchReportResponse,
  DeepResearchTaskDetail,
  DeepResearchTaskListResponse,
  DeepResearchTaskSummary,
  StartDeepResearchData,
  SubmitDeepResearchFeedbackData
} from '@/types/deepresearch'

export const deepResearchApi = {
  getTasks(): Promise<DeepResearchTaskListResponse> {
    return request.get('/api/v1/deepresearch/tasks')
  },

  createTask(data: CreateDeepResearchTaskData): Promise<DeepResearchTaskSummary> {
    return request.post('/api/v1/deepresearch/tasks', data)
  },

  getTask(id: number | string): Promise<DeepResearchTaskDetail> {
    return request.get(`/api/v1/deepresearch/tasks/${id}`)
  },

  submitFeedback(id: number | string, data: SubmitDeepResearchFeedbackData): Promise<DeepResearchTaskSummary> {
    return request.post(`/api/v1/deepresearch/tasks/${id}/feedback`, data)
  },

  startResearch(id: number | string, data: StartDeepResearchData): Promise<DeepResearchTaskSummary> {
    return request.post(`/api/v1/deepresearch/tasks/${id}/start`, data)
  },

  getReport(id: number | string): Promise<DeepResearchReportResponse> {
    return request.get(`/api/v1/deepresearch/tasks/${id}/report`)
  },

  deleteTask(id: number | string): Promise<void> {
    return request.delete(`/api/v1/deepresearch/tasks/${id}`)
  }
}
