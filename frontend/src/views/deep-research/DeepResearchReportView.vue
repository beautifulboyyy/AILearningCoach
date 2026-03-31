<template>
  <div class="report-page">
    <div class="report-toolbar">
      <el-button text @click="goBack">返回工作台</el-button>
      <div class="toolbar-spacer"></div>
      <el-button
        v-if="task?.thread_id"
        type="primary"
        plain
        @click="goWorkbenchTask"
      >
        查看任务详情
      </el-button>
    </div>

    <el-skeleton v-if="loading" :rows="12" animated class="report-skeleton" />

    <el-empty
      v-else-if="!task"
      description="未找到对应的研究任务"
    />

    <el-empty
      v-else-if="!task.final_report"
      description="该任务尚未生成完整报告"
    />

    <ReportViewer
      v-else
      :report="task.final_report"
      :title="task.topic"
      subtitle="完整研究报告已生成，建议在此以连续文档形式阅读。"
      :status-text="statusLabel"
      :analysts-count="task.max_analysts"
      :updated-at="task.updated_at"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ReportViewer from '@/components/deep-research/ReportViewer.vue'
import { useDeepResearchStore } from '@/stores/deep-research'

const route = useRoute()
const router = useRouter()
const store = useDeepResearchStore()

const loading = ref(false)
const threadId = computed(() => String(route.params.threadId || ''))
const task = computed(() => store.currentTask)

const statusLabelMap = {
  pending: '待生成分析师',
  awaiting_feedback: '等待人工确认',
  running: '研究进行中',
  completed: '报告已完成',
  failed: '执行失败'
}

const statusLabel = computed(() => {
  const status = task.value?.status
  return status ? statusLabelMap[status] || status : '未知状态'
})

const loadTask = async () => {
  if (!threadId.value) return
  loading.value = true
  try {
    await store.selectTask(threadId.value)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/deep-research')
}

const goWorkbenchTask = () => {
  router.push({
    path: '/deep-research',
    query: {
      threadId: threadId.value
    }
  })
}

onMounted(async () => {
  await loadTask()
})
</script>

<style scoped lang="scss">
.report-page {
  min-height: calc(100vh - 108px);
  padding-bottom: 24px;
  background:
    radial-gradient(circle at top left, rgba(91, 140, 255, 0.08), transparent 20%),
    linear-gradient(180deg, #f1f5fb 0%, #eceff5 100%);
}

.report-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0 6px;
}

.toolbar-spacer {
  flex: 1;
}

.report-skeleton {
  padding: 24px;
  background: #fff;
  border-radius: 24px;
}
</style>
