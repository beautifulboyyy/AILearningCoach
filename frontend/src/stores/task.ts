import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { taskApi } from '@/api'
import type { Task, CreateTaskData, UpdateTaskData, TaskStatus } from '@/types/task'

export const useTaskStore = defineStore('task', () => {
  // 状态
  const tasks = ref<Task[]>([])
  const loading = ref(false)
  const currentTask = ref<Task | null>(null)

  // 计算属性 - 按状态分组
  const pendingTasks = computed(() => 
    tasks.value.filter(t => t.status === 'todo')
  )
  
  const inProgressTasks = computed(() => 
    tasks.value.filter(t => t.status === 'in_progress')
  )
  
  const completedTasks = computed(() => 
    tasks.value.filter(t => t.status === 'completed')
  )

  // 获取任务列表
  const fetchTasks = async (params?: any) => {
    loading.value = true
    try {
      const res = await taskApi.getTasks(params)
      tasks.value = res.tasks || []
      return res
    } finally {
      loading.value = false
    }
  }

  // 创建任务
  const createTask = async (data: CreateTaskData) => {
    const task = await taskApi.createTask(data)
    tasks.value.unshift(task)
    return task
  }

  // 更新任务
  const updateTask = async (id: string | number, data: UpdateTaskData) => {
    const updatedTask = await taskApi.updateTask(id, data)
    const index = tasks.value.findIndex(t => t.id === id)
    if (index !== -1) {
      tasks.value[index] = updatedTask
    }
    return updatedTask
  }

  // 删除任务
  const deleteTask = async (id: string | number) => {
    await taskApi.deleteTask(id)
    const index = tasks.value.findIndex(t => t.id === id)
    if (index !== -1) {
      tasks.value.splice(index, 1)
    }
  }

  // 完成任务
  const completeTask = async (id: string | number) => {
    const task = await taskApi.completeTask(id)
    const index = tasks.value.findIndex(t => t.id === id)
    if (index !== -1) {
      tasks.value[index] = task
    }
    return task
  }

  // 更改任务状态
  const changeTaskStatus = async (id: string | number, status: TaskStatus) => {
    return updateTask(id, { status })
  }

  return {
    tasks,
    loading,
    currentTask,
    pendingTasks,
    inProgressTasks,
    completedTasks,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    completeTask,
    changeTaskStatus
  }
})
