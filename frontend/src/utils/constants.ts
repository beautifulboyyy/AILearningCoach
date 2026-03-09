// 常量定义

// 优先级
export const PRIORITY_OPTIONS = [
  { label: '低', value: 'low', color: '#67C23A' },
  { label: '中', value: 'medium', color: '#E6A23C' },
  { label: '高', value: 'high', color: '#F56C6C' },
  { label: '紧急', value: 'urgent', color: '#F56C6C' }
]

// 任务状态
export const TASK_STATUS_OPTIONS = [
  { label: '待开始', value: 'todo', color: '#909399' },
  { label: '进行中', value: 'in_progress', color: '#409EFF' },
  { label: '已完成', value: 'completed', color: '#67C23A' },
  { label: '已取消', value: 'cancelled', color: '#C0C4CC' }
]

// 学习目标
export const LEARNING_GOAL_OPTIONS = [
  { label: '求职准备', value: 'job_hunting' },
  { label: '技能提升', value: 'skill_improvement' },
  { label: '兴趣学习', value: 'hobby_learning' },
  { label: '考试备考', value: 'exam_preparation' }
]

// 学习风格
export const LEARNING_STYLE_OPTIONS = [
  { label: '项目驱动', value: 'project_driven', description: '通过实战项目学习' },
  { label: '理论优先', value: 'theory_first', description: '先学理论再实践' },
  { label: '实践优先', value: 'practice_first', description: '边做边学' }
]

// Agent类型
export const AGENT_TYPES = {
  QA: 'QA Agent',
  PLANNER: 'Planner Agent',
  COACH: 'Coach Agent',
  ANALYST: 'Analyst Agent'
}

// Agent颜色
export const AGENT_COLORS = {
  'QA Agent': '#409EFF',
  'Planner Agent': '#67C23A',
  'Coach Agent': '#E6A23C',
  'Analyst Agent': '#F56C6C'
}

// 日期格式
export const DATE_FORMAT = 'YYYY-MM-DD'
export const DATETIME_FORMAT = 'YYYY-MM-DD HH:mm:ss'
export const TIME_FORMAT = 'HH:mm:ss'

// 分页配置
export const PAGE_SIZE = 20
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

// 本地存储键名
export const STORAGE_KEYS = {
  TOKEN: 'ai_coach_token',
  REFRESH_TOKEN: 'ai_coach_refresh_token',
  USER: 'ai_coach_user',
  THEME: 'ai_coach_theme',
  LANGUAGE: 'ai_coach_language'
}
