<template>
  <div class="chat-container">
    <el-row :gutter="24" class="chat-row">
      <!-- 会话列表 -->
      <el-col :xs="24" :sm="8" :lg="6">
        <el-card class="session-card">
          <template #header>
            <div class="card-header">
              <span>对话历史</span>
              <el-button
                type="primary"
                size="small"
                :icon="Plus"
                @click="createNew"
              >
                新对话
              </el-button>
            </div>
          </template>
          <div class="session-list">
            <div
              v-for="session in sessions"
              :key="session.id"
              class="session-item"
              :class="{ active: currentSessionId === session.id }"
              @click="selectSession(session.id)"
            >
              <div class="session-title">{{ session.title || '新对话' }}</div>
              <div class="session-time">{{ formatRelativeTime(session.created_at) }}</div>
            </div>
            <div v-if="sessions.length === 0" class="empty-sessions">
              暂无历史对话
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 聊天区域 -->
      <el-col :xs="24" :sm="16" :lg="18">
        <el-card class="chat-card">
          <template #header>
            <div class="chat-header">
              <div class="agent-info">
                <el-icon :size="24" color="#409EFF">
                  <ChatDotRound />
                </el-icon>
                <span>AI学习助手</span>
              </div>
              <div class="agent-badges">
                <el-tag
                  v-for="agent in agents"
                  :key="agent.name"
                  size="small"
                  class="agent-tag"
                >
                  {{ agent.name }}
                </el-tag>
              </div>
            </div>
          </template>

          <div class="chat-body">
            <div ref="messagesRef" class="messages-container">
              <div
                v-for="(message, index) in messages"
                :key="index"
                class="message-wrapper"
                :class="message.role"
              >
                <div v-if="message.role === 'assistant'" class="message-avatar">
                  <el-avatar :size="32" :style="{ background: getAgentColor(message.agent) }">
                    <el-icon><Service /></el-icon>
                  </el-avatar>
                </div>
                
                <div class="message-content">
                  <div v-if="message.agent" class="agent-label">
                    {{ message.agent }}
                  </div>
                  <div class="message-bubble" :class="message.role">
                    <div class="message-text">{{ message.content }}</div>
                    <div class="message-time">{{ formatTime(message.timestamp) }}</div>
                  </div>
                </div>
                
                <div v-if="message.role === 'user'" class="message-avatar">
                  <el-avatar :size="32" :icon="UserFilled" />
                </div>
              </div>

              <!-- 流式消息已经在messages数组中，不需要额外的loading动画 -->

              <div v-if="messages.length === 0 && !sending" class="welcome-message">
                <el-icon :size="80" color="#409EFF">
                  <ChatLineRound />
                </el-icon>
                <h3>欢迎使用AI学习助手</h3>
                <p>我可以帮您解答问题、规划学习路径、分析进度等</p>
                <div class="quick-questions">
                  <el-tag
                    v-for="(q, index) in quickQuestions"
                    :key="index"
                    class="quick-question"
                    @click="sendQuickQuestion(q)"
                  >
                    {{ q }}
                  </el-tag>
                </div>
              </div>
            </div>

            <div class="input-container">
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="3"
                placeholder="输入您的问题..."
                :disabled="sending"
                @keydown.enter.exact.prevent="handleSend"
              />
              <el-button
                type="primary"
                :icon="Promotion"
                :loading="sending"
                :disabled="!inputMessage.trim()"
                @click="handleSend"
              >
                发送
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus, ChatDotRound, Service, UserFilled, Promotion, ChatLineRound
} from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { formatTime, formatRelativeTime } from '@/utils/format'
import { AGENT_COLORS } from '@/utils/constants'
import type { ChatSession } from '@/types/chat'

const chatStore = useChatStore()

const messagesRef = ref<HTMLElement>()
const inputMessage = ref('')
const sessions = ref<ChatSession[]>([])

const messages = computed(() => chatStore.messages)
const currentSessionId = computed(() => chatStore.currentSessionId)
const agents = computed(() => chatStore.agents)
const sending = computed(() => chatStore.sending)

const quickQuestions = [
  '什么是RAG？',
  '帮我规划学习路径',
  '我的学习进度如何？',
  '推荐一些学习资源'
]

