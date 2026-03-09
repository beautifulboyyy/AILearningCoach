import { request } from '@/utils/request'
import type { ChatRequest, ChatResponse, Message } from '@/types/chat'
import { getToken } from '@/utils/storage'

// 对话相关API
export const chatApi = {
  // 发送消息（流式SSE）
  async sendMessageStream(
    data: ChatRequest,
    onMessage: (chunk: any) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void
  ): Promise<void> {
    // 使用 ?? 而不是 ||，确保空字符串时使用相对路径（通过nginx代理）
    const baseURL = import.meta.env.VITE_API_BASE_URL ?? ''
    const token = getToken()

    try {
      const response = await fetch(`${baseURL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法获取响应流')
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              onMessage(data)
            } catch (e) {
              console.error('解析SSE数据失败:', e)
            }
          }
        }
      }

      onComplete?.()
    } catch (error) {
      onError?.(error as Error)
      throw error
    }
  },

  // 发送消息（非流式，保留兼容）
  sendMessage(data: ChatRequest): Promise<ChatResponse> {
    return request.post('/api/v1/chat/', data)
  },

  // 获取对话历史
  getHistory(sessionId: string): Promise<{ messages: Message[], session_id: string, created_at?: string, message_count?: number }> {
    return request.get(`/api/v1/chat/history/${sessionId}`)
  },

  // 获取会话列表
  getSessions(): Promise<{ sessions: any[], total: number }> {
    return request.get('/api/v1/chat/sessions')
  },

  // 删除会话
  deleteSession(sessionId: string): Promise<void> {
    return request.delete(`/api/v1/chat/sessions/${sessionId}`)
  }
}
