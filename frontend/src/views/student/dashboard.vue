<template>
  <div class="student-dashboard">
    <div class="welcome-card">
      <div class="welcome-text">
        <h2>{{ greeting }}，{{ userStore.userInfo?.real_name || '同学' }}</h2>
        <p>{{ todayStr }}</p>
      </div>
      <div class="welcome-info">
        <div class="info-item">
          <span class="info-label">学号</span>
          <span class="info-value">{{ userStore.userInfo?.student_no || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">院系</span>
          <span class="info-value">{{ userStore.userInfo?.department || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">专业</span>
          <span class="info-value">{{ userStore.userInfo?.major || '-' }}</span>
        </div>
      </div>
    </div>

    <div class="progress-section">
      <div class="section-header">
        <h3>毕业论文进度</h3>
        <el-tag :type="overallStatusType" size="default">{{ overallStatusText }}</el-tag>
      </div>
      <el-steps :active="currentStep" align-center finish-status="success" :process-status="currentStepStatus">
        <el-step
          v-for="(stage, index) in stages"
          :key="index"
          :title="stage.title"
          :description="stage.description"
          :status="stage.status"
        >
          <template #icon>
            <div class="step-icon-wrapper" @click="goToStage(stage.path)">
              <el-icon size="20"><component :is="stage.icon" /></el-icon>
            </div>
          </template>
        </el-step>
      </el-steps>
    </div>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>快捷入口</span>
            </div>
          </template>
          <div class="quick-links">
            <div class="quick-link" @click="$router.push('/student/topics')">
              <el-icon size="20" color="#409eff"><Document /></el-icon>
              <span>选题确认</span>
            </div>
            <div class="quick-link" @click="$router.push('/student/proposals')">
              <el-icon size="20" color="#67c23a"><Files /></el-icon>
              <span>开题报告</span>
            </div>
            <div class="quick-link" @click="$router.push('/student/midterm')">
              <el-icon size="20" color="#909399"><CircleCheck /></el-icon>
              <span>中期检查</span>
            </div>
            <div class="quick-link" @click="$router.push('/student/thesis')">
              <el-icon size="20" color="#f56c6c"><DocumentCopy /></el-icon>
              <span>论文版本</span>
            </div>
            <div class="quick-link" @click="$router.push('/student/reviews')">
              <el-icon size="20" color="#9c27b0"><EditPen /></el-icon>
              <span>评阅答辩</span>
            </div>
            <div class="quick-link" @click="$router.push('/student/archives')">
              <el-icon size="20" color="#00bcd4"><Box /></el-icon>
              <span>成果归档</span>
            </div>
            <div class="quick-link" @click="$router.push('/student/profile')">
              <el-icon size="20" color="#606266"><User /></el-icon>
              <span>个人中心</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import studentApi from '@/api/student'

const router = useRouter()
const userStore = useUserStore()

const topicData = ref(null)
const proposalData = ref(null)
const midtermData = ref(null)
const thesisVersions = ref([])
const reviewData = ref(null)
const archiveData = ref(null)

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '凌晨好'
  if (h < 9) return '早上好'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const todayStr = computed(() => {
  const d = new Date()
  const week = ['日', '一', '二', '三', '四', '五', '六']
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 星期${week[d.getDay()]}`
})

const formatDate = (dt) => {
  if (!dt) return '-'
  return new Date(dt).toLocaleDateString('zh-CN')
}

// 各阶段状态计算
const topicStage = computed(() => {
  if (!topicData.value) return { text: '未开始', isDone: false, tagType: 'info' }
  const map = {
    pending: { text: '待审核', isDone: false, tagType: 'warning' },
    approved: { text: '已通过', isDone: true, tagType: 'success' },
    rejected: { text: '已驳回', isDone: false, tagType: 'danger' },
    withdrawn: { text: '已撤回', isDone: false, tagType: 'info' }
  }
  return map[topicData.value.status] || { text: topicData.value.status, isDone: false, tagType: 'info' }
})

const proposalStage = computed(() => {
  if (!proposalData.value) return { text: '未开始', isDone: false, tagType: 'info' }
  const map = {
    draft: { text: '草稿中', isDone: false, tagType: 'info' },
    submitted: { text: '待审核', isDone: false, tagType: 'warning' },
    approved: { text: '已通过', isDone: true, tagType: 'success' },
    rejected: { text: '已驳回', isDone: false, tagType: 'danger' }
  }
  return map[proposalData.value.status] || { text: proposalData.value.status, isDone: false, tagType: 'info' }
})

const midtermStage = computed(() => {
  if (!midtermData.value) return { text: '未开始', isDone: false, tagType: 'info' }
  const map = {
    draft: { text: '草稿中', isDone: false, tagType: 'info' },
    submitted: { text: '待评审', isDone: false, tagType: 'warning' },
    passed: { text: '已通过', isDone: true, tagType: 'success' },
    rectifying: { text: '需整改', isDone: false, tagType: 'warning' },
    failed: { text: '未通过', isDone: false, tagType: 'danger' },
    rectified: { text: '整改完成', isDone: true, tagType: 'success' }
  }
  return map[midtermData.value.status] || { text: midtermData.value.status, isDone: false, tagType: 'info' }
})

const thesisStage = computed(() => {
  if (thesisVersions.value.length === 0) return { text: '未提交', isDone: false, tagType: 'info' }
  if (thesisVersions.value.length > 0) return { text: `已提交${thesisVersions.value.length}版`, isDone: true, tagType: 'success' }
  return { text: '未提交', isDone: false, tagType: 'info' }
})

const reviewStage = computed(() => {
  if (!reviewData.value) return { text: '未开始', isDone: false, tagType: 'info' }
  const map = {
    pending: { text: '待评阅', isDone: false, tagType: 'warning' },
    reviewing: { text: '评阅中', isDone: false, tagType: 'warning' },
    completed: { text: '已完成', isDone: true, tagType: 'success' }
  }
  return map[reviewData.value.status] || { text: reviewData.value.status, isDone: false, tagType: 'info' }
})

const archiveStage = computed(() => {
  if (!archiveData.value) return { text: '未开始', isDone: false, tagType: 'info' }
  const map = {
    pending: { text: '待审核', isDone: false, tagType: 'warning' },
    archived: { text: '已归档', isDone: true, tagType: 'success' },
    returned: { text: '已退回', isDone: false, tagType: 'danger' }
  }
  return map[archiveData.value.status] || { text: archiveData.value.status, isDone: false, tagType: 'info' }
})

// 阶段列表
const stages = computed(() => [
  {
    title: '选题确认',
    path: '/student/topics',
    icon: 'Document',
    description: topicStage.value.text,
    detail: topicData.value?.title || '',
    isDone: topicStage.value.isDone,
    isCurrent: !topicStage.value.isDone,
    tagType: topicStage.value.tagType,
    status: topicStage.value.isDone ? 'success' : (!topicData.value ? 'wait' : 'process')
  },
  {
    title: '开题报告',
    path: '/student/proposals',
    icon: 'Files',
    description: proposalStage.value.text,
    detail: proposalData.value?.research_content?.slice(0, 60) || '',
    isDone: proposalStage.value.isDone,
    isCurrent: topicStage.value.isDone && !proposalStage.value.isDone,
    tagType: proposalStage.value.tagType,
    status: proposalStage.value.isDone ? 'success' : (topicStage.value.isDone ? 'process' : 'wait')
  },
  {
    title: '中期检查',
    path: '/student/midterm',
    icon: 'CircleCheck',
    description: midtermStage.value.text,
    detail: midtermData.value ? `进度 ${midtermData.value.progress_percentage || 0}%` : '',
    isDone: midtermStage.value.isDone,
    isCurrent: proposalStage.value.isDone && !midtermStage.value.isDone,
    tagType: midtermStage.value.tagType,
    status: midtermStage.value.isDone ? 'success' : (proposalStage.value.isDone ? 'process' : 'wait')
  },
  {
    title: '论文提交',
    path: '/student/thesis',
    icon: 'DocumentCopy',
    description: thesisStage.value.text,
    detail: thesisVersions.value.length > 0 ? `最新v${Math.max(...thesisVersions.value.map(v => v.version_num || 0))}` : '',
    isDone: thesisStage.value.isDone,
    isCurrent: midtermStage.value.isDone && !thesisStage.value.isDone,
    tagType: thesisStage.value.tagType,
    status: thesisStage.value.isDone ? 'success' : (midtermStage.value.isDone ? 'process' : 'wait')
  },
  {
    title: '评阅答辩',
    path: '/student/reviews',
    icon: 'EditPen',
    description: reviewStage.value.text,
    detail: reviewData.value?.total_score ? `${reviewData.value.total_score}分` : '',
    isDone: reviewStage.value.isDone,
    isCurrent: thesisStage.value.isDone && !reviewStage.value.isDone,
    tagType: reviewStage.value.tagType,
    status: reviewStage.value.isDone ? 'success' : (thesisStage.value.isDone ? 'process' : 'wait')
  },
  {
    title: '成果归档',
    path: '/student/archives',
    icon: 'Box',
    description: archiveStage.value.text,
    detail: archiveData.value?.archive_no ? `编号: ${archiveData.value.archive_no}` : '',
    isDone: archiveStage.value.isDone,
    isCurrent: reviewStage.value.isDone && !archiveStage.value.isDone,
    tagType: archiveStage.value.tagType,
    status: archiveStage.value.isDone ? 'success' : (reviewStage.value.isDone ? 'process' : 'wait')
  }
])

const currentStep = computed(() => {
  const doneCount = stages.value.filter(s => s.isDone).length
  return doneCount
})

const currentStepStatus = computed(() => {
  return 'process'
})

const overallStatusText = computed(() => {
  const done = stages.value.filter(s => s.isDone).length
  if (done === 0) return '刚起步'
  if (done === 6) return '全部完成'
  return `已完成 ${done}/6 阶段`
})

const overallStatusType = computed(() => {
  const done = stages.value.filter(s => s.isDone).length
  if (done === 6) return 'success'
  if (done >= 4) return ''
  if (done >= 2) return 'warning'
  return 'info'
})

const goToStage = (path) => {
  router.push(path)
}

const loadDashboard = async () => {
  const [topicRes, proposalRes, midtermRes, thesisRes, reviewRes, archiveRes] = await Promise.allSettled([
    studentApi.getMyTopic(),
    studentApi.getMyProposal(),
    studentApi.getMyMidterm(),
    studentApi.getMyThesisVersions(),
    studentApi.getMyReviews(),
    studentApi.getMyArchives()
  ])

  if (topicRes.status === 'fulfilled' && topicRes.value?.items?.length > 0) {
    topicData.value = topicRes.value.items[0]
  }
  if (proposalRes.status === 'fulfilled' && proposalRes.value?.items?.length > 0) {
    proposalData.value = proposalRes.value.items[0]
  }
  if (midtermRes.status === 'fulfilled' && midtermRes.value?.items?.length > 0) {
    midtermData.value = midtermRes.value.items[0]
  }
  if (thesisRes.status === 'fulfilled') {
    thesisVersions.value = thesisRes.value?.items || []
  }
  if (reviewRes.status === 'fulfilled' && reviewRes.value?.items?.length > 0) {
    reviewData.value = reviewRes.value.items[0]
  }
  if (archiveRes.status === 'fulfilled' && archiveRes.value?.items?.length > 0) {
    archiveData.value = archiveRes.value.items[0]
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped lang="scss">
.student-dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
  border-radius: 12px;
  padding: 24px 32px;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  box-shadow: 0 4px 16px rgba(14, 165, 233, 0.25);

  .welcome-text h2 { margin: 0 0 8px; font-size: 22px; }
  .welcome-text p { margin: 0; opacity: 0.9; font-size: 14px; }

  .welcome-info { display: flex; gap: 32px; }
  .info-item { text-align: center; }
  .info-label { display: block; font-size: 12px; opacity: 0.8; margin-bottom: 4px; }
  .info-value { font-size: 16px; font-weight: 600; }
}

.progress-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 28px;

    h3 { margin: 0; font-size: 16px; color: #303133; }
  }

  .step-icon-wrapper {
    cursor: pointer;
    transition: transform 0.2s;
    &:hover { transform: scale(1.15); }
  }
}

.stages-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stage-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  border: 2px solid transparent;
  position: relative;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  }

  &.stage-done {
    border-color: #67c23a;
    .stage-card-footer .stage-action { color: #67c23a; }
  }

  &.stage-current {
    border-color: #409eff;
    background: #f0f7ff;
    .stage-card-footer .stage-action { color: #409eff; font-weight: 600; }
  }

  &.stage-pending {
    opacity: 0.7;
    .stage-card-footer .stage-action { color: #c0c4cc; }
  }

  .stage-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;

    .stage-card-title {
      font-size: 15px;
      font-weight: 600;
      color: #303133;
      flex: 1;
    }
  }

  .stage-card-body {
    font-size: 13px;
    color: #909399;
    margin-bottom: 12px;
    line-height: 1.5;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .stage-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .stage-action {
      font-size: 13px;
    }
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;

  .quick-link {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 16px 8px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: #f5f7fa;
      transform: translateY(-2px);
    }

    span {
      font-size: 13px;
      color: #606266;
    }
  }
}
</style>
