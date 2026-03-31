<template>
  <el-card class="panel-card" shadow="never">
    <template #header>
      <div class="panel-header">
        <div>
          <h3>分析师确认</h3>
          <p>检查本轮生成的分析师视角，满意后开始正式研究。</p>
        </div>
        <el-tag type="warning" effect="plain" round>Human in the Loop</el-tag>
      </div>
    </template>

    <div class="analyst-grid">
      <article
        v-for="analyst in analysts"
        :key="`${analyst.name}-${analyst.role}`"
        class="analyst-card"
      >
        <div class="analyst-top">
          <div>
            <h4>{{ analyst.name }}</h4>
            <p>{{ analyst.affiliation }}</p>
          </div>
          <el-tag type="primary" effect="plain">{{ analyst.role }}</el-tag>
        </div>
        <div class="analyst-description">{{ analyst.description }}</div>
      </article>
    </div>

    <el-form label-position="top" class="feedback-form">
      <el-form-item label="自然语言反馈">
        <el-input
          v-model="feedback"
          type="textarea"
          :rows="4"
          resize="none"
          maxlength="500"
          show-word-limit
          placeholder="例如：增加一位大学教授背景的分析师，强调学术研究和教学视角"
        />
      </el-form-item>
    </el-form>

    <div class="panel-actions">
      <el-button :loading="loading" @click="emit('approve')">确认并开始研究</el-button>
      <el-button
        type="primary"
        :loading="loading"
        :disabled="!feedback.trim()"
        @click="handleRegenerate"
      >
        根据反馈重新生成
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { DeepResearchAnalyst } from '@/types/deep-research'

interface Props {
  analysts: DeepResearchAnalyst[]
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  approve: []
  regenerate: [feedback: string]
}>()

const feedback = ref('')

const handleRegenerate = () => {
  const value = feedback.value.trim()
  if (!value) return
  emit('regenerate', value)
  feedback.value = ''
}
</script>

<style scoped lang="scss">
.panel-card {
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
    color: #6f8096;
    line-height: 1.6;
  }
}

.analyst-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.analyst-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid #e7edf5;
  background:
    radial-gradient(circle at top right, rgba(91, 140, 255, 0.12), transparent 32%),
    linear-gradient(180deg, #fcfdff 0%, #f7f9fc 100%);
}

.analyst-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;

  h4 {
    margin: 0;
    font-size: 18px;
    color: #17324d;
  }

  p {
    margin: 6px 0 0;
    color: #6f8096;
    font-size: 13px;
  }
}

.analyst-description {
  color: #324e6b;
  line-height: 1.7;
  font-size: 14px;
}

.feedback-form {
  margin-top: 20px;
}

.panel-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 900px) {
  .analyst-grid {
    grid-template-columns: 1fr;
  }

  .panel-actions {
    flex-direction: column-reverse;
  }
}
</style>
