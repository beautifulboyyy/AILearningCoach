<template>
  <el-card class="composer-card" shadow="never">
    <div class="composer-shell">
      <div class="section-title">
        <div>
          <span>新建研究任务</span>
          <p>用主题和分析师数量快速启动一条新研究线。</p>
        </div>
        <el-tag size="small" effect="plain">Deep Research</el-tag>
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
    title="创建 Deep Research 任务"
    width="640px"
    destroy-on-close
    class="composer-dialog"
  >
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

      <el-form-item label="分析师数量" prop="max_analysts">
        <el-input-number
          v-model="form.max_analysts"
          :min="1"
          :max="5"
          :step="1"
          controls-position="right"
        />
      </el-form-item>

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

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-weight: 700;
  color: #17324d;

  p {
    margin: 6px 0 0;
    color: #6f8096;
    font-size: 13px;
    font-weight: 400;
  }
}

.composer-form {
  display: flex;
  flex-direction: column;
}

.launch-btn {
  min-width: 136px;
  height: 46px;
  border-radius: 14px;
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
  border-radius: 24px;
}

@media (max-width: 768px) {
  .composer-shell {
    flex-direction: column;
    align-items: stretch;
  }

  .launch-btn {
    width: 100%;
  }
}
</style>
