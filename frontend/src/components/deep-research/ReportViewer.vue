<template>
  <div class="report-viewer">
    <div class="report-shell">
      <div class="report-head">
        <div class="report-head-main">
          <div class="report-kicker">Deep Research Report</div>
          <h1>{{ title }}</h1>
          <p>{{ subtitle }}</p>
        </div>

        <div class="report-meta">
          <div class="meta-item">
            <span>任务状态</span>
            <strong>{{ statusText }}</strong>
          </div>
          <div class="meta-item">
            <span>分析师数量</span>
            <strong>{{ analystsCount }}</strong>
          </div>
          <div class="meta-item">
            <span>最后更新</span>
            <strong>{{ updatedAtText }}</strong>
          </div>
        </div>
      </div>

      <div v-if="navItems.length > 0" class="report-nav">
        <button
          v-for="item in navItems"
          :key="item.anchor"
          type="button"
          class="nav-chip"
          @click="scrollTo(item.anchor)"
        >
          {{ item.label }}
        </button>
      </div>

      <div v-if="sections.length > 0" class="report-article">
        <section
          v-for="section in sections"
          :key="section.anchor"
          :id="section.anchor"
          class="article-section"
        >
          <h2>{{ section.title }}</h2>
          <div
            v-if="section.kind === 'citations'"
            class="citation-section"
          >
            <div class="citation-summary">
              <span>共 {{ section.lines.length }} 条引用</span>
              <el-button text type="primary" @click="toggleCitations">
                {{ showAllCitations ? '收起部分引用' : '展开全部引用' }}
              </el-button>
            </div>
            <ul class="citation-list">
              <li v-for="line in visibleCitationLines" :key="line">
                <a :href="extractUrl(line)" target="_blank" rel="noreferrer">
                  {{ line }}
                </a>
              </li>
            </ul>
          </div>

          <div
            v-else
            class="article-body markdown-body"
            v-html="section.html"
          ></div>
        </section>
      </div>

      <el-empty v-else description="报告生成后会展示在这里" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import dayjs from 'dayjs'
import MarkdownIt from 'markdown-it'

interface Props {
  report?: string | null
  title?: string
  subtitle?: string
  statusText?: string
  analystsCount?: number
  updatedAt?: string
}

const props = withDefaults(defineProps<Props>(), {
  report: '',
  title: '研究报告',
  subtitle: '完整报告已生成，可在此按论文式连续阅读。',
  statusText: '已完成',
  analystsCount: 0,
  updatedAt: ''
})

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true
})

const showAllCitations = ref(false)

const updatedAtText = computed(() => {
  return props.updatedAt ? dayjs(props.updatedAt).format('YYYY-MM-DD HH:mm:ss') : '暂无'
})

const normalizeHeading = (title: string) => title.trim().toLowerCase()

const sectionKind = (title: string) => {
  const normalized = normalizeHeading(title)
  if (
    normalized.includes('引用') ||
    normalized.includes('references') ||
    normalized.includes('sources')
  ) {
    return 'citations'
  }
  return 'content'
}

const baseAnchor = (title: string) => {
  const normalized = normalizeHeading(title)
  if (normalized.includes('引言') || normalized.includes('introduction')) return 'introduction'
  if (normalized.includes('结论') || normalized.includes('conclusion')) return 'conclusion'
  if (sectionKind(title) === 'citations') return 'citations'
  return 'content'
}

const sections = computed(() => {
  const report = (props.report || '').trim()
  if (!report) return []

  const rawSections = report
    .split(/^##\s+/m)
    .map((chunk) => chunk.trim())
    .filter(Boolean)

  return rawSections.map((chunk, index) => {
    const [titleLine, ...contentLines] = chunk.split('\n')
    const title = titleLine.trim()
    const kind = sectionKind(title)
    const content = contentLines.join('\n').trim()

    return {
      anchor: `${baseAnchor(title)}-${index}`,
      kind,
      title,
      html: kind === 'citations' ? '' : md.render(content),
      lines: kind === 'citations'
        ? content
            .split('\n')
            .map((line) => line.replace(/^[-*\d.\s]+/, '').trim())
            .filter(Boolean)
        : []
    }
  })
})

const navItems = computed(() => {
  return sections.value.map((section) => ({
    anchor: section.anchor,
    label: section.title
  }))
})

const citationSection = computed(() => {
  return sections.value.find((section) => section.kind === 'citations')
})

const visibleCitationLines = computed(() => {
  const lines = citationSection.value?.lines || []
  return showAllCitations.value ? lines : lines.slice(0, 8)
})

const extractUrl = (line: string) => {
  const match = line.match(/https?:\/\/\S+/)
  return match?.[0] || '#'
}

const toggleCitations = () => {
  showAllCitations.value = !showAllCitations.value
}

const scrollTo = (anchor: string) => {
  const element = document.getElementById(anchor)
  if (!element) return
  element.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<style scoped lang="scss">
.report-viewer {
  min-height: 100%;
  padding: 20px 0 36px;
}

.report-shell {
  max-width: 980px;
  margin: 0 auto;
  padding: 28px;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(90, 138, 255, 0.1), transparent 24%),
    linear-gradient(180deg, #fffefb 0%, #faf6ee 100%);
  box-shadow: 0 24px 60px rgba(15, 38, 60, 0.08);
}

.report-head {
  display: flex;
  gap: 24px;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(23, 50, 77, 0.08);
}

.report-head-main {
  flex: 1;

  h1 {
    margin: 10px 0 12px;
    color: #16314c;
    font-size: 40px;
    line-height: 1.2;
  }

  p {
    margin: 0;
    color: #6f8096;
    line-height: 1.7;
    font-size: 15px;
  }
}

.report-kicker {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: #eef4ff;
  color: #4a6ca6;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.report-meta {
  min-width: 280px;
  display: grid;
  gap: 12px;
}

.meta-item {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(23, 50, 77, 0.07);

  span {
    display: block;
    color: #7688a0;
    font-size: 12px;
    margin-bottom: 8px;
  }

  strong {
    color: #17324d;
    font-size: 15px;
  }
}

.report-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 28px;
}

.nav-chip {
  border: none;
  border-radius: 999px;
  padding: 8px 14px;
  background: #f0f4fa;
  color: #38597a;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #dde9ff;
    color: #24476d;
  }
}

.report-article {
  padding: 36px 56px;
  border-radius: 24px;
  background: #fff;
  border: 1px solid rgba(23, 50, 77, 0.06);
}

.article-section + .article-section {
  margin-top: 40px;
}

.article-section h2 {
  margin: 0 0 18px;
  color: #17324d;
  font-size: 28px;
}

.article-body {
  color: #294767;
  font-size: 16px;
  line-height: 1.9;
}

.markdown-body :deep(p),
.markdown-body :deep(li),
.markdown-body :deep(blockquote) {
  line-height: 1.9;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 22px;
}

.markdown-body :deep(a) {
  color: #2f67d7;
  word-break: break-all;
}

.citation-section {
  padding: 18px 20px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid #e7edf5;
}

.citation-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  color: #627892;
  font-size: 13px;
}

.citation-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 8px;

  a {
    color: #2f67d7;
    word-break: break-all;
    line-height: 1.7;
  }
}

@media (max-width: 980px) {
  .report-shell {
    padding: 20px;
  }

  .report-head {
    flex-direction: column;
  }

  .report-meta {
    min-width: 0;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .report-article {
    padding: 24px 20px;
  }
}

@media (max-width: 720px) {
  .report-head-main h1 {
    font-size: 30px;
  }

  .report-meta {
    grid-template-columns: 1fr;
  }
}
</style>
