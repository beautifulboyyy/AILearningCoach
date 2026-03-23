import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { deepResearchApi } from '@/api'
import type {
  CreateDeepResearchTaskData,
  DeepResearchReportResponse,
  DeepResearchTaskDetail,
  DeepResearchTaskSummary,
  StartDeepResearchData,
  SubmitDeepResearchFeedbackData
} from '@/types/deepresearch'

const ACTIVE_STATUSES = new Set(['drafting_analysts', 'running_research'])

export const useDeepResearchStore = defineStore('deepresearch', () => {
  const tasks = ref<DeepResearchTaskSummary[]>([])
  const currentTask = ref<DeepResearchTaskDetail | null>(null)
  const currentReport = ref<DeepResearchReportResponse | null>(null)
  const loading = ref(false)
  const actionLoading = ref(false)
  const polling = ref(false)

  let pollTimer: number | null = null

  const sortedTasks = computed(() =>
    [...tasks.value].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
  )

  const activeTask = computed(() => sortedTasks.value.find((task) => ACTIVE_STATUSES.has(task.status)))

  const fetchTasks = async () => {
    loading.value = true
    try {
      const res = await deepResearchApi.getTasks()
      tasks.value = res.tasks || []
      return res
    } finally {
      loading.value = false
    }
  }

  const fetchTaskDetail = async (taskId: number) => {
    const detail = await deepResearchApi.getTask(taskId)
    currentTask.value = detail

    const index = tasks.value.findIndex((item) => item.id === detail.id)
    if (index >= 0) {
      tasks.value[index] = detail
    } else {
      tasks.value.unshift(detail)
    }

    if (currentReport.value?.task_id !== taskId) {
      currentReport.value = null
    }

    return detail
  }

  const createTask = async (data: CreateDeepResearchTaskData) => {
    actionLoading.value = true
    try {
      const created = await deepResearchApi.createTask(data)
      tasks.value.unshift(created)
      await fetchTaskDetail(created.id)
      return created
    } finally {
      actionLoading.value = false
    }
  }

  const submitFeedback = async (taskId: number, data: SubmitDeepResearchFeedbackData) => {
    actionLoading.value = true
    try {
      const updated = await deepResearchApi.submitFeedback(taskId, data)
      await fetchTaskDetail(updated.id)
      return updated
    } finally {
      actionLoading.value = false
    }
  }

  const startResearch = async (taskId: number, data: StartDeepResearchData) => {
    actionLoading.value = true
    try {
      const updated = await deepResearchApi.startResearch(taskId, data)
      await fetchTaskDetail(updated.id)
      return updated
    } finally {
      actionLoading.value = false
    }
  }

  const loadReport = async (taskId: number) => {
    actionLoading.value = true
    try {
      const report = await deepResearchApi.getReport(taskId)
      currentReport.value = report
      return report
    } finally {
      actionLoading.value = false
    }
  }

  const deleteTask = async (taskId: number) => {
    actionLoading.value = true
    try {
      await deepResearchApi.deleteTask(taskId)
      tasks.value = tasks.value.filter((task) => task.id !== taskId)
      if (currentTask.value?.id === taskId) {
        currentTask.value = null
        currentReport.value = null
      }
    } finally {
      actionLoading.value = false
    }
  }

  const stopPolling = () => {
    polling.value = false
    if (pollTimer !== null) {
      window.clearTimeout(pollTimer)
      pollTimer = null
    }
  }

  const startPolling = (taskId: number, interval = 4000) => {
    stopPolling()
    polling.value = true

    const tick = async () => {
      try {
        const detail = await fetchTaskDetail(taskId)
        if (detail && ACTIVE_STATUSES.has(detail.status)) {
          pollTimer = window.setTimeout(tick, interval)
        } else {
          stopPolling()
        }
      } catch {
        pollTimer = window.setTimeout(tick, interval)
      }
    }

    pollTimer = window.setTimeout(tick, interval)
  }

  return {
    tasks,
    currentTask,
    currentReport,
    loading,
    actionLoading,
    polling,
    sortedTasks,
    activeTask,
    fetchTasks,
    fetchTaskDetail,
    createTask,
    submitFeedback,
    startResearch,
    loadReport,
    deleteTask,
    startPolling,
    stopPolling
  }
})
