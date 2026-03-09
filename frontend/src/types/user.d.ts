// 用户相关类型定义

export interface User {
  id: string | number
  username: string
  email: string
  full_name?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface LoginData {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  user?: User
}

export interface UserProfile {
  id?: string | number
  user_id?: string | number

  // 后端原生字段
  name?: string
  age?: number
  occupation?: string
  technical_background?: {
    education?: string
    major?: string
    work_experience?: string
    tech_stack?: string[]
    programming_languages?: string[]
    frameworks?: string[]
    experience_years?: number
  }
  learning_goal?: string
  learning_preference?: {
    style?: string
    content_type?: string
    explanation_style?: string
    learning_pace?: string
  }
  current_level?: Record<string, string>
  bio?: string

  // 前端兼容字段（由后端自动转换）
  background?: {
    education?: string
    major?: string
    work_experience?: string
  }
  tech_stack?: string[]
  learning_style?: string

  created_at?: string
  updated_at?: string
}
