<template>
  <div class="generate-container">
    <el-card class="generate-card">
      <template #header>
        <div class="card-header">
          <el-icon :size="24" color="#409EFF"><Aim /></el-icon>
          <span>生成学习路径</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
        class="generate-form"
      >
        <el-form-item label="学习目标" prop="learning_goal">
          <el-select
            v-model="form.learning_goal"
            placeholder="请选择学习目标"
            style="width: 100%"
          >
            <el-option
              v-for="option in LEARNING_GOAL_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="每周可用时间" prop="available_hours_per_week">
          <el-input-number
            v-model="form.available_hours_per_week"
            :min="1"
            :max="50"
            style="width: 100%"
          />
          <span class="form-tip">小时/周</span>
        </el-form-item>

        <el-form-item label="当前水平">
          <el-radio-group v-model="form.current_level">
            <el-radio label="beginner">初学者</el-radio>
            <el-radio label="intermediate">中级</el-radio>
            <el-radio label="advanced">高级</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="特定主题">
          <el-input
            v-model="form.specific_topics"
            type="textarea"
            :rows="3"
            placeholder="输入您感兴趣的特定主题（可选）"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="generating"
            :disabled="generating"
            @click="handleGenerate"
          >
            {{ generating ? '正在生成中...' : '生成学习路径' }}
          </el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>

        <el-alert
          v-if="generating"
          title="生成中"
          type="info"
          description="学习路径生成需要60-90秒，请耐心等待..."
          :closable="false"
          show-icon
        />
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance } from 'element-plus'
import { Aim } from '@element-plus/icons-vue'
import { useLearningStore } from '@/stores/learning'
import { LEARNING_GOAL_OPTIONS } from '@/utils/constants'

const router = useRouter()
const learningStore = useLearningStore()

const formRef = ref<FormInstance>()
const form = reactive({
  learning_goal: 'job_hunting',
  available_hours_per_week: 10,
  current_level: 'beginner',
  specific_topics: ''
})

const rules = {
  learning_goal: [
    { required: true, message: '请选择学习目标', trigger: 'change' }
  ],
  available_hours_per_week: [
    { required: true, message: '请输入每周可用时间', trigger: 'blur' }
  ]
}

const generating = computed(() => learningStore.generating)

const handleGenerate = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      const data: any = {
        learning_goal: form.learning_goal,
        available_hours_per_week: form.available_hours_per_week
      }

      if (form.current_level) {
        data.current_level = form.current_level
      }

      if (form.specific_topics) {
        data.specific_topics = form.specific_topics.split('\n').filter(t => t.trim())
      }

      await learningStore.generatePath(data)
      ElMessage.success('学习路径生成成功！')
      router.push('/learning-path')
    } catch (error: any) {
      console.error('Generate path failed:', error)
      ElMessage.error(error.message || '生成失败，请重试')
    }
  })
}

const goBack = () => {
  router.back()
}
</script>

<style scoped lang="scss">
.generate-container {
  max-width: 800px;
  margin: 0 auto;
  
  .generate-card {
    .card-header {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 18px;
      font-weight: 500;
    }
    
    .generate-form {
      padding: 20px 0;
      
      .form-tip {
        margin-left: 12px;
        color: #909399;
        font-size: 14px;
      }
      
      .el-alert {
        margin-top: 20px;
      }
    }
  }
}
</style>
