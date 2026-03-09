<template>
  <div class="learning-path-container">
    <div class="page-header">
      <h2>我的学习路径</h2>
      <el-button
        type="primary"
        :icon="Plus"
        @click="goToGenerate"
      >
        生成新路径
      </el-button>
    </div>

    <div v-if="loading" v-loading="loading" class="loading-container">
      <div style="height: 400px;"></div>
    </div>

    <div v-else-if="!currentPath" class="empty-state">
      <el-empty description="暂无学习路径">
        <el-button type="primary" @click="goToGenerate">
          立即生成
        </el-button>
      </el-empty>
    </div>

    <el-row v-else :gutter="24">
      <!-- 路径时间线 -->
      <el-col :xs="24" :lg="16">
        <el-card>
          <div class="path-timeline">
            <div
              v-for="(phase, phaseIndex) in adaptedPhases"
              :key="phaseIndex"
              class="phase-item"
            >
              <div class="phase-header">
                <div class="phase-number">
                  <el-icon v-if="phase.status === 'completed'" color="#67C23A">
                    <CircleCheck />
                  </el-icon>
                  <span v-else>{{ phase.phase || phaseIndex + 1 }}</span>
                </div>
                <div class="phase-info">
                  <h3>{{ phase.title || phase.name }}</h3>
                  <p v-if="phase.goal">{{ phase.goal }}</p>
                  <p v-else-if="phase.description">{{ phase.description }}</p>
                  <div class="phase-meta">
                    <el-tag :type="getPhaseStatusType(phase.status)" size="small">
                      {{ getPhaseStatusText(phase.status) }}
                    </el-tag>
                    <span v-if="phase.weeks">{{ phase.weeks }}周</span>
                    <span v-else-if="phase.duration_hours">预计 {{ phase.duration_hours }}h</span>
                  </div>
                </div>
                <div class="phase-progress">
                  <el-progress
                    type="circle"
                    :percentage="phase.progress || 0"
                    :width="80"
                  />
                </div>
              </div>

              <div v-if="phase.modules && phase.modules.length > 0" class="modules-list">
                <div
                  v-for="(module, moduleIndex) in adaptModules(phase.modules)"
                  :key="moduleIndex"
                  class="module-item"
                  :class="{ 'module-completed': module.status === 'completed', 'module-in-progress': module.status === 'in_progress' }"
                >
                  <div class="module-header">
                    <el-icon
                      :color="module.status === 'completed' ? '#67C23A' : module.status === 'in_progress' ? '#E6A23C' : '#C0C4CC'"
                    >
                      <CircleCheck />
                    </el-icon>
                    <span class="module-name">{{ module.name }}</span>
                    <el-tag v-if="module.status === 'in_progress'" type="warning" size="small">学习中</el-tag>
                    <el-tag v-else-if="module.status === 'completed'" type="success" size="small">已完成</el-tag>
                  </div>
                  <div class="module-meta">
                    <el-progress
                      :percentage="module.progress || 0"
                      :show-text="true"
                      :stroke-width="8"
                      class="module-progress"
                      :status="module.status === 'completed' ? 'success' : ''"
                    />
                    <span class="module-hours">
                      {{ (module.actual_hours || 0).toFixed(1) }}h / {{ module.duration_hours || 0 }}h
                    </span>
                  </div>
                  <!-- 模块操作按钮 -->
                  <div class="module-actions" v-if="module.module_key">
                    <template v-if="module.status === 'not_started'">
                      <el-button
                        type="primary"
                        size="small"
                        :icon="VideoPlay"
                        @click="handleStartModule(module.module_key, module.name)"
                      >
                        开始学习
                      </el-button>
                    </template>
                    <template v-else-if="module.status === 'in_progress'">
                      <el-button
                        size="small"
                        :icon="Clock"
                        @click="openActivityDialog(module.module_key, module.name)"
                      >
                        记录时长
                      </el-button>
                      <el-button
                        type="success"
                        size="small"
                        :icon="Check"
                        @click="handleCompleteModule(module.module_key, module.name)"
                      >
                        完成
                      </el-button>
                    </template>
                    <template v-else>
                      <el-button
                        size="small"
                        :icon="Clock"
                        @click="openActivityDialog(module.module_key, module.name)"
                      >
                        复习
                      </el-button>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 统计信息 -->
      <el-col :xs="24" :lg="8">
        <el-card class="stats-card" v-loading="progressLoading">
          <template #header>
            <span>路径统计</span>
          </template>
          <div class="stat-item">
            <div class="stat-label">完成度</div>
            <div class="stat-value">
              <el-progress
                type="dashboard"
                :percentage="pathProgress?.overall_completion || currentPath.progress_percentage || 0"
                :width="120"
              >
                <template #default="{ percentage }">
                  <span class="percentage-value">{{ percentage }}%</span>
                </template>
              </el-progress>
            </div>
          </div>

          <el-divider />

          <div class="info-list">
            <div class="info-item" v-if="currentPath.title">
              <span class="label">路径标题：</span>
              <span class="value">{{ currentPath.title }}</span>
            </div>
            <div class="info-item" v-if="currentPath.description">
              <span class="label">路径描述：</span>
              <span class="value" style="word-break: break-word;">{{ currentPath.description }}</span>
            </div>
            <div class="info-item">
              <span class="label">学习目标：</span>
              <span class="value">{{ getGoalText(currentPath.learning_goal) }}</span>
            </div>
            <div class="info-item">
              <span class="label">当前模块：</span>
              <span class="value">{{ pathProgress?.current_module?.module_name || getCurrentPhaseName() }}</span>
            </div>
            <div class="info-item">
              <span class="label">模块进度：</span>
              <span class="value">{{ pathProgress?.completed_modules_count || 0 }}/{{ pathProgress?.total_modules_count || currentPath.phases?.length || 0 }}</span>
            </div>
            <div class="info-item">
              <span class="label">已学时长：</span>
              <span class="value">{{ (pathProgress?.total_study_hours || 0).toFixed(1) }}h / {{ (pathProgress?.estimated_total_hours || 0).toFixed(1) }}h</span>
            </div>
            <div class="info-item">
              <span class="label">创建时间：</span>
              <span class="value">{{ formatDate(currentPath.created_at) }}</span>
            </div>
          </div>

          <el-divider />

          <div class="milestone-section">
            <h4>下一里程碑</h4>
            <p class="milestone-text">
              {{ getNextMilestone() }}
            </p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 学习活动记录弹窗 -->
    <el-dialog
      v-model="activityDialogVisible"
      :title="`记录学习活动 - ${selectedModule?.name || ''}`"
      width="480px"
    >
      <el-form :model="activityForm" label-width="100px">
        <el-form-item label="活动类型">
          <el-radio-group v-model="activityForm.activity_type">
            <el-radio-button
              v-for="option in activityTypeOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
              <span class="activity-hint">{{ option.description }}</span>
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="学习时长">
          <el-slider
            v-model="activityForm.duration_minutes"
            :min="10"
            :max="180"
            :step="10"
            show-input
            :format-tooltip="(val: number) => `${val}分钟`"
          />
        </el-form-item>
        <el-form-item label="学习备注">
          <el-input
            v-model="activityForm.notes"
            type="textarea"
            :rows="3"
            placeholder="记录学习内容、心得或遇到的问题..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="activityDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitActivity">确认记录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, CircleCheck, VideoPlay, Clock, Check } from '@element-plus/icons-vue'
