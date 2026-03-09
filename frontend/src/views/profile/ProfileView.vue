<template>
  <div class="profile-container">
    <el-row :gutter="24">
      <el-col :xs="24" :lg="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>用户画像</span>
              <el-button type="primary" @click="handleSave">保存</el-button>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            label-width="120px"
            v-loading="loading"
          >
            <el-form-item label="学习目标">
              <el-select v-model="form.learning_goal" style="width: 100%">
                <el-option
                  v-for="option in LEARNING_GOAL_OPTIONS"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </el-form-item>

            <el-divider content-position="left">背景信息</el-divider>

            <el-form-item label="学历">
              <el-input v-model="form.background.education" />
            </el-form-item>

            <el-form-item label="专业">
              <el-input v-model="form.background.major" />
            </el-form-item>

            <el-form-item label="工作经验">
              <el-input v-model="form.background.work_experience" />
            </el-form-item>

            <el-divider content-position="left">技术栈</el-divider>

            <el-form-item label="技术栈">
              <el-tag
                v-for="(tag, index) in form.tech_stack"
                :key="index"
                closable
                @close="removeTag(index)"
                style="margin-right: 8px"
              >
                {{ tag }}
              </el-tag>
              <el-input
                v-if="tagInputVisible"
                v-model="tagInputValue"
                ref="tagInputRef"
                size="small"
                style="width: 100px"
                @keyup.enter="addTag"
                @blur="addTag"
              />
              <el-button v-else size="small" @click="showTagInput">
                + 添加
              </el-button>
            </el-form-item>

            <el-divider content-position="left">学习风格</el-divider>

            <el-form-item label="学习风格">
              <el-radio-group v-model="form.learning_style">
                <el-radio
                  v-for="option in LEARNING_STYLE_OPTIONS"
                  :key="option.value"
                  :label="option.value"
                >
                  {{ option.label }}
                  <span style="color: #909399; font-size: 12px">
                    ({{ option.description }})
                  </span>
                </el-radio>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card>
          <template #header>学习统计</template>
          <div class="stats" v-loading="statsLoading">
            <div class="stat-item">
              <div class="stat-label">总体进度</div>
              <el-progress
                type="circle"
                :percentage="Math.round(progressStats.overall_completion || 0)"
                :color="progressColors"
              />
            </div>
            <div class="stat-details">
              <div class="detail-row">
                <span class="label">已完成模块</span>
                <span class="value">{{ progressStats.completed_modules || 0 }}</span>
              </div>
              <div class="detail-row">
                <span class="label">进行中模块</span>
                <span class="value">{{ progressStats.in_progress_modules || 0 }}</span>
              </div>
              <div class="detail-row">
                <span class="label">总学习时长</span>
                <span class="value">{{ formatNumber(progressStats.total_study_hours || 0, 1) }}h</span>
              </div>
              <div class="detail-row" v-if="progressStats.current_module">
                <span class="label">当前模块</span>
                <span class="value highlight">{{ progressStats.current_module }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { profileApi, progressApi } from '@/api'
import { LEARNING_GOAL_OPTIONS, LEARNING_STYLE_OPTIONS } from '@/utils/constants'
import { formatNumber } from '@/utils/format'
import type { ProgressStats } from '@/types/progress'

const loading = ref(false)
const statsLoading = ref(false)
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref()

const form = reactive({
  learning_goal: 'job_hunting',
  background: {
    education: '',
    major: '',
    work_experience: ''
  },
  tech_stack: [] as string[],
  learning_style: 'project_driven'
})

const progressStats = ref<Partial<ProgressStats>>({})

// 进度条颜色配置
const progressColors = [
  { color: '#F56C6C', percentage: 20 },
  { color: '#E6A23C', percentage: 40 },
  { color: '#409EFF', percentage: 60 },
  { color: '#67C23A', percentage: 80 },
  { color: '#6FCF97', percentage: 100 }
]

const fetchProfile = async () => {
  loading.value = true
  try {
    const data = await profileApi.getProfile()
    // 正确处理嵌套对象
    form.learning_goal = data.learning_goal || 'systematic_learning'
    form.learning_style = data.learning_style || 'project_driven'
    form.tech_stack = data.tech_stack || []

    // 深度合并 background 对象
    if (data.background) {
      form.background.education = data.background.education || ''
      form.background.major = data.background.major || ''
      form.background.work_experience = data.background.work_experience || ''
    }
  } catch (error) {
    console.error('Failed to fetch profile:', error)
  } finally {
    loading.value = false
  }
}

const fetchProgressStats = async () => {
  statsLoading.value = true
  try {
    progressStats.value = await progressApi.getStats()
  } catch (error) {
    console.error('Failed to fetch progress stats:', error)
  } finally {
    statsLoading.value = false
  }
}

const handleSave = async () => {
  try {
    await profileApi.updateProfile(form)
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const showTagInput = () => {
  tagInputVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

const addTag = () => {
  if (tagInputValue.value) {
    form.tech_stack.push(tagInputValue.value)
    tagInputValue.value = ''
  }
  tagInputVisible.value = false
}

const removeTag = (index: number) => {
  form.tech_stack.splice(index, 1)
}

onMounted(() => {
  fetchProfile()
  fetchProgressStats()
})
</script>

<style scoped lang="scss">
.profile-container {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stats {
    text-align: center;
    padding: 20px;

    .stat-item {
      .stat-label {
        margin-bottom: 16px;
        font-size: 14px;
        color: #909399;
      }
    }

    .stat-details {
      margin-top: 24px;
      text-align: left;
      border-top: 1px solid #EBEEF5;
      padding-top: 16px;

      .detail-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px dashed #EBEEF5;

        &:last-child {
          border-bottom: none;
        }

        .label {
          font-size: 13px;
          color: #909399;
        }

        .value {
          font-size: 14px;
          font-weight: 500;
          color: #303133;

          &.highlight {
            color: #409EFF;
          }
        }
      }
    }
  }
}
</style>
