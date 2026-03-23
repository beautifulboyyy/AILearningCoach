<template>
  <div class="app-sidebar">
    <div class="logo-container">
      <el-icon :size="32" color="#409EFF">
        <Reading />
      </el-icon>
      <transition name="fade">
        <span v-if="!collapsed" class="logo-text">AI学习教练</span>
      </transition>
    </div>
    
    <el-menu
      :default-active="activeMenu"
      :collapse="collapsed"
      :collapse-transition="false"
      class="sidebar-menu"
      background-color="#001529"
      text-color="#ffffff"
      active-text-color="#409EFF"
      @select="handleMenuSelect"
    >
      <el-menu-item index="/dashboard">
        <el-icon><HomeFilled /></el-icon>
        <template #title>首页</template>
      </el-menu-item>
      
      <el-menu-item index="/chat">
        <el-icon><ChatDotRound /></el-icon>
        <template #title>智能对话</template>
      </el-menu-item>
      
      <el-menu-item index="/deepresearch">
        <el-icon><Connection /></el-icon>
        <template #title>深度研究</template>
      </el-menu-item>

      <el-menu-item index="/learning-path">
        <el-icon><TrendCharts /></el-icon>
        <template #title>学习路径</template>
      </el-menu-item>
      
      <el-menu-item index="/tasks">
        <el-icon><List /></el-icon>
        <template #title>任务管理</template>
      </el-menu-item>
      
      <el-menu-item index="/progress">
        <el-icon><DataAnalysis /></el-icon>
        <template #title>学习进度</template>
      </el-menu-item>
      
      <el-menu-item index="/profile">
        <el-icon><User /></el-icon>
        <template #title>用户画像</template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Reading, HomeFilled, ChatDotRound, TrendCharts, 
  List, DataAnalysis, User, Connection
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

const collapsed = computed(() => appStore.sidebarCollapsed)
const activeMenu = computed(() => route.path)

const handleMenuSelect = (index: string) => {
  router.push(index)
}
</script>

<style scoped lang="scss">
.app-sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 0 20px;
  background: #002140;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  .logo-text {
    color: white;
    font-size: 18px;
    font-weight: bold;
    white-space: nowrap;
  }
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  
  :deep(.el-menu-item) {
    &:hover {
      background-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    &.is-active {
      background-color: rgba(64, 158, 255, 0.2) !important;
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
