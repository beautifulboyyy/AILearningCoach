<template>
  <div class="deepresearch-page">
    <section class="research-hero">
      <div class="hero-copy">
        <div class="hero-kicker">Deep Research</div>
        <h2>把研究任务从一次对话，升级成可追踪、可反馈、可沉淀的研究工作流。</h2>
        <p>
          从选题、分析师草案、多轮反馈到最终报告，整条链路都保存在这里。这里更像一个长期研究工作台，而不是一次性问答窗口。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" :icon="Plus" @click="showCreateDialog = true">
            发起研究
          </el-button>
          <el-button size="large" @click="handleRefresh">刷新列表</el-button>
        </div>
      </div>

      <div class="hero-metrics">
        <div class="metric-card">
          <div class="metric-label">研究记录</div>
          <div class="metric-value">{{ tasks.length }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">进行中</div>
          <div class="metric-value">{{ activeCount }}</div>
        </div>
        <div class="metric-card accent">
          <div class="metric-label">当前轮询</div>
          <div class="metric-value">{{ polling ? '进行中' : '空闲' }}</div>
        </div>
      </div>
    </section>

    <el-row :gutter="24" class="research-layout">
      <el-col :xs="24" :lg="8" :xl="7">
        <el-card class="history-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <div>
                <div class="panel-title">研究历史</div>
                <div class="panel-subtitle">选择一条记录继续推进，或者查看已完成的研究成果。</div>
              </div>
              <el-tag type="info" effect="plain">{{ tasks.length }}</el-tag>
            </div>
          </template>

          <div v-loading="loading" class="history-list">
            <button
              v-for="task in tasks"
              :key="task.id"
              type="button"
              class="history-item"
              :class="{ active: currentTask?.id === task.id }"
              @click="selectTask(task.id)"
            >
              <div class="history-main">
                <div class="history-topic">{{ task.topic }}</div>
                <el-tag size="small" :type="getStatusTagType(task.status)" effect="light">
                  {{ getStatusLabel(task.status) }}
                </el-tag>
              </div>
              <div class="history-meta">
                <span>{{ formatRelativeTime(task.updated_at) }}</span>
              </div>
              <div class="history-progress">
                <el-progress
                  :stroke-width="6"
                  :show-text="false"
                  :percentage="task.progress_percent"
                  :status="task.status === 'failed' ? 'exception' : undefined"
                />
                <span>{{ task.progress_message || '等待开始' }}</span>
              </div>
            </button>

            <el-empty v-if="!loading && tasks.length === 0" description="还没有研究记录，先创建一个主题吧。" />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16" :xl="17">
        <div v-if="currentTask" class="detail-stack">
          <el-card class="detail-card overview-card" shadow="never">
            <div class="overview-header">
              <div class="overview-copy">
                <div class="status-row">
                  <el-tag effect="dark" :type="getStatusTagType(currentTask.status)">
                    {{ getStatusLabel(currentTask.status) }}
                  </el-tag>
                  <span class="phase-text">{{ getPhaseLabel(currentTask.phase) }}</span>
                </div>
                <h3>{{ currentTask.topic }}</h3>
                <p>{{ currentTask.requirements || '没有补充要求，系统将根据主题自动组织研究分析师。' }}</p>
              </div>

              <div class="overview-actions">
                <el-button
                  v-if="currentTask.report_available"
                  type="primary"
                  :icon="Document"
                  @click="goToReport(currentTask.id)"
                >
                  查看完整报告
                </el-button>
                <el-button
                  type="danger"
                  plain
                  :icon="Delete"
                  @click="handleDelete(currentTask.id)"
                >
                  删除
                </el-button>
              </div>
            </div>

            <div class="progress-panel">
              <div class="progress-label-row">
                <span>{{ currentTask.progress_message || '等待处理' }}</span>
                <span>{{ currentTask.progress_percent }}%</span>
              </div>
              <el-progress
                :percentage="currentTask.progress_percent"
                :status="currentTask.status === 'failed' ? 'exception' : undefined"
                :stroke-width="10"
              />
              <div class="context-strip">
                <span class="context-chip">{{ currentTask.analysts.length }} 位分析师已就位</span>
                <span class="context-chip">{{ formatRelativeTime(currentTask.updated_at) }}更新</span>
                <span v-if="currentTask.report_available" class="context-chip success">研究报告已生成</span>
                <span
                  v-else-if="currentTask.status === 'waiting_feedback' && currentTask.remaining_feedback_rounds > 0"
                  class="context-chip accent"
                >
                  还可以继续补充反馈
                </span>
              </div>
              <p v-if="currentTask.error_message" class="error-tip">{{ currentTask.error_message }}</p>
            </div>
          </el-card>

          <el-card class="detail-card workspace-card" shadow="never">
            <el-tabs v-model="activeTab" class="workspace-tabs">
              <el-tab-pane label="分析师方案" name="analysts">
                <div class="workspace-head">
                  <div>
                    <div class="workspace-title">当前分析师团队</div>
                    <div class="workspace-subtitle">这里展示的是系统当前用于研究的分析师方案。</div>
                  </div>
                  <el-tag type="success" effect="plain">{{ currentTask.analysts.length }} 位</el-tag>
                </div>

                <div class="analyst-list">
                  <div
                    v-for="(analyst, index) in currentTask.analysts"
                    :key="`${analyst.name}-${index}`"
                    class="analyst-card"
                  >
                    <div class="analyst-top">
                      <div>
                        <div class="analyst-name">{{ analyst.name }}</div>
                        <div class="analyst-role">{{ analyst.role }}</div>
                      </div>
                      <el-tag size="small" effect="light">{{ analyst.affiliation }}</el-tag>
                    </div>
                    <p>{{ analyst.description }}</p>
                  </div>

                  <el-empty v-if="currentTask.analysts.length === 0" description="分析师还在生成中，稍后刷新。" />
                </div>
              </el-tab-pane>

              <el-tab-pane v-if="showActionsTab" label="推进动作" name="actions">
                <div class="workspace-head">
                  <div>
                    <div class="workspace-title">继续推进这项研究</div>
                    <div class="workspace-subtitle">如果你想继续打磨分析师阵容，先反馈；如果已经满意，就直接启动正式研究。</div>
                  </div>
                </div>

                <div class="actions-layout">
                  <section class="action-block">
                    <div class="action-block-title">正式启动研究</div>
                    <p class="action-block-copy">
                      将使用当前展示的分析师团队，进入检索、访谈、整合与报告生成阶段。
                    </p>
                    <el-button
                      type="success"
                      :disabled="!canStartResearch"
                      :loading="actionLoading"
                      @click="handleStartResearch"
                    >
                      开始正式研究
                    </el-button>
                  </section>

                  <section class="action-block">
                    <div class="action-block-title">继续调整分析师</div>
                    <p class="action-block-copy">
                      通过自然语言补充你想加强的视角，系统会据此重生成当前方案。
                    </p>
                    <el-input
                      v-model="feedbackText"
                      type="textarea"
                      :rows="5"
                      resize="none"
                      maxlength="2000"
                      show-word-limit
                      placeholder="例如：增加偏工程架构和产品落地的视角，减少纯理论角色。"
                    />
                    <div class="feedback-footer">
                      <span v-if="currentTask.status !== 'waiting_feedback'" class="muted-tip">
                        当前阶段暂时不能提交反馈，请等待分析师生成完成。
                      </span>
                      <span
                        v-else-if="currentTask.remaining_feedback_rounds <= 0"
                        class="muted-tip"
                      >
                        当前任务的反馈次数已用尽，可以直接启动研究。
                      </span>
                      <span v-else class="muted-tip">
                        继续反馈后，系统会基于你的意见重生成当前团队。
                      </span>

                      <el-button
                        type="primary"
                        :disabled="!canSubmitFeedback"
                        :loading="actionLoading"
                        @click="handleSubmitFeedback"
                      >
                        提交反馈并重生成
                      </el-button>
                    </div>
                  </section>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </div>

        <el-card v-else class="detail-card empty-stage" shadow="never">
          <el-empty description="从左侧选择一条研究记录，或者直接发起一个新的 DeepResearch 任务。" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showCreateDialog" title="发起新的 Deep Research" width="640px">
      <el-form label-position="top">
        <el-form-item label="研究主题" required>
          <el-input
            v-model="createForm.topic"
            maxlength="500"
            show-word-limit
            placeholder="例如：如何设计一个面向大学生的 AI Learning Coach"
          />
        </el-form-item>
        <el-form-item label="补充要求">
          <el-input
            v-model="createForm.requirements"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
            resize="none"
            placeholder="告诉系统你更看重哪些视角，例如教学设计、工程实现、商业化路径。"
          />
        </el-form-item>
        <el-form-item label="分析师数量">
          <el-slider v-model="createForm.max_analysts" :min="1" :max="8" show-input />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="actionLoading" :disabled="!createForm.topic.trim()" @click="handleCreateTask">
          创建任务
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Document, Plus } from '@element-plus/icons-vue'
import { useDeepResearchStore } from '@/stores/deepresearch'
import type { DeepResearchPhase, DeepResearchStatus } from '@/types/deepresearch'
import { formatRelativeTime } from '@/utils/format'

