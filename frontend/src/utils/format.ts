import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

// 格式化日期时间
export const formatDate = (date: string | Date, format = 'YYYY-MM-DD'): string => {
  return dayjs(date).format(format)
}

export const formatDateTime = (date: string | Date): string => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

export const formatTime = (date: string | Date): string => {
  return dayjs(date).format('HH:mm:ss')
}

// 相对时间
export const formatRelativeTime = (date: string | Date): string => {
  return dayjs(date).fromNow()
}

// 格式化数字
export const formatNumber = (num: number, decimals = 0): string => {
  return num.toFixed(decimals)
}

// 格式化百分比
export const formatPercent = (value: number, decimals = 0): string => {
  return `${(value * 100).toFixed(decimals)}%`
}

// 格式化时长（小时）
export const formatDuration = (hours: number): string => {
  if (hours < 1) {
    return `${Math.round(hours * 60)}分钟`
  }
  const h = Math.floor(hours)
  const m = Math.round((hours - h) * 60)
  return m > 0 ? `${h}小时${m}分钟` : `${h}小时`
}

// 格式化文件大小
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

// 截断文本
export const truncate = (text: string, length: number, suffix = '...'): string => {
  if (text.length <= length) return text
  return text.substring(0, length) + suffix
}