import { useLearningStore } from '@/stores/learning'
import { formatDate } from '@/utils/format'
import { LEARNING_GOAL_OPTIONS } from '@/utils/constants'
import type { PhaseProgressDetail, ActivityType } from '@/types/progress'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const learningStore = useLearningStore()

const loading = computed(() => learningStore.loading)
const currentPath = computed(() => learningStore.currentPath)
const pathProgress = computed(() => learningStore.pathProgress)
const progressLoading = computed(() => learningStore.progressLoading)

// 学习活动记录弹窗
const activityDialogVisible = ref(false)
const selectedModule = ref<{ key: string; name: string } | null>(null)
const activityForm = ref({
  activity_type: 'study' as ActivityType,
  duration_minutes: 30,
  notes: ''
})

// 监听 currentPath 变化，获取进度
watch(() => currentPath.value?.id, (newId) => {
  if (newId) {
    learningStore.fetchPathProgress(Number(newId))
  }
}, { immediate: true })

// 适配后端返回的 phases 数据，优先使用进度API的数据
const adaptedPhases = computed(() => {
  // 如果有详细进度数据，使用进度数据
  if (pathProgress.value?.phases) {
    return pathProgress.value.phases.map((phase: PhaseProgressDetail) => ({
      phase: phase.phase_index + 1,
      title: phase.phase_title,
      goal: phase.goal,
      weeks: phase.weeks,
      status: getPhaseStatus(phase),
      progress: Math.round(phase.completion_percentage),
      modules: phase.modules.map(m => ({
        name: m.module_name,
        module_key: m.module_key,
        progress: Math.round(m.completion_percentage),
        status: m.status,
        duration_hours: m.estimated_hours,
        actual_hours: m.actual_hours
      }))
    }))
  }

  // 否则使用原始路径数据
  if (!currentPath.value?.phases) return []

  return currentPath.value.phases.map((phase, index) => ({
    ...phase,
    status: phase.status || 'not_started',
    progress: phase.progress || 0
  }))
})

