<template>
  <el-card class="panel-card report-card" shadow="never">
    <template #header>
      <div class="panel-header">
        <div>
          <h3>最终报告</h3>
          <p>报告内容已从访谈与检索结果中提炼完成。</p>
        </div>
        <div class="anchor-actions">
          <el-button
            v-for="item in navItems"
            :key="item.anchor"
            text
            type="primary"
            @click="scrollTo(item.anchor)"
          >
            {{ item.label }}
          </el-button>
        </div>
      </div>
    </template>

    <div v-if="sections.length > 0" class="report-sections">
      <section
        v-for="section in sections"
        :key="section.anchor"
        :id="section.anchor"
        class="report-section"
      >
        <div class="section-label">{{ section.label }}</div>
        <h2>{{ section.title }}</h2>
        <div class="section-body markdown-body" v-html="section.html"></div>
      </section>
    </div>

    <el-empty v-else description="报告生成后会展示在这里" />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

interface Props {
  report?: string | null
}

const props = defineProps<Props>()

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true
})

const detectAnchor = (title: string) => {
  const normalized = title.trim().toLowerCase()
  if (normalized.includes('引言') || normalized.includes('introduction')) return 'report-introduction'
  if (normalized.includes('结论') || normalized.includes('conclusion')) return 'report-conclusion'
  if (
    normalized.includes('引用') ||
    normalized.includes('references') ||
    normalized.includes('sources')
  ) {
    return 'report-citations'
  }
  return 'report-content'
}

const sectionLabelMap: Record<string, string> = {
  'report-introduction': '引言',
  'report-content': '主体',
  'report-conclusion': '结论',
  'report-citations': '引用'
}

const sections = computed(() => {
  const report = (props.report || '').trim()
  if (!report) return []

  const chunks = report
    .split(/^##\s+/m)
    .map((chunk) => chunk.trim())
    .filter(Boolean)

  return chunks.map((chunk, index) => {
    const [titleLine, ...contentLines] = chunk.split('\n')
    const title = titleLine.trim()
    const baseAnchor = detectAnchor(title)
    const anchor = index === 0 && baseAnchor === 'report-content' ? 'report-introduction-0' : `${baseAnchor}-${index}`

    return {
      anchor,
      label: sectionLabelMap[baseAnchor] || '内容',
      title,
      html: md.render(contentLines.join('\n').trim())
    }
  })
})

const navItems = computed(() => {
  return sections.value.map((section) => ({
    anchor: section.anchor,
    label: section.label
  }))
})

const scrollTo = (anchor: string) => {
  const element = document.getElementById(anchor)
  if (!element) return
  element.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<style scoped lang="scss">
.report-card {
  border: none;
  background: #fffdfa;
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
  }
}

.anchor-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.report-sections {
  display: grid;
  gap: 20px;
}

.report-section {
  padding: 24px;
  border-radius: 18px;
  border: 1px solid #ece7dd;
  background: #fff;
  box-shadow: 0 10px 30px rgba(17, 43, 67, 0.04);

  h2 {
    margin: 10px 0 18px;
    color: #1a3652;
    font-size: 24px;
  }
}

.section-label {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f2f6fb;
  color: #65809b;
  font-size: 12px;
}

.section-body {
  color: #294767;
  line-height: 1.8;
}

.markdown-body :deep(p),
.markdown-body :deep(li) {
  line-height: 1.8;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
}

.markdown-body :deep(a) {
  color: #2f67d7;
  word-break: break-all;
}
</style>
