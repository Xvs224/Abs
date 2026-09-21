import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

NProgress.configure({ showSpinner: false })

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
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
        meta: { title: '数据看板', icon: 'DataAnalysis', roles: ['admin', 'teacher', 'student'] }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/index.vue'),
        meta: { title: '个人中心', icon: 'User', hidden: true, roles: ['admin', 'teacher', 'student'] }
      },
      // 选题管理 - 学生：申报选题；教师：审核选题；管理员：全部
      {
        path: 'topics',
        name: 'Topics',
        component: () => import('@/views/topics/index.vue'),
        meta: { title: '选题管理', icon: 'Document', roles: ['admin', 'teacher', 'student'] }
      },
      // 开题管理 - 学生：提交开题；教师：审核；管理员：全部
      {
        path: 'proposals',
        name: 'Proposals',
        component: () => import('@/views/proposals/index.vue'),
        meta: { title: '开题管理', icon: 'Files', roles: ['admin', 'teacher', 'student'] }
      },
      // 过程指导 - 学生：查看自己的指导记录；教师：记录指导；管理员：全部
      {
        path: 'guidance',
        name: 'Guidance',
        component: () => import('@/views/guidance/index.vue'),
        meta: { title: '过程指导', icon: 'ChatDotRound', roles: ['admin', 'teacher', 'student'] }
      },
      // 中期检查 - 学生：提交中期报告；教师：评审；管理员：全部
      {
        path: 'midterm',
        name: 'Midterm',
        component: () => import('@/views/midterm/index.vue'),
        meta: { title: '中期检查', icon: 'CircleCheck', roles: ['admin', 'teacher', 'student'] }
      },
      // 论文版本 - 学生：提交版本；教师：查验；管理员：全部
      {
        path: 'thesis',
        name: 'Thesis',
        component: () => import('@/views/thesis/index.vue'),
        meta: { title: '论文版本', icon: 'DocumentCopy', roles: ['admin', 'teacher', 'student'] }
      },
      // 评阅答辩 - 教师：评阅答辩评分；管理员：全部；学生：查看自己的评阅答辩结果
      {
        path: 'reviews',
        name: 'Reviews',
        component: () => import('@/views/reviews/index.vue'),
        meta: { title: '评阅答辩', icon: 'EditPen', roles: ['admin', 'teacher', 'student'] }
      },
      // 异常检测 - 教师：查看异常并复核；管理员：全部；学生：查看自己的异常提示
      {
        path: 'anomaly',
        name: 'Anomaly',
        component: () => import('@/views/anomaly/index.vue'),
        meta: { title: '异常检测', icon: 'Warning', roles: ['admin', 'teacher', 'student'] }
      },
      // 成果归档 - 管理员：归档管理；教师：查看；学生：查看自己的归档
      {
        path: 'archives',
        name: 'Archives',
        component: () => import('@/views/archives/index.vue'),
        meta: { title: '成果归档', icon: 'Box', roles: ['admin', 'teacher', 'student'] }
      },
      // 系统管理 - 仅管理员
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

// 路由守卫
router.beforeEach((to, from, next) => {
  NProgress.start()
  document.title = to.meta.title ? `${to.meta.title} - 毕业论文质量监控系统` : '毕业论文质量监控系统'

  const userStore = useUserStore()

  // 检查是否需要登录
  if (to.meta.requiresAuth === false) {
    next()
    return
  }

  // 检查登录状态
  if (!userStore.token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  // 检查角色权限
  if (to.meta.roles && !to.meta.roles.includes(userStore.userInfo?.role)) {
    next('/404')
    return
  }

  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router
