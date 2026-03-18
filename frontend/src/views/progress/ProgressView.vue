<template>
  <div class="progress-container">
    <div class="page-header">
      <h2>学习进度</h2>
      <el-button type="primary" @click="fetchWeeklyReport">
        生成周报
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="24" class="stats-row" v-loading="loading">
      <el-col :xs="12" :lg="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">总学习时长</div>
            <div class="stat-value">{{ formatNumber(stats.total_study_hours || 0, 1) }}h</div>
            <div class="stat-trend" :class="stats.week_change_percent >= 0 ? 'positive' : 'negative'">
              较上周 {{ stats.week_change_percent >= 0 ? '+' : '' }}{{ formatNumber(stats.week_change_percent || 0, 0) }}%
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">完成任务数</div>
            <div class="stat-value">{{ stats.completed_tasks || 0 }}</div>
            <div class="stat-trend">本周</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">学习天数</div>
            <div class="stat-value">{{ stats.learning_days || 0 }}</div>
            <div class="stat-trend">本周</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">平均每日时长</div>
            <div class="stat-value">{{ formatNumber(stats.average_daily_hours || 0, 1) }}h</div>
            <div class="stat-trend">本周平均</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表 -->
    <el-row :gutter="24">
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>每周学习时长分布</template>
          <div ref="weeklyChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>进度趋势变化</template>
          <div ref="trendChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 周报 -->
    <el-card v-if="weeklyReport" class="report-card">
      <template #header>周报总结</template>
      <div class="report-content">
        <p><strong>学习时长:</strong> {{ formatNumber(weeklyReport.study_hours || 0, 1) }} 小时</p>
        <p><strong>完成任务:</strong> {{ weeklyReport.tasks_completed || 0 }} 个</p>
        <p><strong>提问数量:</strong> {{ weeklyReport.questions_asked || 0 }} 次</p>
        <p v-if="weeklyReport.completed_modules && weeklyReport.completed_modules.length > 0">
          <strong>完成模块:</strong> {{ weeklyReport.completed_modules.join(', ') }}
        </p>
        <div v-if="weeklyReport.suggestions && weeklyReport.suggestions.length > 0" class="suggestions">
          <strong>建议:</strong>
          <ul>
            <li v-for="(suggestion, index) in weeklyReport.suggestions" :key="index">
              {{ suggestion }}
            </li>
          </ul>
        </div>
      </div>
    </el-card>

    <!-- 进度变更历史 -->
    <el-card class="history-card">
      <template #header>
        <div class="history-header">
          <span>进度变更历史</span>
          <el-button text type="primary" @click="fetchProgressHistory" :loading="historyLoading">
            刷新
          </el-button>
        </div>
      </template>
      <div v-if="progressHistory.length === 0 && !historyLoading" class="empty-history">
        <el-empty description="暂无进度变更记录" :image-size="80" />
      </div>
      <el-timeline v-else>
        <el-timeline-item
          v-for="item in progressHistory"
          :key="item.id"
          :timestamp="formatDateTime(item.created_at)"
          :type="getHistoryType(item)"
          placement="top"
        >
          <div class="history-item">
            <div class="history-module">{{ item.module_name }}</div>
            <div class="history-change">
              <span class="old-value">{{ item.old_percentage.toFixed(1) }}%</span>
              <el-icon><ArrowRight /></el-icon>
              <span class="new-value" :class="{ 'increased': item.new_percentage > item.old_percentage }">
                {{ item.new_percentage.toFixed(1) }}%
              </span>
              <el-tag size="small" :type="getTriggerTagType(item.trigger_type)">
                {{ getTriggerTypeText(item.trigger_type) }}
              </el-tag>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { ArrowRight } from '@element-plus/icons-vue'
import { progressApi } from '@/api'
import { formatNumber } from '@/utils/format'
import type { ProgressStats, WeeklyReport, ProgressHistoryItem, ProgressTriggerType } from '@/types/progress'

const loading = ref(false)
const stats = ref<Partial<ProgressStats>>({})
const weeklyReport = ref<WeeklyReport | null>(null)
const weeklyChartRef = ref<HTMLElement>()
const trendChartRef = ref<HTMLElement>()
const progressHistory = ref<ProgressHistoryItem[]>([])
const historyLoading = ref(false)

let weeklyChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null
const refreshTimer = ref<number | null>(null)

const fetchStats = async () => {
  loading.value = true
  try {
    stats.value = await progressApi.getStats()
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  } finally {
    loading.value = false
  }
}

const fetchWeeklyReport = async () => {
  try {
    weeklyReport.value = await progressApi.getWeeklyReport()
  } catch (error) {
    console.error('Failed to fetch weekly report:', error)
  }
}

