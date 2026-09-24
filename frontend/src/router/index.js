import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import studentRoutes from './student'

NProgress.configure({ showSpinner: false })

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  // 学生端独立路由
  ...studentRoutes,
  {
    path: '/',
    component: () => import('@/layout/index.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '数据看板', icon: 'DataAnalysis', roles: ['admin', 'teacher'] }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/index.vue'),
        meta: { title: '个人中心', icon: 'User', hidden: true, roles: ['admin', 'teacher'] }
      },
      {
        path: 'topics',
        name: 'Topics',
        component: () => import('@/views/topics/index.vue'),
        meta: { title: '选题管理', icon: 'Document', roles: ['admin', 'teacher'] }
      },
      {
        path: 'proposals',
        name: 'Proposals',
        component: () => import('@/views/proposals/index.vue'),
        meta: { title: '开题管理', icon: 'Files', roles: ['admin', 'teacher'] }
      },
      {
        path: 'midterm',
        name: 'Midterm',
        component: () => import('@/views/midterm/index.vue'),
        meta: { title: '中期检查', icon: 'CircleCheck', roles: ['admin', 'teacher'] }
      },
      {
        path: 'guidance',
        name: 'Guidance',
        component: () => import('@/views/teacher/guidance.vue'),
        meta: { title: '过程指导', icon: 'ChatDotRound', roles: ['admin', 'teacher'] }
      },
      {
        path: 'thesis',
        name: 'Thesis',
        redirect: '/thesis/draft1',
        meta: { title: '论文版本', icon: 'DocumentCopy', roles: ['admin', 'teacher'] },
        children: [
          {
            path: 'draft1',
            name: 'ThesisDraft1',
            component: () => import('@/views/thesis/index.vue'),
            meta: { title: '论文一稿', icon: 'Document', roles: ['admin', 'teacher'] }
          },
          {
            path: 'draft2',
            name: 'ThesisDraft2',
            component: () => import('@/views/thesis/index.vue'),
            meta: { title: '论文二稿', icon: 'Document', roles: ['admin', 'teacher'] }
          },
          {
            path: 'final',
            name: 'ThesisFinal',
            component: () => import('@/views/thesis/index.vue'),
            meta: { title: '论文终审', icon: 'DocumentChecked', roles: ['admin', 'teacher'] }
          }
        ]
      },
      {
        path: 'reviews',
        name: 'Reviews',
        redirect: '/reviews/review',
        meta: { title: '评阅答辩', icon: 'EditPen', roles: ['admin', 'teacher'] },
        children: [
          {
            path: 'review',
            name: 'ReviewList',
            component: () => import('@/views/reviews/index.vue'),
            meta: { title: '论文评阅', icon: 'Reading', roles: ['admin', 'teacher'] }
          },
          {
            path: 'defense',
            name: 'DefenseList',
            component: () => import('@/views/reviews/index.vue'),
            meta: { title: '答辩评价', icon: 'ChatLineSquare', roles: ['admin', 'teacher'] }
          }
        ]
      },
      {
        path: 'anomaly',
        name: 'Anomaly',
        component: () => import('@/views/anomaly/index.vue'),
        meta: { title: '异常检测', icon: 'Warning', roles: ['admin', 'teacher'] }
      },
      {
        path: 'archives',
        name: 'Archives',
        component: () => import('@/views/archives/index.vue'),
        meta: { title: '成果归档', icon: 'Box', roles: ['admin', 'teacher'] }
      },
      {
        path: 'system',
        name: 'System',
        redirect: '/system/users',
        meta: { title: '系统管理', icon: 'Setting', roles: ['admin'] },
        children: [
          {
            path: 'users',
            name: 'Users',
            component: () => import('@/views/system/users.vue'),
            meta: { title: '用户管理', icon: 'UserFilled', roles: ['admin'] }
          },
          {
            path: 'logs',
            name: 'Logs',
            component: () => import('@/views/system/logs.vue'),
            meta: { title: '操作日志', icon: 'List', roles: ['admin'] }
          },
          {
            path: 'stages',
            name: 'Stages',
            component: () => import('@/views/system/stages.vue'),
            meta: { title: '阶段时间设定', icon: 'Timer', roles: ['admin'] }
          }
        ]
      }
    ]
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { title: '页面不存在' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

function getHomePage(role) {
  if (role === 'student') {
    return '/student/dashboard'
  }
  return '/dashboard'
}

router.beforeEach((to, from, next) => {
  NProgress.start()
  document.title = to.meta.title ? `${to.meta.title} - 毕业论文质量监控系统` : '毕业论文质量监控系统'

  const userStore = useUserStore()

  if (to.meta.requiresAuth === false) {
    next()
    return
  }

  if (!userStore.token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  const role = userStore.userInfo?.role

  if (to.path === '/') {
    next(getHomePage(role))
    return
  }

  // 学生只能访问 /student/ 下的路由
  if (role === 'student' && !to.path.startsWith('/student')) {
    next(getHomePage(role))
    return
  }

  // 教师和管理员不能访问学生端路由
  if (role !== 'student' && to.path.startsWith('/student')) {
    next(getHomePage(role))
    return
  }

  // 检查角色权限
  if (to.meta.roles && !to.meta.roles.includes(role)) {
    const home = getHomePage(role)
    if (to.path !== home) {
      next(home)
      return
    }
    next('/404')
    return
  }

  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router
