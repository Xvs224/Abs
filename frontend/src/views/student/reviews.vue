<template>
  <div class="student-reviews">
    <StageBanner module-key="review" />
    <!-- 评阅结果 -->
    <template v-if="!isDefenseRoute">
      <el-card shadow="never" v-loading="loadingReviews">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>论文评阅</span>
            <div>
              <el-button
                v-if="canApplyReview"
                type="primary"
                size="small"
                @click="openApplyDialog(false)"
              >
                {{ hasReviews ? '申请再次评阅' : '申请评阅' }}
              </el-button>
              <el-button :icon="Refresh" size="small" @click="loadReviews">刷新</el-button>
            </div>
          </div>
        </template>
        <div v-if="reviews.length > 0">
          <el-alert
            v-if="latestReview && (latestReview.result === 'reject' || latestReview.result === 'revision')"
            :title="latestReview.result === 'reject' ? '评阅未通过，请修改论文后申请再次评阅' : '评阅需修改后答辩，请修改论文并申请再次评阅'"
            type="warning"
            :closable="false"
            show-icon
            style="margin-bottom: 16px;"
          />
          <div v-for="item in reviews" :key="item.id" class="review-item">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="状态">
                <el-tag :type="reviewStatusType(item.status)" size="small">{{ reviewStatusText(item.status) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="评阅成绩">
                <span v-if="item.total_score" class="score">{{ item.total_score }} 分</span>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="选题质量">{{ item.topic_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="论文质量">{{ item.content_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="研究方法">{{ item.method_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="创新性">{{ item.innovation_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="格式规范">{{ item.format_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="评阅时间">{{ formatDate(item.review_time) }}</el-descriptions-item>
              <el-descriptions-item label="评阅意见" :span="2" v-if="item.opinion">{{ item.opinion }}</el-descriptions-item>
              <el-descriptions-item label="修改建议" :span="2" v-if="item.suggestions">{{ item.suggestions }}</el-descriptions-item>
              <el-descriptions-item label="评审结论" :span="2" v-if="item.result">
                <el-tag :type="resultType(item.result)" size="small">{{ resultText(item.result) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="评阅意见书" :span="2" v-if="item.review_file_name || item.review_file_path">
                <el-button type="primary" link :icon="Download" @click="handleFileDownload(item.review_file_id, item.review_file_path, item.review_file_name)">
                  {{ item.review_file_name || '下载评阅意见书' }}
                </el-button>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
        <el-empty v-else description="暂无评阅记录，请点击「申请评阅」提交论文评阅申请" />
      </el-card>
    </template>

    <!-- 答辩安排 -->
    <template v-else>
      <el-card shadow="never" v-loading="loadingDefense">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>答辩评价</span>
            <el-button :icon="Refresh" size="small" @click="loadDefense">刷新</el-button>
          </div>
        </template>
        <div v-if="defense">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="状态">
              <el-tag :type="defenseStatusType(defense.status)" size="small">{{ defenseStatusText(defense.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="答辩形式">{{ defenseFormText(defense.defense_form) }}</el-descriptions-item>
            <el-descriptions-item label="答辩日期">{{ formatDate(defense.defense_date) }}</el-descriptions-item>
            <el-descriptions-item label="答辩时间">
              {{ defense.defense_time_start || '-' }} ~ {{ defense.defense_time_end || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="答辩地点" :span="2">{{ defense.location || '-' }}</el-descriptions-item>
            <el-descriptions-item label="答辩委员会" :span="2">{{ defense.committee_member_names || '-' }}</el-descriptions-item>
            <el-descriptions-item label="答辩秘书" :span="2">{{ defense.secretary_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="答辩成绩" v-if="defense.total_score">
              <span class="score">{{ defense.total_score }} 分</span>
            </el-descriptions-item>
            <el-descriptions-item label="成绩等级" v-if="defense.grade">
              <el-tag type="success" size="small">{{ defense.grade }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="答辩评语" :span="2" v-if="defense.opinion">{{ defense.opinion }}</el-descriptions-item>
            <el-descriptions-item label="答辩建议" :span="2" v-if="defense.suggestions">{{ defense.suggestions }}</el-descriptions-item>
            <el-descriptions-item label="答辩结果" :span="2" v-if="defense.result">
              <el-tag :type="defenseResultType(defense.result)" size="small">
                {{ defenseResultText(defense.result) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="答辩记录" :span="2" v-if="defense.defense_file_name || defense.defense_file_path">
              <el-button type="primary" link :icon="Download" @click="handleFileDownload(defense.defense_file_id, defense.defense_file_path, defense.defense_file_name)">
                {{ defense.defense_file_name || '下载答辩记录' }}
              </el-button>
            </el-descriptions-item>
          </el-descriptions>
          <div v-if="defense.result && defense.result !== 'pass'" style="margin-top: 20px; text-align: center;">
            <el-button type="warning" @click="handleApplyRedefense">申请再次答辩</el-button>
          </div>
        </div>
        <el-empty v-else description="暂无答辩安排" />
      </el-card>
    </template>

    <!-- 申请评阅对话框 -->
    <el-dialog v-model="applyDialogVisible" :title="applyDialogTitle" width="560px" :close-on-click-modal="false">
      <el-form label-width="100px">
        <el-form-item label="选择版本" required>
          <el-select v-model="applyForm.version_id" placeholder="请选择待评阅的论文版本" style="width: 100%;" filterable>
            <el-option
              v-for="v in versionList"
              :key="v.id"
              :label="`v${v.version_num} - ${v.file_name || '未命名'}`"
              :value="v.id"
            />
          </el-select>
          <div v-if="versionList.length === 0" style="margin-top: 8px; color: #e6a23c; font-size: 13px;">
            暂无论文版本，请先前往「论文」页面上传论文版本
          </div>
          <div v-else style="margin-top: 8px;">
            <el-button type="primary" link @click="goToUpload">前往上传新版本</el-button>
            <span style="color: #909399; font-size: 12px;">若需提交修改后的论文，请先前往「论文」页面上传新版本</span>
          </div>
        </el-form-item>
        <el-alert
          v-if="latestReview && (latestReview.result === 'reject' || latestReview.result === 'revision')"
          :title="`上次评阅结果：${resultText(latestReview.result)}。请确认已根据修改建议上传新版本后再申请。`"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>
      <template #footer>
        <el-button @click="applyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="applyLoading" :disabled="!applyForm.version_id" @click="submitApply">
          提交申请
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import StageBanner from '@/views/common/StageBanner.vue'
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import studentApi from '@/api/student'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()
// 根据路由路径决定显示评阅还是答辩
const isDefenseRoute = computed(() => route.path.includes('/defense'))

const reviews = ref([])
const defense = ref(null)
const loadingReviews = ref(false)
const loadingDefense = ref(false)
let timer = null

// 申请评阅相关
const applyDialogVisible = ref(false)
const applyLoading = ref(false)
const applyForm = ref({ version_id: null })
const versionList = ref([])

// 最新一条评阅记录
const latestReview = computed(() => {
  if (reviews.value.length === 0) return null
  return reviews.value.reduce((latest, r) => (r.id > latest.id ? r : latest), reviews.value[0])
})

const hasReviews = computed(() => reviews.value.length > 0)

// 是否可以申请评阅：
// - 无评阅记录 → 可申请
// - 最新评阅为 reject/revision → 可再次申请
// - 最新评阅为 pending/reviewing → 不可申请（等待中）
// - 最新评阅为 pass → 不可申请（已通过）
const canApplyReview = computed(() => {
  if (!hasReviews.value) return true
  const r = latestReview.value
  if (!r) return true
  if (r.status === 'pending' || r.status === 'reviewing') return false
  if (r.result === 'pass') return false
  return r.result === 'reject' || r.result === 'revision'
})

const applyDialogTitle = computed(() => hasReviews.value ? '申请再次评阅' : '申请评阅')

const formatDate = (dt) => dt ? new Date(dt).toLocaleDateString('zh-CN') : '-'

// 下载评阅意见书 / 答辩记录
const handleFileDownload = async (fileId, filePath, fileName) => {
  if (!fileId && !filePath) return
  try {
    let blob
    if (fileId) {
      const res = await studentApi.downloadFile(fileId)
      blob = res.data || res
    } else {
      const res = await request.get('/files/download', { path: filePath }, { responseType: 'blob' })
      blob = res.data || res
    }
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    if (fileName) link.download = fileName
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('下载失败:', e)
  }
}

const reviewStatusText = (s) => ({ pending: '待评阅', reviewing: '评阅中', completed: '已完成' })[s] || s
const reviewStatusType = (s) => ({ pending: 'info', reviewing: 'warning', completed: 'success' })[s] || 'info'

const resultText = (r) => ({ pass: '同意答辩', revision: '修改后答辩', reject: '不同意答辩' })[r] || r
const resultType = (r) => ({ pass: 'success', revision: 'warning', reject: 'danger' })[r] || 'info'

const defenseStatusText = (s) => ({ scheduled: '已安排', completed: '已完成', pending: '待安排', in_progress: '进行中' })[s] || s
const defenseStatusType = (s) => ({ scheduled: 'warning', completed: 'success', pending: 'info', in_progress: 'warning' })[s] || 'info'
const defenseFormText = (f) => ({ offline: '线下答辩', online: '线上答辩' })[f] || f || '-'

const defenseResultText = (r) => ({ pass: '通过', fail: '未通过', reargue: '需重新答辩' })[r] || r
const defenseResultType = (r) => ({ pass: 'success', fail: 'danger', reargue: 'warning' })[r] || 'info'

const loadReviews = async () => {
  loadingReviews.value = true
  try {
    const res = await studentApi.getMyReviews()
    reviews.value = res?.items || []
  } catch (e) { /* silent */ }
  finally { loadingReviews.value = false }
}

const loadDefense = async () => {
  loadingDefense.value = true
  try {
    const res = await studentApi.getMyDefenses()
    defense.value = res?.items?.[0] || null
  } catch (e) { /* silent */ }
  finally { loadingDefense.value = false }
}

const handleApplyRedefense = async () => {
  try {
    await ElMessageBox.confirm('确认要申请再次答辩吗？申请后请等待教师安排答辩。', '申请再次答辩', {
      confirmButtonText: '确认申请',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await studentApi.applyRedefense()
    ElMessage.success('再次答辩申请已提交，请等待教师安排答辩')
    loadDefense()
  } catch (e) {
    // 错误信息由拦截器统一提示
  }
}

const loadVersions = async () => {
  try {
    const res = await studentApi.getMyThesisVersions({ page_size: 50 })
    versionList.value = res?.items || []
  } catch (e) {
    console.error('加载论文版本失败:', e)
    versionList.value = []
  }
}

const openApplyDialog = async () => {
  await loadVersions()
  applyForm.value.version_id = null
  applyDialogVisible.value = true
}

const goToUpload = () => {
  applyDialogVisible.value = false
  router.push('/student/thesis')
}

const submitApply = async () => {
  if (!applyForm.value.version_id) {
    ElMessage.warning('请选择论文版本')
    return
  }
  // 若选择的版本与上次评阅使用的版本相同，提醒学生确认
  if (latestReview.value && latestReview.value.version_id === applyForm.value.version_id) {
    try {
      await ElMessageBox.confirm(
        '确认要使用该版本再次申请评阅吗？',
        '版本确认',
        { confirmButtonText: '确认提交', cancelButtonText: '取消', type: 'warning' }
      )
    } catch {
      return
    }
  }
  applyLoading.value = true
  try {
    await studentApi.applyReview(applyForm.value.version_id)
    ElMessage.success('评阅申请已提交，请等待评阅教师评阅')
    applyDialogVisible.value = false
    loadReviews()
  } catch (e) {
    // 错误信息由拦截器统一提示
  } finally {
    applyLoading.value = false
  }
}

// 根据当前路由加载对应数据
const loadCurrentData = () => {
  if (isDefenseRoute.value) {
    loadDefense()
  } else {
    loadReviews()
  }
}

// 路由切换时重新加载
watch(isDefenseRoute, loadCurrentData)

onMounted(() => {
  loadCurrentData()
  // 每30秒自动刷新，确保教师提交评阅后学生端状态能自动同步
  timer = setInterval(loadCurrentData, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped lang="scss">
.review-item {
  margin-bottom: 20px;
}

.score {
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
}
</style>
