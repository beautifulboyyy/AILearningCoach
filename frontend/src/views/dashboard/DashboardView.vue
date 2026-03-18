<template>
  <div class="dashboard-container">
    <!-- 统计卡片 -->
    <el-row :gutter="24" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #ecf5ff">
              <el-icon :size="40" color="#409EFF"><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">总学习时长</div>
              <div class="stat-value">{{ stats.total_study_hours || 0 }}h</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f0f9ff">
              <el-icon :size="40" color="#67C23A"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">完成任务数</div>
              <div class="stat-value">{{ stats.completed_tasks || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fef0f0">
              <el-icon :size="40" color="#E6A23C"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">当前阶段</div>
              <div class="stat-value phase-text">{{ currentPhase }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f4f4f5">
              <el-icon :size="40" color="#909399"><DataAnalysis /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">周进度</div>
              <div class="stat-value">{{ weeklyProgress }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表和任务 -->
    <el-row :gutter="24" class="content-row">
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <span>学习时长趋势</span>
          </template>
          <div ref="studyChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <el-card class="tasks-card">
          <template #header>
            <div class="card-header">
              <span>即将到来的任务</span>
              <el-button type="primary" link @click="goToTasks">查看全部</el-button>
            </div>
          </template>
          <div v-loading="tasksLoading" class="tasks-list">
            <div
              v-for="task in upcomingTasks"
              :key="task.id"
              class="task-item"
              @click="goToTaskDetail(task.id)"
            >
              <div class="task-content">
                <div class="task-title">{{ task.title }}</div>
                <div class="task-meta">
                  <el-tag
                    :type="getPriorityType(task.priority)"
                    size="small"
                  >
                    {{ getPriorityLabel(task.priority) }}
                  </el-tag>
                  <span class="task-date">{{ formatDate(task.due_date) }}</span>
                </div>
              </div>
            </div>
            <el-empty v-if="!tasksLoading && upcomingTasks.length === 0" description="暂无任务" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row :gutter="24">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>最近活动</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(activity, index) in recentActivities"
              :key="index"
              :timestamp="activity.timestamp"
              placement="top"
            >
              {{ activity.content }}
            </el-timeline-item>
            <el-timeline-item v-if="recentActivities.length === 0">
              暂无活动记录
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { Timer, CircleCheck, TrendCharts, DataAnalysis } from '@element-plus/icons-vue'
import { progressApi, taskApi } from '@/api'
import { formatDate, formatRelativeTime } from '@/utils/format'
import { PRIORITY_OPTIONS } from '@/utils/constants'
import type { ProgressStats } from '@/types/progress'
import type { Task } from '@/types/task'

const router = useRouter()

const studyChartRef = ref<HTMLElement>()
const stats = ref<ProgressStats>({
  total_study_hours: 0,
  completed_tasks: 0,
  learning_days: 0,
  average_daily_hours: 0
})
const upcomingTasks = ref<Task[]>([])
const tasksLoading = ref(false)
const recentActivities = ref<any[]>([])
const weeklyStudyData = ref<number[]>([0, 0, 0, 0, 0, 0, 0])
const refreshTimer = ref<number | null>(null)

const currentPhase = computed(() => stats.value.current_module || '暂无')
const weeklyProgress = computed(() => Math.round(stats.value.overall_completion || 0))

// 获取统计数据
const fetchStats = async () => {
  try {
    const data = await progressApi.getStats()
    stats.value = data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

// 获取周报数据（包含每日学习时长）
const fetchWeeklyData = async () => {
  try {
    const report = await progressApi.getWeeklyReport()
    if (report.daily_hours) {
      // 将每日学习时长数据转换为数组格式
      const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
      weeklyStudyData.value = days.map((day) => report.daily_hours?.[day] || 0)
    }
  } catch (error) {
    console.error('Failed to fetch weekly data:', error)
    // 如果获取失败，使用空数据
    weeklyStudyData.value = [0, 0, 0, 0, 0, 0, 0]
  }
}

// 获取最近活动
const fetchRecentActivities = async () => {
  try {
    // 获取最近完成的任务作为活动记录
    const res = await taskApi.getTasks({ status: 'completed', limit: 5 })
    recentActivities.value = (res.tasks || []).slice(0, 3).map((task: Task) => ({
      content: `完成了任务：${task.title}`,
      timestamp: task.completed_at ? formatRelativeTime(task.completed_at) : formatRelativeTime(task.updated_at || task.created_at || new Date().toISOString())
    }))
    
    // 如果没有已完成的任务，显示提示信息
    if (recentActivities.value.length === 0) {
      recentActivities.value = [
        { content: '暂无活动记录，开始您的学习之旅吧！', timestamp: formatRelativeTime(new Date().toISOString()) }
      ]
    }
  } catch (error) {
    console.error('Failed to fetch recent activities:', error)
    recentActivities.value = []
  }
}

// 获取即将到来的任务
const fetchUpcomingTasks = async () => {
  tasksLoading.value = true
  try {
    const [todoRes, progressRes] = await Promise.all([
      taskApi.getTasks({ status: 'todo', limit: 5 }),
      taskApi.getTasks({ status: 'in_progress', limit: 5 })
    ])
    const merged = [...(progressRes.tasks || []), ...(todoRes.tasks || [])]
    upcomingTasks.value = merged
      .sort((a, b) => {
        const aTime = a.due_date ? new Date(a.due_date).getTime() : Number.MAX_SAFE_INTEGER
        const bTime = b.due_date ? new Date(b.due_date).getTime() : Number.MAX_SAFE_INTEGER
        return aTime - bTime
      })
      .slice(0, 5)
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
  } finally {
    tasksLoading.value = false
  }
}

// 初始化图表
const initChart = () => {
  if (!studyChartRef.value) return
  
  const chart = echarts.init(studyChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const item = params[0]
        return `${item.name}<br/>${item.seriesName}: ${item.value}小时`
      }
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '学习时长（小时）',
      minInterval: 0.5
    },
    series: [
      {
        name: '学习时长',
        type: 'line',
        data: weeklyStudyData.value,
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        },
        lineStyle: {
          color: '#409EFF',
          width: 2
        },
        itemStyle: {
          color: '#409EFF'
        }
      }
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

const getPriorityType = (priority: string) => {
  const map: Record<string, any> = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  }
  return map[priority] || 'info'
}

const getPriorityLabel = (priority: string) => {
  const option = PRIORITY_OPTIONS.find(o => o.value === priority)
  return option?.label || priority
}

const goToTasks = () => {
  router.push('/tasks')
}

const goToTaskDetail = (id: string | number) => {
  router.push(`/tasks`)
}

onMounted(async () => {
  // 并行获取所有数据
  await Promise.all([
    fetchStats(),
    fetchUpcomingTasks(),
    fetchWeeklyData(),
    fetchRecentActivities()
  ])
  
  // 等待数据加载完成后初始化图表
  nextTick(() => {
    initChart()
  })

  // 定时刷新面板数据，避免长驻页面时数据显示陈旧
  refreshTimer.value = window.setInterval(async () => {
    await Promise.all([fetchStats(), fetchUpcomingTasks(), fetchRecentActivities()])
  }, 30000)
})

onBeforeUnmount(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
})
</script>

<style scoped lang="scss">
.dashboard-container {
  .stats-row {
    margin-bottom: 24px;
  }
  
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .stat-icon {
        width: 80px;
        height: 80px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }
      
      .stat-info {
        flex: 1;
        
        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-bottom: 8px;
        }
        
        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #303133;
          
          &.phase-text {
            font-size: 18px;
          }
        }
      }
    }
  }
  
  .content-row {
    margin-bottom: 24px;
  }
  
  .chart-card {
    .chart-container {
      height: 300px;
    }
  }
  
  .tasks-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .tasks-list {
      min-height: 300px;
      max-height: 300px;
      overflow-y: auto;
      
      .task-item {
        padding: 12px;
        border-bottom: 1px solid #EBEEF5;
        cursor: pointer;
        transition: all 0.3s;
        
        &:hover {
          background: #F5F7FA;
        }
        
        &:last-child {
          border-bottom: none;
        }
        
        .task-content {
          .task-title {
            font-size: 14px;
            color: #303133;
            margin-bottom: 8px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          
          .task-meta {
            display: flex;
            align-items: center;
            gap: 12px;
            
            .task-date {
              font-size: 12px;
              color: #909399;
            }
          }
        }
      }
    }
  }
}
</style>
