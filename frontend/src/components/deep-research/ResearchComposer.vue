<template>
  <el-card class="composer-card" shadow="never">
    <div class="composer-shell">
      <div class="composer-copy">
        <div class="composer-eyebrow">
          <el-tag size="small" effect="plain">Deep Research</el-tag>
        </div>
        <h3>新建研究任务</h3>
        <p>用主题和分析师数量快速启动一条新研究线。</p>
      </div>
      <el-button
        type="primary"
        class="launch-btn"
        @click="dialogVisible = true"
      >
        新建任务
      </el-button>
    </div>
  </el-card>

  <el-dialog
    v-model="dialogVisible"
    width="560px"
    align-center
    :close-on-click-modal="false"
    destroy-on-close
    class="composer-dialog"
  >
    <template #header>
      <div class="dialog-header">
        <div>
          <h3>创建 Deep Research 任务</h3>
          <p>先定义主题和分析师规模，再进入分析师确认与正式研究流程。</p>
        </div>
      </div>
    </template>

    <div class="dialog-body">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        class="composer-form"
      >
        <el-form-item label="研究主题" prop="topic">
          <el-input
            v-model="form.topic"
            type="textarea"
            :rows="4"
            resize="none"
            maxlength="500"
            show-word-limit
            placeholder="例如：Agent 在企业软件中的应用与趋势"
          />
        </el-form-item>

        <div class="form-row">
          <el-form-item label="分析师数量" prop="max_analysts" class="count-item">
            <el-input-number
              v-model="form.max_analysts"
              :min="1"
              :max="5"
              :step="1"
              controls-position="right"
            />
          </el-form-item>

          <div class="count-hint">
            <span>建议范围</span>
            <p>建议使用 2 到 4 位分析师，覆盖视角更平衡。</p>
          </div>
        </div>

        <el-form-item label="分析师偏好（可选）">
          <el-input
            v-model="directionInput"
            type="textarea"
            :rows="4"
            resize="none"
            placeholder="每行一条，例如：增加大学教授视角"
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          class="submit-btn"
          :loading="loading"
          @click="handleSubmit"
        >
          创建任务
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { StartDeepResearchRequest } from '@/types/deepResearch'

interface Props {
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  submit: [payload: StartDeepResearchRequest]
}>()

const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const directionInput = ref('')
const form = reactive<StartDeepResearchRequest>({
  topic: '',
  max_analysts: 3,
  analyst_directions: []
})

const rules: FormRules<typeof form> = {
  topic: [
    { required: true, message: '请输入研究主题', trigger: 'blur' },
    { min: 1, max: 500, message: '主题长度需要在 1 到 500 个字符之间', trigger: 'blur' }
  ],
  max_analysts: [{ required: true, message: '请选择分析师数量', trigger: 'change' }]
}

const resetForm = () => {
  form.topic = ''
  form.max_analysts = 3
  directionInput.value = ''
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  const directions = directionInput.value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)

  emit('submit', {
    topic: form.topic.trim(),
    max_analysts: form.max_analysts,
    analyst_directions: directions.length > 0 ? directions : undefined
  })
  dialogVisible.value = false
  resetForm()
}
</script>

<style scoped lang="scss">
.composer-card {
  border: none;
  background:
    radial-gradient(circle at top right, rgba(245, 157, 66, 0.16), transparent 35%),
    linear-gradient(180deg, #f7f5ef 0%, #f3f6fb 100%);
  box-shadow: 0 18px 40px rgba(19, 42, 66, 0.08);

  :deep(.el-card__body) {
    padding: 22px;
  }
}

.composer-shell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.composer-copy {
  flex: 1;
  min-width: 0;

  h3 {
    margin: 10px 0 6px;
    color: #17324d;
    font-size: 24px;
    line-height: 1.2;
  }

  p {
    margin: 0;
    color: #6f8096;
    font-size: 14px;
    line-height: 1.7;
    font-weight: 400;
    max-width: 360px;
  }
}

.composer-eyebrow {
  display: flex;
  align-items: center;
}

.composer-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.launch-btn {
  min-width: 136px;
  height: 46px;
  border-radius: 14px;
  padding-inline: 26px;
  flex-shrink: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.submit-btn {
  height: 44px;
  border-radius: 12px;
}

.composer-dialog :deep(.el-dialog) {
  border-radius: 22px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 28px 80px rgba(20, 44, 70, 0.24);
}

.composer-dialog :deep(.el-overlay-dialog) {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.composer-dialog :deep(.el-overlay) {
  background: rgba(15, 27, 43, 0.46);
  backdrop-filter: blur(8px);
}

.composer-dialog :deep(.el-dialog__header) {
  padding: 22px 24px 0;
}

.composer-dialog :deep(.el-dialog__body) {
  padding: 14px 24px 8px;
}

.composer-dialog :deep(.el-dialog__footer) {
  padding: 0 24px 22px;
}

.composer-dialog :deep(.el-dialog__headerbtn) {
  top: 18px;
  right: 18px;
}

.dialog-header h3 {
  margin: 0;
  color: #17324d;
  font-size: 26px;
  line-height: 1.18;
}

.dialog-header p {
  margin: 8px 0 0;
  color: #6f8096;
  line-height: 1.6;
  font-size: 14px;
}

.dialog-body {
  display: grid;
  gap: 14px;
}

.form-row {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.count-item {
  margin-bottom: 0;
}

.count-hint {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(245, 248, 252, 0.92);
  border: 1px solid rgba(22, 49, 76, 0.08);

  span {
    display: block;
    margin-bottom: 4px;
    color: #70839a;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  p {
    margin: 0;
    color: #43617f;
    line-height: 1.6;
    font-size: 13px;
  }
}

.composer-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.composer-form :deep(.el-textarea__inner) {
  min-height: 112px !important;
  border-radius: 14px;
}

.composer-form :deep(.el-input-number) {
  width: 100%;
  max-width: 168px;
}

@media (max-width: 768px) {
  .composer-shell {
    align-items: flex-end;
    flex-wrap: wrap;
  }

  .composer-copy {
    width: 100%;

    p {
      max-width: none;
    }
  }

  .launch-btn {
    width: 100%;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .dialog-header h3 {
    font-size: 22px;
  }
}
</style>
