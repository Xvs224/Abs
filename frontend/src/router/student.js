export default [
  {
    path: '/student',
    component: () => import('@/layout/StudentLayout.vue'),
    redirect: '/student/dashboard',
    meta: { requiresAuth: true, roles: ['student'] },
    children: [
      {
        path: 'dashboard',
        name: 'StudentDashboard',
        component: () => import('@/views/student/dashboard.vue'),
        meta: { title: '工作台' }
      },
      {
        path: 'topics',
        name: 'StudentTopics',
        component: () => import('@/views/student/topics.vue'),
        meta: { title: '选题确认' }
      },
      {
        path: 'proposals',
        name: 'StudentProposals',
        component: () => import('@/views/student/proposals.vue'),
        meta: { title: '开题报告' }
      },
      {
        path: 'midterm',
        name: 'StudentMidterm',
        component: () => import('@/views/student/midterm.vue'),
        meta: { title: '中期检查' }
      },
      {
        path: 'thesis',
        name: 'StudentThesis',
        redirect: '/student/thesis/draft1',
        meta: { title: '论文版本' },
        children: [
          {
            path: 'draft1',
            name: 'StudentThesisDraft1',
            component: () => import('@/views/student/thesis.vue'),
            meta: { title: '论文一稿' }
          },
          {
            path: 'draft2',
            name: 'StudentThesisDraft2',
            component: () => import('@/views/student/thesis.vue'),
            meta: { title: '论文二稿' }
          },
          {
            path: 'final',
            name: 'StudentThesisFinal',
            component: () => import('@/views/student/thesis.vue'),
            meta: { title: '论文终审' }
          }
        ]
      },
      {
        path: 'reviews',
        name: 'StudentReviews',
        redirect: '/student/reviews/review',
        meta: { title: '评阅答辩' },
        children: [
          {
            path: 'review',
            name: 'StudentReview',
            component: () => import('@/views/student/reviews.vue'),
            meta: { title: '论文评阅' }
          },
          {
            path: 'defense',
            name: 'StudentDefense',
            component: () => import('@/views/student/reviews.vue'),
            meta: { title: '答辩评价' }
          }
        ]
      },
      {
        path: 'anomaly',
        name: 'StudentAnomaly',
        component: () => import('@/views/student/anomaly.vue'),
        meta: { title: '异常提示' }
      },
      {
        path: 'archives',
        name: 'StudentArchives',
        component: () => import('@/views/student/archives.vue'),
        meta: { title: '成果归档' }
      },
      {
        path: 'profile',
        name: 'StudentProfile',
        component: () => import('@/views/student/profile.vue'),
        meta: { title: '个人中心' }
      }
    ]
  }
]
