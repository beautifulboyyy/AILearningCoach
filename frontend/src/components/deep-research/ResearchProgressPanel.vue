<template>
  <el-card class="panel-card progress-card" shadow="never">
    <template #header>
      <div class="panel-header">
        <div>
          <h3>研究进度</h3>
          <p>当前任务正在执行中，页面会自动刷新阶段与任务状态。</p>
        </div>
        <el-tag type="primary" effect="plain" round>{{ stageLabel }}</el-tag>
      </div>
    </template>

    <div class="current-stage">
      <div class="stage-pill">{{ stageLabel }}</div>
      <p>{{ progress.message || '系统正在推进研究流程' }}</p>
      <span v-if="progress.updated_at" class="stage-time">更新时间：{{ formattedTime }}</span>
    </div>

    <div class="timeline">
      <div
        v-for="item in stageItems"
        :key="item.value"
        class="timeline-item"
        :class="{
          active: item.value === progress.stage,
          passed: stageIndex(progress.stage) > stageIndex(item.value)
        }"
      >
        <div class="timeline-dot"></div>
        <div class="timeline-content">
          <strong>{{ item.label }}</strong>
          <span>{{ item.description }}</span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import dayjs from 'dayjs'
import type { DeepResearchProgress, DeepResearchStage } from '@/types/deep-research'

interface Props {
  progress: DeepResearchProgress
}

const props = defineProps<Props>()

const stageItems: Array<{ value: DeepResearchStage; label: string; description: string }> = [
  { value: 'creating_analysts', label: '生成分析师', description: '构建多视角分析团队' },
  { value: 'awaiting_feedback', label: '等待确认', description: '等待人工反馈或批准' },
  { value: 'running', label: '准备执行', description: '开始正式研究流程' },
  { value: 'searching', label: '并行检索', description: '同时检索 Tavily 与 Bocha' },
  { value: 'interviewing', label: '分析师讨论', description: '组织多轮访谈与归纳' },
  { value: 'writing_sections', label: '写作小节', description: '提炼 section 草稿' },
  { value: 'writing_report', label: '整合报告', description: '汇总引言、主体与结论' },
  { value: 'finalizing_report', label: '完成收口', description: '沉淀引用并输出最终报告' }
]

const stageLabelMap: Record<string, string> = {
  idle: '等待开始',
  creating_analysts: '正在生成分析师',
  awaiting_feedback: '等待人工确认',
  running: '正在启动研究',
  searching: '正在并行检索',
  interviewing: '正在分析师讨论',
  writing_sections: '正在整理小节',
  writing_report: '正在生成报告',
  finalizing_report: '正在收尾'
}

const stageLabel = computed(() => {
  return stageLabelMap[props.progress.stage] || props.progress.stage
})

const formattedTime = computed(() => {
  return props.progress.updated_at ? dayjs(props.progress.updated_at).format('YYYY-MM-DD HH:mm:ss') : ''
})

const stageIndex = (stage: string) => {
  return stageItems.findIndex((item) => item.value === stage)
}
</script>

<style scoped lang="scss">
.progress-card {
  border: none;
  background: #ffffff;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;

  h3 {
    margin: 0;
    color: #17324d;
  }

  p {
    margin: 8px 0 0;
    color: #70839a;
  }
}

.current-stage {
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, #f6f9fe 0%, #fffaf1 100%);
  border: 1px solid #e7edf5;

  p {
    margin: 12px 0 8px;
    color: #2b4968;
    line-height: 1.7;
  }
}

.stage-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: #17324d;
  color: #f7fafc;
  font-size: 12px;
  letter-spacing: 0.04em;
}

.stage-time {
  color: #72849a;
  font-size: 12px;
}

.timeline {
  display: grid;
  gap: 10px;
  margin-top: 20px;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 6px;
  opacity: 0.54;
  transition: opacity 0.2s ease, transform 0.2s ease;

  &.active,
  &.passed {
    opacity: 1;
  }

  &.active {
    transform: translateX(4px);
  }
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  margin-top: 5px;
  background: #c4d0de;
  box-shadow: 0 0 0 6px rgba(196, 208, 222, 0.18);

  .timeline-item.passed & {
    background: #4f82f7;
    box-shadow: 0 0 0 6px rgba(79, 130, 247, 0.16);
  }

  .timeline-item.active & {
    background: #f59e42;
    box-shadow: 0 0 0 6px rgba(245, 158, 66, 0.18);
  }
}

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: 4px;

  strong {
    color: #18324d;
  }

  span {
    color: #72849a;
    font-size: 13px;
  }
}
</style>