const router = useRouter()
const store = useDeepResearchStore()

const showCreateDialog = ref(false)
const feedbackText = ref('')
const activeTab = ref<'analysts' | 'actions'>('analysts')

const createForm = reactive({
  topic: '',
  requirements: '',
  max_analysts: 4
})

const tasks = computed(() => store.sortedTasks)
const currentTask = computed(() => store.currentTask)
const loading = computed(() => store.loading)
const actionLoading = computed(() => store.actionLoading)
const polling = computed(() => store.polling)
const activeCount = computed(() => tasks.value.filter((task) => ['drafting_analysts', 'running_research'].includes(task.status)).length)

const showActionsTab = computed(() =>
  Boolean(currentTask.value) && !currentTask.value?.report_available && currentTask.value?.status !== 'completed'
)

const canSubmitFeedback = computed(() =>
  currentTask.value?.status === 'waiting_feedback' &&
  currentTask.value.remaining_feedback_rounds > 0 &&
  feedbackText.value.trim().length > 0
)

const canStartResearch = computed(() =>
  currentTask.value?.status === 'waiting_feedback' &&
  currentTask.value.current_revision > 0 &&
  currentTask.value.analysts.length > 0
)

const statusMap: Record<DeepResearchStatus, { label: string; type: '' | 'primary' | 'success' | 'warning' | 'danger' | 'info' }> = {
  pending: { label: '待启动', type: 'info' },
  drafting_analysts: { label: '生成分析师中', type: 'warning' },
  waiting_feedback: { label: '等待反馈', type: 'primary' },
  running_research: { label: '研究执行中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '执行失败', type: 'danger' }
}

const phaseMap: Record<string, string> = {
  analyst_generation: '分析师生成阶段',
  analyst_feedback: '分析师确认阶段',
  research_execution: '正式研究阶段',
  report_finalization: '报告收束阶段'
}

const getStatusLabel = (status: DeepResearchStatus) => statusMap[status]?.label || status
const getStatusTagType = (status: DeepResearchStatus) => statusMap[status]?.type || 'info'
const getPhaseLabel = (phase: DeepResearchPhase) => phase ? phaseMap[phase] || phase : '等待阶段推进'

const resetCreateForm = () => {
  createForm.topic = ''
  createForm.requirements = ''
  createForm.max_analysts = 4
}

const syncActiveTab = () => {
  if (!showActionsTab.value) {
    activeTab.value = 'analysts'
  }
}

const handleRefresh = async () => {
  await store.fetchTasks()
  if (currentTask.value?.id) {
    const detail = await store.fetchTaskDetail(currentTask.value.id)
    if (['drafting_analysts', 'running_research'].includes(detail.status)) {
      store.startPolling(detail.id)
    }
  }
  syncActiveTab()
}

const selectTask = async (taskId: number) => {
  feedbackText.value = ''
  const detail = await store.fetchTaskDetail(taskId)
  if (['drafting_analysts', 'running_research'].includes(detail.status)) {
    store.startPolling(taskId)
  } else {
    store.stopPolling()
  }
  syncActiveTab()
}

const handleCreateTask = async () => {
  try {
    const created = await store.createTask({
      topic: createForm.topic.trim(),
      requirements: createForm.requirements.trim() || undefined,
      max_analysts: createForm.max_analysts
    })
    showCreateDialog.value = false
    resetCreateForm()
    activeTab.value = 'analysts'
    ElMessage.success('Deep Research 任务已创建')
    store.startPolling(created.id)
  } catch {
    // handled globally
  }
}

const handleSubmitFeedback = async () => {
  if (!currentTask.value) return
  try {
    await store.submitFeedback(currentTask.value.id, {
      feedback: feedbackText.value.trim()
    })
    feedbackText.value = ''
    activeTab.value = 'analysts'
    ElMessage.success('反馈已提交，正在重生成分析师方案')
    store.startPolling(currentTask.value.id)
  } catch {
    // handled globally
  }
}

const handleStartResearch = async () => {
  if (!currentTask.value) return
  try {
    await store.startResearch(currentTask.value.id, {
      selected_revision: currentTask.value.current_revision
    })
    ElMessage.success('已启动正式研究')
    store.startPolling(currentTask.value.id)
  } catch {
    // handled globally
  }
}

const goToReport = (taskId: number) => {
  router.push({ name: 'DeepResearchReport', params: { taskId } })
}

const handleDelete = async (taskId: number) => {
  try {
    await ElMessageBox.confirm(
      '删除后会同时清理该研究任务的分析师版本和报告数据，且不可恢复。确定继续吗？',
      '删除 Deep Research',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )

    await store.deleteTask(taskId)
    store.stopPolling()
    feedbackText.value = ''
    ElMessage.success('研究记录已删除')
  } catch (error: any) {
    if (error === 'cancel' || error === 'close') return
  }
}

watch(showCreateDialog, (visible) => {
  if (!visible) resetCreateForm()
})

watch(currentTask, () => {
  syncActiveTab()
})

onMounted(async () => {
  await store.fetchTasks()
  const firstTask = store.activeTask?.id || store.sortedTasks[0]?.id
  if (firstTask) {
    await selectTask(firstTask)
  }
})

onBeforeUnmount(() => {
  store.stopPolling()
})
</script>

<style scoped lang="scss">
.deepresearch-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.research-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 0.9fr);
  gap: 24px;
  padding: 28px;
  border-radius: 20px;
  background:
    radial-gradient(circle at top left, rgba(64, 158, 255, 0.18), transparent 38%),
    radial-gradient(circle at right center, rgba(103, 194, 58, 0.12), transparent 36%),
    linear-gradient(135deg, #f7fbff 0%, #eef4ff 52%, #fbfcff 100%);
  border: 1px solid rgba(64, 158, 255, 0.16);
}

