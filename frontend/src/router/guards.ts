import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

NProgress.configure({ showSpinner: false })

export function setupRouterGuards(router: Router) {
  // 前置守卫
  router.beforeEach((to, from, next) => {
    NProgress.start()
    
    // 设置页面标题
    if (to.meta.title) {
      document.title = `${to.meta.title} - AI学习教练系统`
    }
    
    const authStore = useAuthStore()
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
    const isLoggedIn = authStore.isLoggedIn
    
    // 需要认证但未登录
    if (requiresAuth && !isLoggedIn) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
    
    // 已登录访问登录页，跳转到首页
    if (isLoggedIn && (to.path === '/login' || to.path === '/register')) {
      next({ path: '/' })
      return
    }
    
    next()
  })
  
  // 后置守卫
  router.afterEach(() => {
    NProgress.done()
  })
  
  // 错误处理
  router.onError((error) => {
    console.error('Router error:', error)
    NProgress.done()
  })
}
