<template>
  <div class="auth-container">
    <div class="auth-left">
      <div class="illustration">
        <el-icon :size="200" color="#67C23A">
          <User />
        </el-icon>
        <h2>加入AI学习教练</h2>
        <p>开启智能学习之旅</p>
      </div>
    </div>
    
    <div class="auth-right">
      <div class="auth-form-container">
        <div class="logo-section">
          <el-icon :size="50" color="#409EFF">
            <Reading />
          </el-icon>
          <h1>注册账号</h1>
        </div>
        
        <el-form
          ref="formRef"
          :model="registerForm"
          :rules="rules"
          class="register-form"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="用户名（4-20位字母数字）"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>
          
          <el-form-item prop="email">
            <el-input
              v-model="registerForm.email"
              placeholder="邮箱"
              size="large"
              :prefix-icon="Message"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="密码（至少8位）"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          
          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="确认密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleRegister"
            />
          </el-form-item>
          
          <el-form-item prop="fullName">
            <el-input
              v-model="registerForm.fullName"
              placeholder="姓名（可选）"
              size="large"
              :prefix-icon="Avatar"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="register-button"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="auth-footer">
          已有账号？
          <router-link to="/login" class="login-link">
            立即登录
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Message, Avatar, Reading } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  fullName: ''
})

const validatePassword = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else if (value.length < 8) {
    callback(new Error('密码至少需要8个字符'))
  } else {
    callback()
  }
}

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 20, message: '用户名长度为4-20个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, validator: validatePassword, trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await authStore.register({
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password,
        full_name: registerForm.fullName || undefined
      })
      
      ElMessage.success('注册成功！请登录')
      router.push('/login')
    } catch (error: any) {
      console.error('Register failed:', error)
      const detail = error.response?.data?.detail
      if (typeof detail === 'string') {
        ElMessage.error(detail)
      } else if (Array.isArray(detail)) {
        ElMessage.error(detail[0]?.msg || '注册失败')
      } else {
        ElMessage.error('注册失败，请重试')
      }
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.auth-container {
  display: flex;
  height: 100vh;
  width: 100%;
}

.auth-left {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  
  .illustration {
    text-align: center;
    
    h2 {
      margin: 30px 0 10px;
      font-size: 32px;
    }
    
    p {
      font-size: 16px;
      opacity: 0.9;
    }
  }
}

.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.auth-form-container {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  
  .logo-section {
    text-align: center;
    margin-bottom: 30px;
    
    h1 {
      margin-top: 15px;
      font-size: 24px;
      color: #303133;
    }
  }
  
  .register-form {
    .register-button {
      width: 100%;
    }
  }
  
  .auth-footer {
    text-align: center;
    margin-top: 20px;
    color: #606266;
    
    .login-link {
      color: #409EFF;
      text-decoration: none;
      margin-left: 5px;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
}

@media (max-width: 768px) {
  .auth-left {
    display: none;
  }
  
  .auth-right {
    flex: 1;
  }
  
  .auth-form-container {
    width: 90%;
    max-width: 400px;
  }
}
</style>