.hero-copy h2 {
  margin: 8px 0 14px;
  font-size: 30px;
  line-height: 1.25;
  color: #18222f;
  max-width: 760px;
}

.hero-copy p {
  max-width: 760px;
  font-size: 15px;
  line-height: 1.8;
  color: #5f6b7a;
}

.hero-kicker {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(64, 158, 255, 0.1);
  color: #1d6fd8;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  flex-wrap: wrap;
}

.hero-metrics {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.metric-card {
  padding: 18px 18px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(24, 34, 47, 0.06);
  box-shadow: 0 18px 40px rgba(52, 98, 160, 0.08);
}

.metric-card.accent {
  background: linear-gradient(135deg, #1b67d8 0%, #3e8dff 100%);
}

.metric-card.accent .metric-label,
.metric-card.accent .metric-value {
  color: #fff;
}

.metric-label {
  font-size: 13px;
  color: #708093;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #18222f;
}

.research-layout {
  min-height: calc(100vh - 260px);
}

.detail-stack {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-card,
.history-card {
  border: none;
  border-radius: 20px;
  box-shadow: 0 12px 34px rgba(15, 35, 64, 0.06);
}

.detail-card :deep(.el-card__header),
.history-card :deep(.el-card__header) {
  border-bottom: 1px solid #edf1f7;
  padding: 20px 22px;
}

.detail-card :deep(.el-card__body),
.history-card :deep(.el-card__body) {
  padding: 22px;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
}

.panel-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #7a8797;
  line-height: 1.6;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 860px;
  overflow-y: auto;
}

.history-item {
  width: 100%;
  text-align: left;
  border: 1px solid #edf1f7;
  background: #fff;
  border-radius: 18px;
  padding: 16px;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.history-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(19, 56, 112, 0.08);
  border-color: rgba(64, 158, 255, 0.25);
}

.history-item.active {
  border-color: rgba(64, 158, 255, 0.45);
  box-shadow: 0 16px 30px rgba(30, 99, 197, 0.14);
}

.history-main,
.history-meta,
.history-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.history-main {
  margin-bottom: 10px;
}

.history-topic {
  font-size: 15px;
  font-weight: 700;
  color: #18222f;
  line-height: 1.5;
}

.history-meta {
  margin-bottom: 12px;
  font-size: 12px;
  color: #7a8797;
}

.history-progress {
  align-items: flex-start;
  flex-direction: column;
}

.history-progress span {
  font-size: 12px;
  color: #657387;
}

.overview-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.overview-copy {
  flex: 1;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.phase-text {
  font-size: 13px;
  color: #708093;
}

.overview-header h3 {
  margin: 0 0 10px;
  font-size: 28px;
  line-height: 1.3;
  color: #18222f;
}

.overview-header p {
  margin: 0;
  max-width: 760px;
  font-size: 14px;
  line-height: 1.8;
  color: #667384;
}

.overview-actions {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.progress-panel {
  margin-top: 24px;
  padding: 20px;
  border-radius: 18px;
  background: linear-gradient(180deg, #f9fbff 0%, #f6f8fc 100%);
  border: 1px solid #edf2fb;
}

.progress-label-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #516172;
}

.context-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.context-chip {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #e6ecf5;
  font-size: 12px;
  color: #5f6f82;
}

.context-chip.accent {
  color: #1d6fd8;
  border-color: rgba(64, 158, 255, 0.22);
  background: rgba(64, 158, 255, 0.08);
}

.context-chip.success {
  color: #1f8b4c;
  border-color: rgba(103, 194, 58, 0.2);
  background: rgba(103, 194, 58, 0.1);
}

.error-tip {
  margin: 14px 0 0;
  color: #d14343;
  font-size: 13px;
  line-height: 1.6;
}

.workspace-card :deep(.el-card__body) {
  padding-top: 16px;
}

.workspace-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.workspace-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.workspace-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.workspace-subtitle {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.7;
  color: #77869a;
}

.analyst-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.analyst-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid #ebf0f6;
  background:
    radial-gradient(circle at top right, rgba(64, 158, 255, 0.08), transparent 28%),
    #fff;
  min-height: 190px;
}

.analyst-top {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.analyst-name {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
}

.analyst-role {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.6;
  color: #637385;
}

.analyst-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: #4d5d6f;
}

.actions-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.action-block {
  padding: 20px;
  border-radius: 18px;
  border: 1px solid #ebf0f6;
  background: linear-gradient(180deg, #ffffff 0%, #fafcff 100%);
}

.action-block-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
}

.action-block-copy {
  margin: 10px 0 18px;
  font-size: 14px;
  line-height: 1.8;
  color: #667384;
}

.feedback-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 14px;
}

.muted-tip {
  font-size: 12px;
  line-height: 1.7;
  color: #7a8797;
}

.empty-stage {
  min-height: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 1280px) {
  .research-hero {
    grid-template-columns: 1fr;
  }

  .hero-metrics {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .analyst-list,
  .actions-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .research-hero {
    padding: 22px;
  }

  .hero-copy h2 {
    font-size: 24px;
  }

  .hero-metrics {
    grid-template-columns: 1fr;
  }

  .overview-header,
  .workspace-head,
  .feedback-footer {
    flex-direction: column;
  }

  .overview-actions {
    width: 100%;
  }

  .overview-actions :deep(.el-button) {
    flex: 1;
  }

  .analyst-card,
  .action-block {
    padding: 16px;
  }
}
</style>