const fetchProgressHistory = async () => {
  historyLoading.value = true
  try {
    const response = await progressApi.getProgressHistory(undefined, 20)
    progressHistory.value = response.items
  } catch (error) {
    console.error('Failed to fetch progress history:', error)
  } finally {
    historyLoading.value = false
  }
}

const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getHistoryType = (item: ProgressHistoryItem) => {
  if (item.new_percentage >= 100) return 'success'
  if (item.new_percentage > item.old_percentage) return 'primary'
  return 'info'
}

const getTriggerTypeText = (triggerType: ProgressTriggerType) => {
  const map: Record<string, string> = {
    manual: '手动更新',
    conversation: '对话学习',
    task: '完成任务',
    time: '学习活动',
    quiz: '测验结果',
    ai: 'AI评估',
    system: '系统更新'
  }
  return map[triggerType] || triggerType
}

const getTriggerTagType = (triggerType: ProgressTriggerType) => {
  const map: Record<string, string> = {
    manual: 'info',
    conversation: 'success',
    task: 'warning',
    time: 'primary',
    quiz: '',
    ai: 'danger',
    system: 'info'
  }
  return map[triggerType] || 'info'
}

const initCharts = () => {
  // 初始化每周学习时长图表
  if (weeklyChartRef.value) {
    weeklyChart = echarts.init(weeklyChartRef.value)
    updateWeeklyChart()
  }

  // 初始化进度趋势图表
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    updateTrendChart()
  }
}

const updateWeeklyChart = () => {
  if (!weeklyChart) return

  const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const dailyHours = stats.value.daily_hours || {}

  // 从后端数据获取每日学习时长
  const data = weekdays.map(day => dailyHours[day] || 0)

  weeklyChart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c} 小时'
    },
    xAxis: {
      type: 'category',
      data: weekdays
    },
    yAxis: {
      type: 'value',
      name: '小时',
      min: 0
    },
    series: [{
      data: data,
      type: 'bar',
      itemStyle: { color: '#409EFF' },
      label: {
        show: true,
        position: 'top',
        formatter: (params: any) => params.value > 0 ? params.value + 'h' : ''
      }
    }],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true }
  })
}

const updateTrendChart = () => {
  if (!trendChart) return

  const weeklyTrend = stats.value.weekly_trend || []

  // 从后端数据获取周进度趋势
  const weeks = weeklyTrend.map(item => item.week)
  const completions = weeklyTrend.map(item => item.completion)

  // 如果没有数据，显示空状态
  if (weeks.length === 0) {
    weeks.push('W1', 'W2', 'W3', 'W4')
    completions.push(0, 0, 0, 0)
  }

  trendChart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c}%'
    },
    xAxis: {
      type: 'category',
      data: weeks
    },
    yAxis: {
      type: 'value',
      name: '进度%',
      min: 0,
      max: 100
    },
    series: [{
      data: completions,
      type: 'line',
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
          { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
        ])
      },
      itemStyle: { color: '#67C23A' },
      label: {
        show: true,
        position: 'top',
        formatter: '{c}%'
      }
    }],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true }
  })
}

// 监听 stats 变化，更新图表
watch(() => stats.value, () => {
  nextTick(() => {
    updateWeeklyChart()
    updateTrendChart()
  })
}, { deep: true })

onMounted(async () => {
  await Promise.all([
    fetchStats(),
    fetchProgressHistory()
  ])
  nextTick(() => {
    initCharts()
  })

  refreshTimer.value = window.setInterval(async () => {
    await Promise.all([
      fetchStats(),
      fetchProgressHistory()
    ])
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
.progress-container {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h2 {
      margin: 0;
    }
  }

  .stats-row {
    margin-bottom: 24px;
  }

  .stat-card {
    .stat-item {
      text-align: center;

      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-bottom: 12px;
      }

      .stat-value {
        font-size: 32px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 8px;
      }

      .stat-trend {
        font-size: 12px;
        color: #909399;

        &.positive {
          color: #67C23A;
        }

        &.negative {
          color: #F56C6C;
        }
      }
    }
  }

  .report-card {
    margin-top: 24px;

    .report-content {
      p {
        line-height: 1.8;
        color: #606266;
        margin-bottom: 8px;
      }

      .suggestions {
        margin-top: 16px;

        ul {
          margin: 8px 0 0 20px;
          padding: 0;

          li {
            line-height: 1.8;
            color: #606266;
          }
        }
      }
    }
  }

  .history-card {
    margin-top: 24px;

    .history-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .empty-history {
      padding: 20px 0;
    }

    .history-item {
      .history-module {
        font-weight: 500;
        color: #303133;
        margin-bottom: 4px;
      }

      .history-change {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;

        .old-value {
          color: #909399;
        }

        .new-value {
          color: #303133;
          font-weight: 500;

          &.increased {
            color: #67C23A;
          }
        }

        .el-icon {
          color: #C0C4CC;
        }
      }
    }
  }
}
</style>
