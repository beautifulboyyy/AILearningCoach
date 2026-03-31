import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { setupRouterGuards } from './guards'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { requiresAuth: false, title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { requiresAuth: false, title: '注册' }
  },
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/chat/ChatView.vue'),
        meta: { title: '智能对话' }
      },
      {
        path: 'learning-path',
        name: 'LearningPath',
        component: () => import('@/views/learning-path/PathView.vue'),
        meta: { title: '学习路径' }
      },
      {
        path: 'learning-path/generate',
        name: 'GeneratePath',
        component: () => import('@/views/learning-path/GenerateView.vue'),
        meta: { title: '生成学习路径' }
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/tasks/TasksView.vue'),
        meta: { title: '任务管理' }
      },
      {
        path: 'deep-research',
        name: 'DeepResearch',
        component: () => import('@/views/deep-research/DeepResearchWorkbench.vue'),
        meta: { title: 'Deep Research' }
      },
      {
        path: 'progress',
        name: 'Progress',
        component: () => import('@/views/progress/ProgressView.vue'),
        meta: { title: '学习进度' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/ProfileView.vue'),
        meta: { title: '用户画像' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFoundView.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 设置路由守卫
setupRouterGuards(router)

export default router
