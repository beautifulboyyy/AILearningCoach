<template>
  <el-card class="rail-card" shadow="never">
    <template #header>
      <div class="rail-header">
        <div>
          <span>任务轨道</span>
          <p>切换任务、查看状态、删除历史任务</p>
        </div>
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
  height: min(640px, calc(100vh - 250px));
  min-height: 360px;
  background:
    radial-gradient(circle at top right, rgba(76, 141, 246, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.88) 0%, rgba(250, 247, 240, 0.92) 100%);
  box-shadow: 0 18px 40px rgba(19, 42, 66, 0.08);

  :deep(.el-card__header) {
    border-bottom: 1px solid rgba(22, 49, 76, 0.08);
  }

  :deep(.el-card__body) {
    height: calc(100% - 92px);
    padding-top: 16px;
  }
}

.rail-header {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: space-between;
  gap: 12px;
  color: #17324d;
  font-weight: 700;

  p {
    margin: 6px 0 0;
    color: #6f8096;
    font-size: 13px;
    font-weight: 400;
  }
}

.rail-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(76, 141, 246, 0.24);
    border-radius: 999px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

.task-item {
  width: 100%;
  border: 1px solid rgba(22, 49, 76, 0.08);
  border-radius: 18px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.82);
  color: #17324d;
  text-align: left;
  cursor: pointer;
  transition: all 0.24s ease;
  box-shadow: 0 12px 24px rgba(20, 44, 70, 0.04);

  &:hover {
    transform: translateY(-1px);
    border-color: rgba(76, 141, 246, 0.32);
    background:
      radial-gradient(circle at top right, rgba(76, 141, 246, 0.12), transparent 30%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(244, 248, 255, 0.95) 100%);
  }

  &.active {
    border-color: rgba(76, 141, 246, 0.4);
    background:
      radial-gradient(circle at top right, rgba(76, 141, 246, 0.15), transparent 30%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(241, 247, 255, 0.98) 100%);
    box-shadow: 0 18px 34px rgba(76, 141, 246, 0.12);
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
  font-size: 16px;
  font-weight: 700;
  line-height: 1.6;
  color: #17324d;
}

.task-time,
.task-meta span {
  color: #72849a;
  font-size: 12px;
}

@media (max-width: 1080px) {
  .rail-card {
    height: auto;
    min-height: 320px;
  }

  .rail-list {
    max-height: 420px;
  }
}
</style>
