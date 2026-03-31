<template>
  <div class="deep-research-page">
    <aside class="rail-column">
      <ResearchComposer :loading="store.createLoading" @submit="handleCreateTask" />
      <TaskRail
        :tasks="store.sortedTasks"
        :selected-task-id="store.selectedTaskId"
        :loading="store.listLoading"
        @select="handleSelectTask"
        @delete="handleDeleteTask"
      />
    </aside>

    <main class="workspace-column">
      <div v-if="store.currentTask" class="workspace-stack">
        <TaskHeader :task="store.currentTask" :progress="store.progress" />

        <el-card v-if="store.currentTask.status === 'pending'" class="pending-card" shadow="never">
          <div class="pending-state">
            <div>
              <div class="pending-badge">Step 1</div>
              <h3>先生成分析师，再进入研究流程</h3>
              <p>
                当前任务已经创建完成。下一步会根据主题与分析师数量，生成本轮专家团队并等待你确认。
              </p>
            </div>
            <el-button
              type="primary"
              size="large"
              :loading="store.actionLoading"
              @click="handleGenerateAnalysts"
            >
              生成分析师
            </el-button>
          </div>
        </el-card>

        <AnalystReviewPanel
          v-else-if="store.currentTask.status === 'awaiting_feedback'"
          :analysts="store.currentTask.analysts || []"
          :loading="store.actionLoading"
          @approve="handleApprove"
          @regenerate="handleRegenerate"
        />

        <ResearchProgressPanel
          v-else-if="store.currentTask.status === 'running'"
          :progress="store.progress"
        />

        <el-card v-else-if="store.currentTask.status === 'failed'" class="failed-card" shadow="never">
          <div class="failed-state">
            <div class="failed-badge">Failed</div>
            <h3>任务执行失败</h3>
            <p>
              这条研究任务没有成功完成。按照当前后端策略，建议直接删除任务并重新创建一个新的任务继续。
            </p>
            <el-button
              type="danger"
              :loading="store.actionLoading"
              @click="handleDeleteTask(store.currentTask.thread_id)"
            >
              删除当前任务
            </el-button>
          </div>
        </el-card>

        <ReportViewer
          v-if="store.currentTask.status === 'completed' || !!store.currentTask.final_report"
          :report="store.currentTask.final_report"
        />
      </div>

      <el-card v-else class="empty-workspace" shadow="never">
        <div class="empty-state">
          <div class="empty-eyebrow">Research Cockpit</div>
          <h2>先创建一个 Deep Research 任务</h2>
          <p>
            左侧可以输入主题、分析师数量和可选方向。创建后，你就能在同一页面里完成分析师确认、查看运行进度和阅读最终报告。
          </p>
        </div>
      </el-card>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ResearchComposer from '@/components/deep-research/ResearchComposer.vue'
import TaskRail from '@/components/deep-research/TaskRail.vue'
import TaskHeader from '@/components/deep-research/TaskHeader.vue'
import AnalystReviewPanel from '@/components/deep-research/AnalystReviewPanel.vue'
import ResearchProgressPanel from '@/components/deep-research/ResearchProgressPanel.vue'
import ReportViewer from '@/components/deep-research/ReportViewer.vue'
import { useDeepResearchStore } from '@/stores/deepResearch'
import type { StartDeepResearchRequest } from '@/types/deepResearch'

const store = useDeepResearchStore()

const handleCreateTask = async (payload: StartDeepResearchRequest) => {
  try {
    const task = await store.createTask(payload)
    ElMessage.success('研究任务已创建')
    await store.selectTask(task.thread_id)
  } catch (error) {
    console.error(error)
  }
}

const handleSelectTask = async (threadId: string) => {
  try {
    await store.selectTask(threadId)
  } catch (error) {
    console.error(error)
  }
}

const handleDeleteTask = async (threadId: string) => {
  try {
    await ElMessageBox.confirm(
      '删除后无法恢复，且不会保留运行中的中间状态，确定继续吗？',
      '删除研究任务',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
    await store.deleteTask(threadId)
    ElMessage.success('任务已删除')
  } catch (error: any) {
    if (error === 'cancel' || error === 'close') return
    console.error(error)
  }
}

const handleGenerateAnalysts = async () => {
  try {
    await store.generateAnalysts()
    ElMessage.success('分析师已生成，请确认后继续')
  } catch (error) {
    console.error(error)
  }
}

const handleApprove = async () => {
  try {
    await store.approveTask()
    ElMessage.success('研究流程已完成')
  } catch (error) {
    console.error(error)
  }
}

const handleRegenerate = async (feedback: string) => {
  try {
    await store.regenerateAnalysts(feedback)
    ElMessage.success('已根据反馈重新生成分析师')
  } catch (error) {
    console.error(error)
  }
}

onMounted(async () => {
  await store.initialize()
})

onBeforeUnmount(() => {
  store.stopPolling()
})
</script>

<style scoped lang="scss">
.deep-research-page {
  --page-bg: #edf2f8;
  --ink-strong: #17324d;
  --ink-soft: #6f8096;

  min-height: calc(100vh - 108px);
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
  padding: 4px 0 8px;
  background:
    radial-gradient(circle at top right, rgba(91, 140, 255, 0.12), transparent 22%),
    linear-gradient(180deg, #f3f6fb 0%, var(--page-bg) 100%);
}

.rail-column,
.workspace-stack {
  display: grid;
  gap: 16px;
}

.workspace-column {
  min-width: 0;
}

.pending-card,
.failed-card,
.empty-workspace {
  border: none;
  background: #fff;
}

.pending-state,
.failed-state,
.empty-state {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
  padding: 8px;

  h2,
  h3 {
    margin: 0;
    color: var(--ink-strong);
  }

  p {
    margin: 0;
    max-width: 700px;
    color: var(--ink-soft);
    line-height: 1.8;
  }
}

.pending-state {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.pending-badge,
.failed-badge,
.empty-eyebrow {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f3f6fb;
  color: #5d7391;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.failed-badge {
  background: #fff1f0;
  color: #d34a4a;
}

@media (max-width: 1080px) {
  .deep-research-page {
    grid-template-columns: 1fr;
  }

  .pending-state {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
