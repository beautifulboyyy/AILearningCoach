// 表单验证工具

// 验证邮箱
export const validateEmail = (email: string): boolean => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

// 验证用户名（4-20位，字母数字下划线）
export const validateUsername = (username: string): boolean => {
  const re = /^[a-zA-Z0-9_]{4,20}$/
  return re.test(username)
}

// 验证密码强度（至少8位，包含大小写字母和数字）
export const validatePassword = (password: string): {
  valid: boolean
  strength: 'weak' | 'medium' | 'strong'
  message: string
} => {
  if (password.length < 8) {
    return { valid: false, strength: 'weak', message: '密码至少需要8个字符' }
  }
  
  const hasLower = /[a-z]/.test(password)
  const hasUpper = /[A-Z]/.test(password)
  const hasNumber = /\d/.test(password)
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password)
  
  const score = [hasLower, hasUpper, hasNumber, hasSpecial].filter(Boolean).length
  
  if (score < 3) {
    return { valid: false, strength: 'weak', message: '密码强度太弱，需要包含大小写字母和数字' }
  } else if (score === 3) {
    return { valid: true, strength: 'medium', message: '密码强度中等' }
  } else {
    return { valid: true, strength: 'strong', message: '密码强度强' }
  }
}

// 验证URL
export const validateURL = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

// 验证手机号（中国）
export const validatePhone = (phone: string): boolean => {
  const re = /^1[3-9]\d{9}$/
  return re.test(phone)
}

// Element Plus 表单验证规则
export const rules = {
  required: { required: true, message: '此项为必填项', trigger: 'blur' },
  
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 20, message: '用户名长度为4-20个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少需要8个字符', trigger: 'blur' }
  ],
  
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ]
}
