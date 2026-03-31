<template>
  <el-card class="composer-card" shadow="never">
    <template #header>
      <div class="section-title">
        <span>新建研究任务</span>
        <el-tag size="small" effect="plain">Deep Research</el-tag>
      </div>
    </template>

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
          :rows="3"
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
          :rows="3"
          resize="none"
          placeholder="每行一条，例如：增加大学教授视角"
        />
      </el-form-item>

      <el-button
        type="primary"
        class="submit-btn"
        :loading="loading"
        @click="handleSubmit"
      >
        创建任务
      </el-button>
    </el-form>
  </el-card>
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
  resetForm()
}
</script>

<style scoped lang="scss">
.composer-card {
  border: none;
  background:
    radial-gradient(circle at top right, rgba(245, 157, 66, 0.16), transparent 35%),
    linear-gradient(180deg, #f7f5ef 0%, #f3f6fb 100%);

  :deep(.el-card__header) {
    border-bottom: none;
    padding-bottom: 0;
  }
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-weight: 700;
  color: #17324d;
}

.composer-form {
  display: flex;
  flex-direction: column;
}

.submit-btn {
  width: 100%;
  margin-top: 4px;
  height: 44px;
  border-radius: 12px;
}
</style>
