import { defineStore } from 'pinia'
import { ref } from 'vue'
import { learningPathApi, progressApi } from '@/api'
import type { LearningPath, GeneratePathRequest } from '@/types/learning'
import type { PathProgressResponse, RecordActivityRequest, UpdateProgressRequest } from '@/types/progress'

export const useLearningStore = defineStore('learning', () => {
  // 状态
  const currentPath = ref<LearningPath | null>(null)
  const paths = ref<LearningPath[]>([])
  const loading = ref(false)
  const generating = ref(false)

  // 进度状态
  const pathProgress = ref<PathProgressResponse | null>(null)
  const progressLoading = ref(false)

  // 生成学习路径
  const generatePath = async (data: GeneratePathRequest) => {
    generating.value = true
    try {
      const path = await learningPathApi.generatePath(data)
      currentPath.value = path
      return path
    } finally {
      generating.value = false
    }
  }

  // 获取当前活跃路径
  const fetchActivePath = async () => {
    loading.value = true
    try {
      const path = await learningPathApi.getActivePath()
      currentPath.value = path
      return path
    } catch (error: any) {
      // 如果没有活跃路径，返回null而不是抛出错误
      if (error.response?.status === 404) {
        currentPath.value = null
        return null
      }
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取指定路径
  const fetchPath = async (id: string | number) => {
    loading.value = true
    try {
      const path = await learningPathApi.getPath(id)
      currentPath.value = path
      return path
    } finally {
      loading.value = false
    }
  }

  // 更新路径
  const updatePath = async (id: string | number, data: any) => {
    const path = await learningPathApi.updatePath(id, data)
    if (currentPath.value?.id === id) {
      currentPath.value = path
    }
    return path
  }

  // 获取路径详细进度
  const fetchPathProgress = async (pathId?: number) => {
    const targetId = pathId || currentPath.value?.id
    if (!targetId) return null

    progressLoading.value = true
    try {
      pathProgress.value = await progressApi.getPathProgress(Number(targetId))
      return pathProgress.value
    } catch (error) {
      console.error('Failed to fetch path progress:', error)
      return null
    } finally {
      progressLoading.value = false
    }
  }

  // 更新模块进度
  const updateModuleProgress = async (moduleKey: string, data: UpdateProgressRequest) => {
    try {
      await progressApi.updateModuleProgress(moduleKey, data)
      // 刷新进度数据
      await fetchPathProgress()
    } catch (error) {
      console.error('Failed to update module progress:', error)
      throw error
    }
  }

  // 记录学习活动
  const recordActivity = async (moduleKey: string, data: RecordActivityRequest) => {
    try {
      const response = await progressApi.recordActivity(moduleKey, data)
      // 刷新进度数据
      await fetchPathProgress()
      return response
    } catch (error) {
      console.error('Failed to record activity:', error)
      throw error
    }
  }

  // 标记模块开始学习
  const startModule = async (moduleKey: string) => {
    return updateModuleProgress(moduleKey, {
      status: 'in_progress'
    })
  }

  // 标记模块完成
  const completeModule = async (moduleKey: string) => {
    return updateModuleProgress(moduleKey, {
      status: 'completed',
      completion_percentage: 100
    })
  }

  return {
    currentPath,
    paths,
    loading,
    generating,
    pathProgress,
    progressLoading,
    generatePath,
    fetchActivePath,
    fetchPath,
    updatePath,
    fetchPathProgress,
    updateModuleProgress,
    recordActivity,
    startModule,
    completeModule
  }
})
