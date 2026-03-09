<template>
  <div class="auth-container">
    <div class="auth-left">
      <div class="illustration">
        <el-icon :size="200" color="#409EFF">
          <Avatar />
        </el-icon>
        <h2>AI学习教练系统</h2>
        <p>智能规划·个性化辅导·高效学习</p>
      </div>
    </div>
    
    <div class="auth-right">
      <div class="auth-form-container">
        <div class="logo-section">
          <el-icon :size="50" color="#409EFF">
            <Reading />
          </el-icon>
          <h1>AI学习教练</h1>
        </div>
        
        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="rules"
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="用户名/邮箱"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          
          <el-form-item>
            <el-checkbox v-model="loginForm.remember">
              记住我
            </el-checkbox>
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="login-button"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="auth-footer">
          <router-link to="/register" class="register-link">
            注册新账号
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance } from 'element-plus'
import { User, Lock, Avatar, Reading } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

const rules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少需要6个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await authStore.login({
        username: loginForm.username,
        password: loginForm.password
      })
      
      ElMessage.success('登录成功')
      
      // 跳转到之前的页面或首页
      const redirect = route.query.redirect as string
      router.push(redirect || '/')
    } catch (error: any) {
      console.error('Login failed:', error)
      ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
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
    margin-bottom: 40px;
    
    h1 {
      margin-top: 15px;
      font-size: 24px;
      color: #303133;
    }
  }
  
  .login-form {
    .login-button {
      width: 100%;
    }
  }
  
  .auth-footer {
    text-align: center;
    margin-top: 20px;
    
    .register-link {
      color: #409EFF;
      text-decoration: none;
      
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
