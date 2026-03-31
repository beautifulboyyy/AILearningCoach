<template>
  <el-card class="rail-card" shadow="never">
    <template #header>
      <div class="rail-header">
        <span>任务轨道</span>
        <el-segmented v-model="currentFilter" :options="filterOptions" size="small" />
      </div>
    </template>

    <div v-loading="loading" class="rail-list">
      <button
        v-for="task in filteredTasks"
        :key="task.thread_id"
        type="button"
        class="task-item"
        :class="{ active: task.thread_id === selectedTaskId }"
        @click="$emit('select', task.thread_id)"
      >
        <div class="task-item-top">
          <el-tag :type="statusTypeMap[task.status]" effect="dark" size="small">
            {{ statusLabelMap[task.status] }}
          </el-tag>
          <span class="task-time">{{ formatTime(task.updated_at) }}</span>
        </div>
        <div class="task-topic">{{ task.topic }}</div>
        <div class="task-meta">
          <span>分析师 {{ task.max_analysts }} 位</span>
          <el-button
            text
            type="danger"
            size="small"
            @click.stop="$emit('delete', task.thread_id)"
          >
            删除
          </el-button>
        </div>
      </button>

      <el-empty v-if="!loading && filteredTasks.length === 0" description="暂无研究任务" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import dayjs from 'dayjs'
import type { DeepResearchStatus, DeepResearchTask } from '@/types/deepResearch'

interface Props {
  tasks: DeepResearchTask[]
  selectedTaskId?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selectedTaskId: '',
  loading: false
})

defineEmits<{
  select: [threadId: string]
  delete: [threadId: string]
}>()

const currentFilter = ref<'all' | DeepResearchStatus>('all')

const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '待处理', value: 'pending' },
  { label: '待确认', value: 'awaiting_feedback' },
  { label: '运行中', value: 'running' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' }
]

const statusLabelMap: Record<DeepResearchStatus, string> = {
  pending: '待生成',
  awaiting_feedback: '待确认',
  running: '运行中',
  completed: '已完成',
  failed: '失败'
}

const statusTypeMap: Record<DeepResearchStatus, 'info' | 'warning' | 'success' | 'danger' | 'primary'> = {
  pending: 'info',
  awaiting_feedback: 'warning',
  running: 'primary',
  completed: 'success',
  failed: 'danger'
}

const filteredTasks = computed(() => {
  if (currentFilter.value === 'all') return props.tasks
  return props.tasks.filter((task) => task.status === currentFilter.value)
})

const formatTime = (value: string) => {
  return dayjs(value).format('MM-DD HH:mm')
}
</script>

<style scoped lang="scss">
.rail-card {
  border: none;
  background: #10263b;

  :deep(.el-card__header) {
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  :deep(.el-card__body) {
    padding-top: 16px;
  }
}

.rail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #f5f7fa;
  font-weight: 700;
}

.rail-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 240px;
}

.task-item {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.04);
  color: #f5f7fa;
  text-align: left;
  cursor: pointer;
  transition: all 0.24s ease;

  &:hover {
    transform: translateY(-1px);
    border-color: rgba(89, 150, 255, 0.45);
    background: rgba(89, 150, 255, 0.12);
  }

  &.active {
    border-color: #5b8cff;
    background: linear-gradient(180deg, rgba(91, 140, 255, 0.22), rgba(91, 140, 255, 0.12));
    box-shadow: 0 18px 30px rgba(6, 18, 34, 0.28);
  }
}

.task-item-top,
.task-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.task-topic {
  margin: 12px 0;
  font-size: 14px;
  line-height: 1.6;
  color: #f3f6fb;
}

.task-time,
.task-meta span {
  color: rgba(243, 246, 251, 0.68);
  font-size: 12px;
}
</style>
