import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { deepResearchApi } from '@/api'
import type {
  DeepResearchProgress,
  DeepResearchTask,
  StartDeepResearchRequest
} from '@/types/deepResearch'

const DEFAULT_PROGRESS: DeepResearchProgress = {
  thread_id: '',
  stage: 'idle',
  message: '等待开始研究',
  updated_at: ''
}

export const useDeepResearchStore = defineStore('deepResearch', () => {
  const tasks = ref<DeepResearchTask[]>([])
  const selectedTaskId = ref<string>('')
  const currentTask = ref<DeepResearchTask | null>(null)
  const progress = ref<DeepResearchProgress>({ ...DEFAULT_PROGRESS })

  const listLoading = ref(false)
  const detailLoading = ref(false)
  const progressLoading = ref(false)
  const createLoading = ref(false)
  const actionLoading = ref(false)
  const pollingTimer = ref<number | null>(null)

  const selectedTask = computed(() => {
    return tasks.value.find((task) => task.thread_id === selectedTaskId.value) || currentTask.value
  })

  const sortedTasks = computed(() => {
    return [...tasks.value].sort((a, b) => {
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })
  })

  const setCurrentTask = (task: DeepResearchTask | null) => {
    currentTask.value = task
    selectedTaskId.value = task?.thread_id || ''
  }

  const upsertTask = (task: DeepResearchTask) => {
    const index = tasks.value.findIndex((item) => item.thread_id === task.thread_id)
    if (index === -1) {
      tasks.value.unshift(task)
      return
    }
    tasks.value[index] = task
  }

  const fetchTasks = async (limit = 50) => {
    listLoading.value = true
    try {
      const data = await deepResearchApi.listTasks(limit)
      tasks.value = data
      if (!selectedTaskId.value && data.length > 0) {
        setCurrentTask(data[0])
      } else if (selectedTaskId.value) {
        const task = data.find((item) => item.thread_id === selectedTaskId.value) || null
        setCurrentTask(task)
      }
      return data
    } finally {
      listLoading.value = false
    }
  }

  const fetchTaskDetail = async (threadId = selectedTaskId.value) => {
    if (!threadId) return null
    detailLoading.value = true
    try {
      const task = await deepResearchApi.getTask(threadId)
      upsertTask(task)
      if (selectedTaskId.value === threadId) {
        setCurrentTask(task)
      }
      return task
    } finally {
      detailLoading.value = false
    }
  }

  const fetchProgress = async (threadId = selectedTaskId.value) => {
    if (!threadId) return progress.value
    progressLoading.value = true
    try {
      const data = await deepResearchApi.getProgress(threadId)
      progress.value = data
      return data
    } finally {
      progressLoading.value = false
    }
  }

  const selectTask = async (threadId: string) => {
    stopPolling()
    selectedTaskId.value = threadId
    const localTask = tasks.value.find((task) => task.thread_id === threadId) || null
    setCurrentTask(localTask)
    await Promise.all([fetchTaskDetail(threadId), fetchProgress(threadId)])
    maybeStartPolling()
  }

  const createTask = async (payload: StartDeepResearchRequest) => {
    createLoading.value = true
    try {
      const task = await deepResearchApi.createTask(payload)
      upsertTask(task)
      setCurrentTask(task)
      progress.value = {
        thread_id: task.thread_id,
        stage: 'idle',
        message: '任务已创建，等待生成分析师',
        updated_at: new Date().toISOString()
      }
      return task
    } finally {
      createLoading.value = false
    }
  }

  const deleteTask = async (threadId: string) => {
    actionLoading.value = true
    try {
      await deepResearchApi.deleteTask(threadId)
      tasks.value = tasks.value.filter((task) => task.thread_id !== threadId)
      if (selectedTaskId.value === threadId) {
        setCurrentTask(tasks.value[0] || null)
        progress.value = {
          ...DEFAULT_PROGRESS,
          thread_id: currentTask.value?.thread_id || ''
        }
      }
    } finally {
      actionLoading.value = false
    }
  }

  const generateAnalysts = async (threadId = selectedTaskId.value) => {
    if (!threadId) return null
    actionLoading.value = true
    progress.value = {
      thread_id: threadId,
      stage: 'creating_analysts',
      message: '正在生成分析师',
      updated_at: new Date().toISOString()
    }
    try {
      const response = await deepResearchApi.generateAnalysts(threadId)
      await Promise.all([fetchTaskDetail(threadId), fetchProgress(threadId), fetchTasks()])
      return response
    } finally {
      actionLoading.value = false
    }
  }

  const approveTask = async (threadId = selectedTaskId.value) => {
    if (!threadId) return null
    actionLoading.value = true
    progress.value = {
      thread_id: threadId,
      stage: 'running',
      message: '正在开始研究',
      updated_at: new Date().toISOString()
    }

    if (selectedTask.value) {
      const optimisticTask = {
        ...selectedTask.value,
        status: 'running' as const,
        updated_at: new Date().toISOString()
      }
      upsertTask(optimisticTask)
      setCurrentTask(optimisticTask)
    }

    startPolling(threadId)

    try {
      const response = await deepResearchApi.submitFeedback(threadId, { action: 'approve' })
      await Promise.all([fetchTaskDetail(threadId), fetchProgress(threadId), fetchTasks()])
      return response
    } finally {
      actionLoading.value = false
      maybeStartPolling()
    }
  }

  const regenerateAnalysts = async (feedback: string, threadId = selectedTaskId.value) => {
    if (!threadId) return null
    actionLoading.value = true
    progress.value = {
      thread_id: threadId,
      stage: 'creating_analysts',
      message: '正在根据反馈重新生成分析师',
      updated_at: new Date().toISOString()
    }
    try {
      const response = await deepResearchApi.submitFeedback(threadId, {
        action: 'regenerate',
        feedback
      })
      await Promise.all([fetchTaskDetail(threadId), fetchProgress(threadId), fetchTasks()])
      return response
    } finally {
      actionLoading.value = false
    }
  }

  const pollCurrentTask = async (threadId = selectedTaskId.value) => {
    if (!threadId) return
    await Promise.allSettled([fetchTaskDetail(threadId), fetchProgress(threadId), fetchTasks()])
    const task = tasks.value.find((item) => item.thread_id === threadId) || currentTask.value
    if (!task || ['completed', 'failed'].includes(task.status)) {
      stopPolling()
    }
  }

  const startPolling = (threadId = selectedTaskId.value) => {
    if (!threadId) return
    stopPolling()
    pollingTimer.value = window.setInterval(() => {
      void pollCurrentTask(threadId)
    }, 2500)
  }

  const stopPolling = () => {
    if (pollingTimer.value) {
      window.clearInterval(pollingTimer.value)
      pollingTimer.value = null
    }
  }

  const maybeStartPolling = () => {
    const task = selectedTask.value
    if (task?.status === 'running') {
      startPolling(task.thread_id)
      return
    }
    stopPolling()
  }

  const initialize = async () => {
    await fetchTasks()
    if (selectedTaskId.value) {
      await Promise.all([fetchTaskDetail(selectedTaskId.value), fetchProgress(selectedTaskId.value)])
      maybeStartPolling()
    }
  }

  return {
    tasks,
    selectedTaskId,
    currentTask,
    progress,
    listLoading,
    detailLoading,
    progressLoading,
    createLoading,
    actionLoading,
    selectedTask,
    sortedTasks,
    fetchTasks,
    fetchTaskDetail,
    fetchProgress,
    selectTask,
    createTask,
    deleteTask,
    generateAnalysts,
    approveTask,
    regenerateAnalysts,
    startPolling,
    stopPolling,
    initialize
  }
})
