import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi, agentsApi } from '@/api'
import type { Message, ChatSession, Agent } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const messages = ref<Message[]>([])
  const currentSessionId = ref<string | null>(null)
  const sessions = ref<ChatSession[]>([])
  const agents = ref<Agent[]>([])
  const loading = ref(false)
  const sending = ref(false)

  // 发送消息（流式）
  const sendMessage = async (content: string) => {
    if (!content.trim()) return
    
    // 添加用户消息到列表
    const userMessage: Message = {
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    }
    messages.value.push(userMessage)
    
    // 创建AI消息占位符（必须先添加到数组，然后再修改引用）
    const aiMessageIndex = messages.value.length
    messages.value.push({
      role: 'assistant',
      content: '正在思考...',  // 初始状态
      timestamp: new Date().toISOString()
    })
    
    sending.value = true
    let fullContent = ''
    let hasStartedResponse = false
    
    try {
      await chatApi.sendMessageStream(
        {
          message: content,
          session_id: currentSessionId.value || undefined
        },
        // onMessage
        (chunk) => {
          // 处理session_id
          if (chunk.session_id && !currentSessionId.value) {
            currentSessionId.value = chunk.session_id
            messages.value[aiMessageIndex].session_id = chunk.session_id
          }
          
          // 处理状态
          if (chunk.type === 'status') {
            if (chunk.status === 'processing') {
              messages.value[aiMessageIndex].content = '🤔 正在分析您的问题...'
            }
          }
          
          // 处理Agent信息
          if (chunk.type === 'agent') {
            messages.value[aiMessageIndex].agent = chunk.agent
            messages.value[aiMessageIndex].content = `🤖 ${chunk.agent} 为您服务...`
            console.log(`🤖 使用Agent: ${chunk.agent}, 意图: ${chunk.intent}`)
          }
          
          // 处理答案内容
          if (chunk.type === 'answer') {
            if (chunk.content) {
              if (!hasStartedResponse) {
                // 第一次收到内容，清空占位文本
                fullContent = chunk.content
                hasStartedResponse = true
              } else {
                fullContent += chunk.content
              }
              console.log('📝 流式更新:', fullContent.length, '字符')
              // 直接修改属性
              messages.value[aiMessageIndex].content = fullContent
              // 强制触发响应式更新
              messages.value = [...messages.value]
            }
            
            // 处理完成标记
            if (chunk.done) {
              if (chunk.sources && chunk.sources.length > 0) {
                messages.value[aiMessageIndex].sources = chunk.sources
              }
              if (chunk.confidence !== undefined) {
                messages.value[aiMessageIndex].confidence = chunk.confidence
              }
            }
          }
          
          // 处理错误
          if (chunk.type === 'error') {
            console.error('流式对话错误:', chunk.error)
            messages.value[aiMessageIndex].content = '抱歉，处理您的请求时遇到了问题。'
          }
          
          // 兼容旧格式
          if (chunk.message) {
            fullContent = chunk.message
            messages.value[aiMessageIndex].content = fullContent
          }
        },
        // onError
        (error) => {
          console.error('流式消息发送失败:', error)
          // 移除占位消息
          messages.value.pop()
          messages.value.pop()
          throw error
        },
        // onComplete
        () => {
          sending.value = false
        }
      )
    } catch (error) {
      sending.value = false
      throw error
    }
  }

  // 获取会话列表
  const fetchSessions = async () => {
    try {
      const res = await chatApi.getSessions()
      sessions.value = res.sessions || []
      return res
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
      sessions.value = []
    }
  }

  // 加载历史消息
  const loadHistory = async (sessionId: string) => {
    loading.value = true
    try {
      const res = await chatApi.getHistory(sessionId)
      messages.value = (res.messages || []).map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.created_at || new Date().toISOString(),
        session_id: sessionId
      }))
      currentSessionId.value = sessionId
    } finally {
      loading.value = false
    }
  }

  // 创建新会话
  const createNewSession = () => {
    messages.value = []
    currentSessionId.value = null
  }

  // 删除会话
  const deleteSession = async (sessionId: string) => {
    await chatApi.deleteSession(sessionId)
    sessions.value = sessions.value.filter(session => session.id !== sessionId)

    // 如果删除的是当前会话，清空当前聊天窗口
    if (currentSessionId.value === sessionId) {
      createNewSession()
    }
  }

  // 获取Agent列表
  const fetchAgents = async () => {
    try {
      const res = await agentsApi.getAgentList()
      agents.value = res.agents || []
    } catch (error) {
      console.error('Failed to fetch agents:', error)
    }
  }

  // 清空消息
  const clearMessages = () => {
    messages.value = []
  }

  return {
    messages,
    currentSessionId,
    sessions,
    agents,
    loading,
    sending,
    sendMessage,
    loadHistory,
    createNewSession,
    fetchAgents,
    fetchSessions,
    deleteSession,
    clearMessages
  }
})