// 根据模块完成情况判断阶段状态
const getPhaseStatus = (phase: PhaseProgressDetail) => {
  if (phase.completed_modules === phase.total_modules && phase.total_modules > 0) {
    return 'completed'
  }
  if (phase.completion_percentage > 0) {
    return 'in_progress'
  }
  return 'not_started'
}

// 将模块数据适配为统一格式
const adaptModules = (modules: any[] | string[]) => {
  if (!modules) return []

  return modules.map((module) => {
    // 如果是字符串，转换为对象
    if (typeof module === 'string') {
      return {
        name: module,
        progress: 0,
        status: 'not_started',
        duration_hours: 0
      }
    }
    // 如果已经是对象，直接返回
    return {
      name: module.name || '',
      module_key: module.module_key || '',
      progress: module.progress || 0,
      status: module.status || 'not_started',
      duration_hours: module.duration_hours || 0,
      actual_hours: module.actual_hours || 0
    }
  })
}

const goToGenerate = () => {
  router.push('/learning-path/generate')
}

// 开始学习模块
const handleStartModule = async (moduleKey: string, moduleName: string) => {
  try {
    await learningStore.startModule(moduleKey)
    ElMessage.success(`已开始学习「${moduleName}」`)
  } catch (error) {
    ElMessage.error('操作失败，请重试')
  }
}

