// 对话相关类型定义

export interface Message {
  id?: string | number
  role: 'user' | 'assistant'
  content: string
  agent?: string
  timestamp?: string
  session_id?: string
}

export interface ChatSession {
  id: string
  title?: string
  created_at: string
  updated_at?: string
  message_count?: number
}

export interface ChatRequest {
  message: string
  session_id?: string
}

export interface ChatResponse {
  response: string
  session_id: string
  conversation_id?: string
  agent?: string
  extra_data?: {
    agent?: string
    intent?: string
    confidence?: number
  }
}

export interface Agent {
  name: string
  description: string
  capabilities: string[]
  icon?: string
}

export interface IntentResponse {
  agent: string
  confidence: number
  reasoning?: string
}
