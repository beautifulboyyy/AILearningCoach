import { request } from '@/utils/request'
import type { Agent, IntentResponse } from '@/types/chat'

// Agent相关API
export const agentsApi = {
  // 获取Agent列表
  getAgentList(): Promise<{ agents: Agent[] }> {
    return request.get('/api/v1/agents/list')
  },

  // 测试意图识别
  testIntent(message: string): Promise<IntentResponse> {
    return request.post('/api/v1/agents/intent', { message })
  }
}