const getAgentColor = (agent?: string) => {
  return AGENT_COLORS[agent as keyof typeof AGENT_COLORS] || '#409EFF'
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 监听消息变化，自动滚动（使用 flush: 'post' 确保 DOM 更新后执行）
watch(() => chatStore.messages, () => {
  scrollToBottom()
}, { deep: true, flush: 'post' })

// 额外监听消息长度变化
watch(() => chatStore.messages.length, () => {
  scrollToBottom()
})

const createNew = () => {
  chatStore.createNewSession()
  inputMessage.value = ''
}

const selectSession = async (sessionId: string) => {
  try {
    await chatStore.loadHistory(sessionId)
    scrollToBottom()
  } catch (error) {
    ElMessage.error('加载历史失败')
  }
}

const handleSend = async () => {
  const message = inputMessage.value.trim()
  if (!message) return

  inputMessage.value = ''
  scrollToBottom()

  try {
    await chatStore.sendMessage(message)
    scrollToBottom()
  } catch (error: any) {
    ElMessage.error(error.message || '发送失败')
  }
}

const sendQuickQuestion = (question: string) => {
  inputMessage.value = question
  handleSend()
}

// 监听消息变化，自动滚动
watch(() => chatStore.messages.length, () => {
  scrollToBottom()
})

onMounted(async () => {
  // 获取Agent列表
  await chatStore.fetchAgents()
  
  // 获取会话列表
  await chatStore.fetchSessions()
  sessions.value = chatStore.sessions
})
</script>

<style scoped lang="scss">
.chat-container {
  height: calc(100vh - 108px);
  
  .chat-row {
    height: 100%;
  }
}

.session-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  :deep(.el-card__body) {
    flex: 1;
    overflow: hidden;
    padding: 0;
  }
  
  .session-list {
    height: 100%;
    overflow-y: auto;
    padding: 12px;
    
    .session-item {
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 8px;
      cursor: pointer;
      transition: all 0.3s;
      border: 1px solid transparent;
      
      &:hover {
        background: #F5F7FA;
      }
      
      &.active {
        background: #ECF5FF;
        border-color: #409EFF;
      }
      
      .session-title {
        font-size: 14px;
        color: #303133;
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .session-time {
        font-size: 12px;
        color: #909399;
      }
    }
    
    .empty-sessions {
      text-align: center;
      padding: 40px 20px;
      color: #909399;
    }
  }
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  :deep(.el-card__body) {
    flex: 1;
    overflow: hidden;
    padding: 0;
  }
  
  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .agent-info {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 16px;
      font-weight: 500;
    }
    
    .agent-badges {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
  }
  
  .chat-body {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 20px;
  }
  
  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 20px 0;
    
    .message-wrapper {
      display: flex;
      margin-bottom: 24px;
      gap: 12px;
      
      &.user {
        flex-direction: row-reverse;
      }
      
      .message-avatar {
        flex-shrink: 0;
      }
      
      .message-content {
        max-width: 70%;
        
        .agent-label {
          font-size: 12px;
          color: #909399;
          margin-bottom: 4px;
        }
        
        .message-bubble {
          padding: 12px 16px;
          border-radius: 12px;
          
          &.user {
            background: #409EFF;
            color: white;
            border-bottom-right-radius: 4px;
          }
          
          &.assistant {
            background: #F5F7FA;
            color: #303133;
            border-bottom-left-radius: 4px;
          }
          
          .message-text {
            font-size: 14px;
            line-height: 1.6;
            word-break: break-word;
            white-space: pre-wrap;
          }
          
          .message-time {
            font-size: 12px;
            opacity: 0.7;
            margin-top: 8px;
          }
        }
      }
    }
    
    .welcome-message {
      text-align: center;
      padding: 60px 20px;
      
      h3 {
        margin: 20px 0 10px;
        font-size: 24px;
        color: #303133;
      }
      
      p {
        color: #909399;
        margin-bottom: 30px;
      }
      
      .quick-questions {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 12px;
        
        .quick-question {
          cursor: pointer;
          
          &:hover {
            opacity: 0.8;
          }
        }
      }
    }
  }
  
  .input-container {
    display: flex;
    gap: 12px;
    padding-top: 20px;
    border-top: 1px solid #EBEEF5;
    
    :deep(.el-textarea) {
      flex: 1;
      
      .el-textarea__inner {
        resize: none;
      }
    }
    
    .el-button {
      align-self: flex-end;
    }
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
  
  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #909399;
    animation: typing 1.4s infinite;
    
    &:nth-child(1) {
      animation-delay: 0s;
    }
    
    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

@media (max-width: 768px) {
  .session-card {
    display: none;
  }
}
</style>
