<template>
  <div class="report-page">
    <el-card class="report-shell" shadow="never">
      <template #header>
        <div class="report-header">
          <div class="report-header-main">
            <el-button text @click="goBack">返回研究工作台</el-button>
            <div class="report-kicker">Deep Research Report</div>
            <h2>{{ currentTask?.topic || currentReport?.topic || '研究报告' }}</h2>
            <p>
              {{ currentTask?.progress_message || '在这里阅读完整报告。' }}
            </p>
          </div>

          <div class="report-header-side">
            <el-tag v-if="currentTask" :type="getStatusTagType(currentTask.status)" effect="light">
              {{ getStatusLabel(currentTask.status) }}
            </el-tag>
            <span v-if="currentTask" class="report-updated">{{ formatRelativeTime(currentTask.updated_at) }}更新</span>
          </div>
        </div>
      </template>

      <div v-loading="loading" class="report-body">
        <div v-if="currentReport" class="markdown-body" v-html="renderedReport"></div>
        <el-empty v-else description="这条研究记录暂时还没有可阅读的完整报告。" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'
import { useDeepResearchStore } from '@/stores/deepresearch'
import type { DeepResearchStatus } from '@/types/deepresearch'
import { formatRelativeTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const store = useDeepResearchStore()
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

const currentTask = computed(() => store.currentTask)
const currentReport = computed(() => store.currentReport)
const loading = computed(() => store.actionLoading)
const renderedReport = computed(() => currentReport.value ? md.render(currentReport.value.report_markdown) : '')
const taskId = computed(() => Number(route.params.taskId))

const statusMap: Record<DeepResearchStatus, { label: string; type: '' | 'primary' | 'success' | 'warning' | 'danger' | 'info' }> = {
  pending: { label: '待启动', type: 'info' },
  drafting_analysts: { label: '生成分析师中', type: 'warning' },
  waiting_feedback: { label: '等待反馈', type: 'primary' },
  running_research: { label: '研究执行中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '执行失败', type: 'danger' }
}

const getStatusLabel = (status: DeepResearchStatus) => statusMap[status]?.label || status
const getStatusTagType = (status: DeepResearchStatus) => statusMap[status]?.type || 'info'

const goBack = () => {
  router.push({ name: 'DeepResearch' })
}

onMounted(async () => {
  if (!taskId.value) return
  await store.fetchTaskDetail(taskId.value)
  await store.loadReport(taskId.value)
})
</script>

<style scoped lang="scss">
.report-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.report-shell {
  border: none;
  border-radius: 24px;
  box-shadow: 0 16px 44px rgba(15, 35, 64, 0.07);
}

.report-shell :deep(.el-card__header) {
  border-bottom: 1px solid #edf1f7;
  padding: 24px 28px;
}

.report-shell :deep(.el-card__body) {
  padding: 28px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.report-kicker {
  margin-top: 12px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #1d6fd8;
}

.report-header h2 {
  margin: 10px 0 10px;
  font-size: 32px;
  line-height: 1.25;
  color: #18222f;
}

.report-header p {
  margin: 0;
  max-width: 760px;
  color: #677486;
  line-height: 1.8;
}

.report-header-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  min-width: 120px;
}

.report-updated {
  font-size: 12px;
  color: #7c8898;
}

.report-body {
  min-height: 420px;
}

.markdown-body {
  max-width: 920px;
  margin: 0 auto;
  color: #223042;
  line-height: 1.9;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  color: #152033;
  line-height: 1.35;
  margin-top: 1.6em;
  margin-bottom: 0.7em;
}

.markdown-body :deep(p),
.markdown-body :deep(li) {
  font-size: 15px;
}

.markdown-body :deep(pre) {
  overflow-x: auto;
  padding: 16px;
  border-radius: 16px;
  background: #0f172a;
}

.markdown-body :deep(code) {
  font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
}

@media (max-width: 768px) {
  .report-shell :deep(.el-card__header),
  .report-shell :deep(.el-card__body) {
    padding: 20px;
  }

  .report-header {
    flex-direction: column;
  }

  .report-header-side {
    align-items: flex-start;
  }

  .report-header h2 {
    font-size: 26px;
  }
}
</style>
