<template>
  <div class="not-found-container">
    <div class="error-content">
      <div class="error-code">404</div>
      <h1>页面不存在</h1>
      <p>抱歉，您访问的页面不存在</p>
      <el-button type="primary" @click="goHome">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped lang="scss">
.not-found-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f5f5f5;
  
  .error-content {
    text-align: center;
    
    .error-code {
      font-size: 120px;
      font-weight: bold;
      color: #409EFF;
      line-height: 1;
      margin-bottom: 24px;
    }
    
    h1 {
      font-size: 32px;
      margin: 0 0 16px 0;
      color: #303133;
    }
    
    p {
      font-size: 16px;
      color: #606266;
      margin: 0 0 32px 0;
    }
  }
}
</style>
