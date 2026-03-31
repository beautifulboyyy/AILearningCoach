import { request } from '@/utils/request'
import type {
  DeepResearchFeedbackRequest,
  DeepResearchProgress,
  DeepResearchTask,
  DeepResearchTaskOperationResponse,
  GenerateAnalystsResponse,
  StartDeepResearchRequest
} from '@/types/deepResearch'

const BASE_URL = '/api/v1/deep-research'

export const deepResearchApi = {
  createTask(data: StartDeepResearchRequest): Promise<DeepResearchTask> {
    return request.post(`${BASE_URL}/tasks`, data)
  },

  listTasks(limit = 50): Promise<DeepResearchTask[]> {
    return request.get(`${BASE_URL}/tasks`, { params: { limit } })
  },

  getTask(threadId: string): Promise<DeepResearchTask> {
    return request.get(`${BASE_URL}/tasks/${threadId}`)
  },

  getProgress(threadId: string): Promise<DeepResearchProgress> {
    return request.get(`${BASE_URL}/tasks/${threadId}/progress`)
  },

  generateAnalysts(threadId: string): Promise<GenerateAnalystsResponse> {
    return request.post(`${BASE_URL}/tasks/${threadId}/analysts`)
  },

  submitFeedback(
    threadId: string,
    data: DeepResearchFeedbackRequest
  ): Promise<DeepResearchTaskOperationResponse> {
    return request.post(`${BASE_URL}/tasks/${threadId}/feedback`, data)
  },

  deleteTask(threadId: string): Promise<{ status: string }> {
    return request.delete(`${BASE_URL}/tasks/${threadId}`)
  }
}
