<template>
  <el-card class="task-header-card" shadow="never">
    <div class="task-header">
      <div class="title-wrap">
        <div class="eyebrow">当前研究</div>
        <h1>{{ task.topic }}</h1>
      </div>

      <div class="summary-grid">
        <div class="summary-item">
          <span class="summary-label">任务状态</span>
          <el-tag :type="statusType" effect="dark" round>{{ statusLabel }}</el-tag>
        </div>
        <div class="summary-item">
          <span class="summary-label">分析师数量</span>
          <strong>{{ task.max_analysts }}</strong>
        </div>
        <div class="summary-item wide">
          <span class="summary-label">当前进度</span>
          <p>{{ progressMessage }}</p>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DeepResearchProgress, DeepResearchTask } from '@/types/deep-research'

interface Props {
  task: DeepResearchTask
  progress?: DeepResearchProgress | null
}

const props = defineProps<Props>()

const statusLabelMap = {
  pending: '待生成分析师',
  awaiting_feedback: '等待人工确认',
  running: '研究进行中',
  completed: '报告已完成',
  failed: '执行失败'
}

const statusTypeMap = {
  pending: 'info',
  awaiting_feedback: 'warning',
  running: 'primary',
  completed: 'success',
  failed: 'danger'
} as const

const statusLabel = computed(() => statusLabelMap[props.task.status] || props.task.status)
const statusType = computed(() => statusTypeMap[props.task.status] || 'info')
const progressMessage = computed(() => props.progress?.message || '等待操作')
</script>

<style scoped lang="scss">
.task-header-card {
  border: none;
  background:
    radial-gradient(circle at top left, rgba(71, 125, 255, 0.18), transparent 32%),
    radial-gradient(circle at bottom right, rgba(245, 169, 75, 0.14), transparent 28%),
    linear-gradient(135deg, #fffdf7 0%, #f4f7fb 100%);
}

.task-header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
}

.title-wrap {
  flex: 1;

  .eyebrow {
    color: #55708f;
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 10px;
  }

  h1 {
    margin: 0;
    font-size: 30px;
    line-height: 1.24;
    color: #12314d;
  }
}

.summary-grid {
  min-width: 340px;
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 14px;
}

.summary-item {
  padding: 16px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(18, 49, 77, 0.06);
  border-radius: 16px;

  &.wide {
    grid-column: 1 / -1;
  }

  strong,
  p {
    margin: 8px 0 0;
    color: #17324d;
  }

  strong {
    font-size: 24px;
  }

  p {
    line-height: 1.6;
    font-size: 14px;
  }
}

.summary-label {
  font-size: 12px;
  color: #69819d;
}

@media (max-width: 1080px) {
  .task-header {
    flex-direction: column;
  }

  .summary-grid {
    min-width: 0;
  }
}
</style>
