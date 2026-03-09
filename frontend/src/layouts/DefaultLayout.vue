<template>
  <el-container class="layout-container">
    <el-aside :width="sidebarWidth" class="layout-aside">
      <AppSidebar />
    </el-aside>
    
    <el-container>
      <el-header class="layout-header">
        <AppHeader />
      </el-header>
      
      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppHeader from '@/components/common/AppHeader.vue'
import AppSidebar from '@/components/common/AppSidebar.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const sidebarWidth = computed(() => 
  appStore.sidebarCollapsed ? '64px' : '200px'
)
</script>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
  width: 100%;
}

.layout-aside {
  background: #001529;
  transition: width 0.3s;
  overflow-x: hidden;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
}

.layout-header {
  background: white;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 24px;
  display: flex;
  align-items: center;
  height: 60px !important;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.layout-main {
  background: #f0f2f5;
  padding: 24px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