// 标记模块完成
const handleCompleteModule = async (moduleKey: string, moduleName: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要将「${moduleName}」标记为已完成吗？`,
      '确认完成',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'success'
      }
    )
    await learningStore.completeModule(moduleKey)
    ElMessage.success(`恭喜！「${moduleName}」已完成`)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败，请重试')
    }
  }
}

// 打开记录学习活动弹窗
const openActivityDialog = (moduleKey: string, moduleName: string) => {
  selectedModule.value = { key: moduleKey, name: moduleName }
  activityForm.value = {
    activity_type: 'study',
    duration_minutes: 30,
    notes: ''
  }
  activityDialogVisible.value = true
}

// 提交学习活动记录
const submitActivity = async () => {
  if (!selectedModule.value) return

  try {
    const response = await learningStore.recordActivity(selectedModule.value.key, activityForm.value)
    activityDialogVisible.value = false
    ElMessage.success(response.message || `已记录学习活动，进度 +${response.progress_change.toFixed(1)}%`)
  } catch (error) {
    ElMessage.error('记录失败，请重试')
  }
}

// 活动类型选项
const activityTypeOptions = [
  { value: 'study', label: '学习新内容', description: '30分钟 +5%' },
  { value: 'practice', label: '实践练习', description: '30分钟 +10%' },
  { value: 'review', label: '复习回顾', description: '30分钟 +3%' }
]

const getPhaseStatusType = (status: string) => {
  const map: Record<string, any> = {
    not_started: 'info',
    in_progress: 'warning',
    completed: 'success'
  }
  return map[status] || 'info'
}

const getPhaseStatusText = (status: string) => {
  const map: Record<string, string> = {
    not_started: '未开始',
    in_progress: '进行中',
    completed: '已完成'
  }
  return map[status] || status
}

const getGoalText = (goal?: string) => {
  if (!goal) return '学习提升'
  const option = LEARNING_GOAL_OPTIONS.find(o => o.value === goal)
  return option?.label || goal
}

const getCurrentPhaseName = () => {
  const phases = currentPath.value?.phases || []
  // 优先查找进行中的阶段
  const inProgressPhase = phases.find(p => p.status === 'in_progress')
  if (inProgressPhase) return inProgressPhase.title || inProgressPhase.name || '进行中'
  
  // 否则返回第一个未开始的阶段
  const notStartedPhase = phases.find(p => !p.status || p.status === 'not_started')
  if (notStartedPhase) return notStartedPhase.title || notStartedPhase.name || '待开始'
  
  return '暂无'
}

const getNextModuleName = () => {
  const phases = currentPath.value?.phases || []
  for (const phase of phases) {
    const modules = adaptModules(phase.modules || [])
    const module = modules.find(m => m.status !== 'completed')
    if (module) return module.name
  }
  return '暂无'
}

const getNextMilestone = () => {
  // 优先使用进度API的下一模块数据
  if (pathProgress.value?.next_module) {
    return `完成《${pathProgress.value.next_module.module_name}》模块`
  }
  if (pathProgress.value?.current_module) {
    return `继续学习《${pathProgress.value.current_module.module_name}》模块`
  }

  const nextModule = getNextModuleName()
  if (nextModule === '暂无') {
    return '恭喜！所有模块已完成'
  }
  return `完成《${nextModule}》模块`
}

onMounted(async () => {
  await learningStore.fetchActivePath()
})
</script>

<style scoped lang="scss">
.learning-path-container {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    h2 {
      margin: 0;
      font-size: 24px;
    }
  }
  
  .loading-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
  }
  
  .empty-state {
    min-height: 400px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .path-timeline {
    .phase-item {
      position: relative;
      padding-left: 40px;
      padding-bottom: 40px;
      
      &:not(:last-child)::before {
        content: '';
        position: absolute;
        left: 19px;
        top: 40px;
        bottom: 0;
        width: 2px;
        background: #E4E7ED;
      }
      
      .phase-header {
        display: flex;
        align-items: flex-start;
        gap: 20px;
        margin-bottom: 20px;
        
        .phase-number {
          position: absolute;
          left: 0;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: #409EFF;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: 16px;
        }
        
        .phase-info {
          flex: 1;
          
          h3 {
            margin: 0 0 8px 0;
            font-size: 18px;
          }
          
          p {
            margin: 0 0 12px 0;
            color: #606266;
          }
          
          .phase-meta {
            display: flex;
            align-items: center;
            gap: 16px;
            
            span {
              font-size: 14px;
              color: #909399;
            }
          }
        }
        
        .phase-progress {
          flex-shrink: 0;
        }
      }
      
      .modules-list {
        .module-item {
          padding: 12px;
          background: #F5F7FA;
          border-radius: 8px;
          margin-bottom: 12px;
          transition: all 0.3s ease;
          border-left: 3px solid transparent;

          &:last-child {
            margin-bottom: 0;
          }

          &.module-completed {
            background: #F0F9EB;
            border-left-color: #67C23A;
          }

          &.module-in-progress {
            background: #FDF6EC;
            border-left-color: #E6A23C;
          }

          .module-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;

            .module-name {
              font-size: 14px;
              color: #303133;
              flex: 1;
            }
          }

          .module-meta {
            display: flex;
            align-items: center;
            gap: 12px;

            .module-progress {
              flex: 1;
            }

            .module-hours {
              font-size: 12px;
              color: #909399;
              min-width: 80px;
              text-align: right;
            }
          }
        }
      }
    }
  }
  
  .stats-card {
    .stat-item {
      text-align: center;
      padding: 20px;
      
      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-bottom: 16px;
      }
      
      .stat-value {
        .percentage-value {
          font-size: 24px;
          font-weight: bold;
        }
      }
    }
    
    .info-list {
      .info-item {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid #EBEEF5;
        
        &:last-child {
          border-bottom: none;
        }
        
        .label {
          color: #909399;
          font-size: 14px;
        }
        
        .value {
          color: #303133;
          font-size: 14px;
          font-weight: 500;
        }
      }
    }
    
    .milestone-section {
      h4 {
        margin: 0 0 12px 0;
        font-size: 16px;
      }
      
      .milestone-text {
        color: #606266;
        font-size: 14px;
        margin: 0;
      }
    }
  }
}
</style>
