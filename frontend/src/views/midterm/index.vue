<template>
  <div class="midterm-page">
    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="草稿" value="draft" />
            <el-option label="待指导" value="form_submitted" />
            <el-option label="已指导" value="guided" />
            <el-option label="待评审" value="ppt_submitted" />
            <el-option label="已通过" value="passed" />
            <el-option label="需整改" value="rectifying" />
            <el-option label="未通过" value="failed" />
            <el-option label="整改完成" value="rectified" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索学生/题目"
            clearable
            style="width: 240px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card class="table-card" shadow="never">
      <div class="table-toolbar">
        <div class="toolbar-left">
          <el-button :icon="RefreshRight" @click="loadList">刷新</el-button>
        </div>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="topic_title" label="论文题目" min-width="180" show-overflow-tooltip />
        <el-table-column prop="student_name" label="学生" width="100" />
        <el-table-column prop="progress_percentage" label="进度" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.progress_percentage || 0" :status="row.progress_percentage >= 80 ? 'success' : row.progress_percentage >= 50 ? '' : 'warning'" />
          </template>
        </el-table-column>
        <el-table-column prop="stage" label="阶段" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.stage === 'ppt' ? 'success' : 'primary'" size="small">
              {{ row.stage === 'ppt' ? 'PPT' : '检查表' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submit_time" label="提交时间" width="160">
          <template #default="{ row }">{{ formatTime(row.submit_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">详情</el-button>
            <el-button v-if="row.status === 'form_submitted' && isTeacher" type="warning" link size="small" @click="handleGuidance(row)">指导</el-button>
            <el-button v-if="(row.status === 'ppt_submitted' || row.status === 'rectified') && isTeacher" type="success" link size="small" @click="handleReview(row)">评审</el-button>
            <el-button v-if="row.status === 'rectifying' && isTeacher" type="danger" link size="small" @click="handleRectification(row)">整改</el-button>
            <!-- 管理员可删除/重交 -->
            <el-button v-if="isAdmin" type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
            <el-button v-if="isAdmin" type="warning" link size="small" @click="handleResubmit(row)">重交</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="中期检查详情" width="750px" top="5vh">
      <div v-loading="detailLoading" class="midterm-detail">
        <template v-if="currentDetail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="论文题目" :span="2">{{ currentDetail.topic_title || '-' }}</el-descriptions-item>
            <el-descriptions-item label="学生">{{ currentDetail.student_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="指导教师">{{ currentDetail.teacher_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="完成进度">
              <el-progress :percentage="currentDetail.progress_percentage || 0" />
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusTagType(currentDetail.status)" size="small">{{ statusLabel(currentDetail.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="中期检查表" :span="2">
              <template v-if="currentDetail.file_name">
                <el-button type="primary" link @click="handleDownload(currentDetail.file_id)">
                  <el-icon><Document /></el-icon> {{ currentDetail.file_name }}
                </el-button>
              </template>
              <span v-else style="color:#909399">未上传</span>
            </el-descriptions-item>
            <el-descriptions-item label="演示文稿(PPT)" :span="2">
              <template v-if="currentDetail.ppt_file_name">
                <el-button type="primary" link @click="handleDownload(currentDetail.ppt_file_id)">
                  <el-icon><Document /></el-icon> {{ currentDetail.ppt_file_name }}
                </el-button>
              </template>
              <span v-else style="color:#909399">未上传</span>
            </el-descriptions-item>
          </el-descriptions>

          <div class="detail-section">
            <div class="section-title">进度描述</div>
            <div class="section-content">{{ currentDetail.progress_description || '-' }}</div>
          </div>
          <div class="detail-section">
            <div class="section-title">已完成工作</div>
            <div class="section-content">{{ currentDetail.completed_work || '-' }}</div>
          </div>
          <div class="detail-section">
            <div class="section-title">剩余工作</div>
            <div class="section-content">{{ currentDetail.remaining_work || '-' }}</div>
          </div>
          <div class="detail-section">
            <div class="section-title">存在问题</div>
            <div class="section-content problem">{{ currentDetail.existing_problems || '-' }}</div>
          </div>
          <div class="detail-section">
            <div class="section-title">后续计划</div>
            <div class="section-content">{{ currentDetail.next_plan || '-' }}</div>
          </div>
          <div class="detail-section" v-if="currentDetail.teacher_guidance">
            <div class="section-title">教师指导意见</div>
            <div class="section-content guidance">{{ currentDetail.teacher_guidance }}</div>
          </div>
          <div class="detail-section" v-if="currentDetail.teacher_opinion">
            <div class="section-title">教师评审意见</div>
            <div class="section-content review">{{ currentDetail.teacher_opinion }}</div>
          </div>
        </template>
      </div>
    </el-dialog>

    <!-- 指导对话框 -->
    <el-dialog v-model="guidanceVisible" title="教师指导" width="500px" :close-on-click-modal="false">
      <el-form :model="guidanceForm" label-width="100px">
        <el-form-item label="指导意见" required>
          <el-input v-model="guidanceForm.teacher_guidance" type="textarea" :rows="6" placeholder="请输入对学生中期进展的指导意见..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="guidanceVisible = false">取消</el-button>
        <el-button type="primary" :loading="guidanceLoading" v-if='isTeacher' @click="submitGuidance">确认指导</el-button>
      </template>
    </el-dialog>

    <!-- 评审对话框 -->
    <el-dialog v-model="reviewVisible" title="中期评审" width="500px" :close-on-click-modal="false">
      <el-form :model="reviewForm" label-width="100px">
        <el-form-item label="评审结果" prop="status">
          <el-radio-group v-model="reviewForm.status">
            <el-radio value="passed">通过</el-radio>
            <el-radio value="rectifying">需整改</el-radio>
            <el-radio value="failed">不通过</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="教师评分">
          <el-input-number v-model="reviewForm.teacher_score" :min="0" :max="100" :precision="1" />
        </el-form-item>
        <el-form-item label="评审意见">
          <el-input v-model="reviewForm.teacher_opinion" type="textarea" :rows="4" placeholder="请输入评审意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewLoading" v-if='isTeacher' @click="submitReview">确认评审</el-button>
      </template>
    </el-dialog>

    <!-- 整改记录对话框 -->
    <el-dialog v-model="rectificationVisible" title="整改记录管理" width="700px">
      <div class="rectification-container">
        <div class="rect-header">
          <span class="rect-title">整改记录列表</span>
          <el-button type="primary" size="small" :icon="Plus" v-if='isTeacher' @click="showAddRectification = true">新增整改要求</el-button>
        </div>
        <el-table :data="rectificationList" v-loading="rectLoading" border size="small">
          <el-table-column prop="problem_description" label="问题描述" min-width="150" show-overflow-tooltip />
          <el-table-column prop="requirement" label="整改要求" min-width="150" show-overflow-tooltip />
          <el-table-column prop="deadline" label="截止日期" width="120">
            <template #default="{ row }">{{ row.deadline ? dayjs(row.deadline).format('YYYY-MM-DD') : '-' }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="rectStatusType(row.status)" size="small">{{ rectStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button v-if="row.status === 'submitted' && isTeacher" type="success" link size="small" @click="handleRecheck(row)">复检</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-divider v-if="showAddRectification" />
      <div v-if="showAddRectification" class="add-rectification">
        <el-form :model="rectForm" label-width="100px">
          <el-form-item label="问题描述">
            <el-input v-model="rectForm.problem_description" type="textarea" :rows="3" placeholder="请输入问题描述" />
          </el-form-item>
          <el-form-item label="整改要求">
            <el-input v-model="rectForm.requirement" type="textarea" :rows="3" placeholder="请输入整改要求" />
          </el-form-item>
          <el-form-item label="截止日期">
            <el-date-picker v-model="rectForm.deadline" type="date" placeholder="选择截止日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="rectSubmitting" size="small" @click="submitRectification">提交</el-button>
            <el-button size="small" v-if='isTeacher' @click="showAddRectification = false">取消</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-dialog v-model="recheckVisible" title="整改复检" width="450px" append-to-body>
        <el-form :model="recheckForm" label-width="80px">
          <el-form-item label="整改内容">
            <div class="rect-content-display">{{ currentRectification?.rectification_content || '-' }}</div>
          </el-form-item>
          <el-form-item label="复检结果">
            <el-radio-group v-model="recheckForm.review_result">
              <el-radio value="passed">通过</el-radio>
              <el-radio value="failed">不通过</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="复检意见">
            <el-input v-model="recheckForm.review_opinion" type="textarea" :rows="3" placeholder="请输入复检意见" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="recheckVisible = false">取消</el-button>
          <el-button type="primary" :loading="recheckLoading" v-if='isTeacher' @click="submitRecheck">确认复检</el-button>
        </template>
      </el-dialog>
    </el-dialog>
  </div>
</template>

<script setup>
import { useUserStore } from '@/store/user' 
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, RefreshRight, Document } from '@element-plus/icons-vue'
import request from '@/utils/request'
import dayjs from 'dayjs'


const userStore = useUserStore()
const isTeacher = computed(() => userStore.userInfo?.role === 'teacher')
const isAdmin = computed(() => userStore.userInfo?.role === 'admin')

const loading = ref(false)
const detailLoading = ref(false)
const detailVisible = ref(false)
const guidanceVisible = ref(false)
const guidanceLoading = ref(false)
const reviewVisible = ref(false)
const reviewLoading = ref(false)
const rectificationVisible = ref(false)
const rectLoading = ref(false)
const rectSubmitting = ref(false)
const showAddRectification = ref(false)
const recheckVisible = ref(false)
const recheckLoading = ref(false)

const currentRow = ref(null)
const currentDetail = ref(null)
const currentRectification = ref(null)

const tableData = ref([])
const pagination = reactive({ page: 1, page_size: 10, total: 0 })
const searchForm = reactive({ status: '', keyword: '' })

const guidanceForm = reactive({ teacher_guidance: '' })
const reviewForm = reactive({ status: 'passed', teacher_opinion: '', teacher_score: null })
const rectificationList = ref([])
const rectForm = reactive({ problem_description: '', requirement: '', deadline: null })
const recheckForm = reactive({ review_result: 'passed', review_opinion: '' })

const statusLabel = (s) => ({
  draft: '草稿', form_submitted: '待指导', guided: '已指导',
  ppt_submitted: '待评审', passed: '已通过', rectifying: '需整改',
  failed: '未通过', rectified: '整改完成'
})[s] || s

const statusTagType = (s) => ({
  draft: 'info', form_submitted: 'warning', guided: 'primary',
  ppt_submitted: 'warning', passed: 'success', rectifying: 'danger',
  failed: 'danger', rectified: 'success'
})[s] || 'info'

const rectStatusText = (s) => ({ pending: '待整改', submitted: '已提交', passed: '已通过', failed: '未通过' })[s] || s
const rectStatusType = (s) => ({ pending: 'warning', submitted: '', passed: 'success', failed: 'danger' })[s] || 'info'
const formatTime = (t) => t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '-'

const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/midterm', {
      page: pagination.page,
      page_size: pagination.page_size,
      status: searchForm.status || undefined,
      keyword: searchForm.keyword || undefined
    })
    tableData.value = res.items || res.data || []
    pagination.total = res.total || 0
  } catch (e) { console.error('加载列表失败:', e) }
  finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadList() }
const handleReset = () => { searchForm.status = ''; searchForm.keyword = ''; pagination.page = 1; loadList() }

const handleView = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  currentDetail.value = null
  try {
    const res = await request.get(`/midterm/${row.id}`)
    currentDetail.value = res
  } catch (e) { console.error('获取详情失败:', e) }
  finally { detailLoading.value = false }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该中期检查记录吗？', '提示', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    try {
      await request.delete(`/midterm/${row.id}`)
      ElMessage.success('删除成功')
      loadList()
    } catch (e) { console.error('删除失败:', e) }
  }).catch(() => {})
}

const handleResubmit = (row) => {
  ElMessageBox.confirm('确定要重置该中期检查为草稿状态吗？', '重交确认', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    try {
      await request.post(`/midterm/${row.id}/resubmit`)
      ElMessage.success('已重置为草稿，可重新提交')
      loadList()
    } catch (e) { console.error('重交失败:', e) }
  }).catch(() => {})
}

const handleGuidance = (row) => {
  currentRow.value = row
  guidanceForm.teacher_guidance = ''
  guidanceVisible.value = true
}

const submitGuidance = async () => {
  if (!guidanceForm.teacher_guidance.trim()) {
    ElMessage.warning('请输入指导意见')
    return
  }
  try {
    guidanceLoading.value = true
    await request.post(`/midterm/${currentRow.value.id}/guidance`, {
      teacher_guidance: guidanceForm.teacher_guidance
    })
    ElMessage.success('指导意见已提交')
    guidanceVisible.value = false
    loadList()
  } catch (e) { console.error('指导失败:', e) }
  finally { guidanceLoading.value = false }
}

const handleReview = (row) => {
  currentRow.value = row
  reviewForm.status = 'passed'
  reviewForm.teacher_opinion = ''
  reviewForm.teacher_score = null
  reviewVisible.value = true
}

const submitReview = async () => {
  try {
    reviewLoading.value = true
    await request.post(`/midterm/${currentRow.value.id}/review`, {
      status: reviewForm.status,
      teacher_opinion: reviewForm.teacher_opinion,
      teacher_score: reviewForm.teacher_score
    })
    ElMessage.success('评审成功')
    reviewVisible.value = false
    loadList()
  } catch (e) { console.error('评审失败:', e) }
  finally { reviewLoading.value = false }
}

const handleDownload = async (fileId) => {
  if (!fileId) return
  try {
    const response = await request.download(`/files/${fileId}/download`)
    const blob = response.data || response
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) { console.error('下载失败:', e) }
}

const handleRectification = async (row) => {
  currentRow.value = row
  rectificationVisible.value = true
  rectLoading.value = true
  showAddRectification.value = false
  await loadRectifications(row.id)
}

const loadRectifications = async (midtermId) => {
  try {
    const res = await request.get('/midterm/rectifications', { midterm_id: midtermId })
    rectificationList.value = res.items || res.data || []
  } catch (e) { console.error('加载整改记录失败:', e) }
  finally { rectLoading.value = false }
}

const submitRectification = async () => {
  if (!rectForm.problem_description.trim()) {
    ElMessage.warning('请输入问题描述')
    return
  }
  try {
    rectSubmitting.value = true
    await request.post('/midterm/rectifications', {
      midterm_id: currentRow.value.id,
      topic_id: currentRow.value.topic_id,
      problem_description: rectForm.problem_description,
      requirement: rectForm.requirement,
      deadline: rectForm.deadline
    })
    ElMessage.success('整改要求已创建')
    rectForm.problem_description = ''
    rectForm.requirement = ''
    rectForm.deadline = null
    showAddRectification.value = false
    await loadRectifications(currentRow.value.id)
  } catch (e) { console.error('创建整改失败:', e) }
  finally { rectSubmitting.value = false }
}

const handleRecheck = (row) => {
  currentRectification.value = row
  recheckForm.review_result = 'passed'
  recheckForm.review_opinion = ''
  recheckVisible.value = true
}

const submitRecheck = async () => {
  try {
    recheckLoading.value = true
    await request.post(`/midterm/rectifications/${currentRectification.value.id}/review`, {
      review_opinion: recheckForm.review_opinion,
      review_result: recheckForm.review_result
    })
    ElMessage.success(recheckForm.review_result === 'passed' ? '复检通过' : '复检不通过')
    recheckVisible.value = false
    await loadRectifications(currentRow.value.id)
  } catch (e) { console.error('复检失败:', e) }
  finally { recheckLoading.value = false }
}

onMounted(loadList)
</script>

<style scoped lang="scss">
.midterm-page {
  .search-card { margin-bottom: 16px; }
  .table-card {
    .table-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 20px; }
  }
  .midterm-detail {
    .detail-section {
      margin-top: 16px;
      .section-title {
        font-size: 14px; font-weight: 600; color: #303133;
        margin-bottom: 8px; padding-left: 8px; border-left: 3px solid #409eff;
      }
      .section-content {
        background: #f5f7fa; padding: 12px 16px; border-radius: 4px;
        line-height: 1.8; color: #606266; white-space: pre-wrap;
        &.problem { background: #fef0f0; color: #f56c6c; }
        &.guidance { background: #ecf5ff; color: #409eff; }
        &.review { background: #fdf6ec; color: #e6a23c; }
      }
    }
  }
  .rectification-container {
    .rect-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; .rect-title { font-size: 14px; font-weight: 600; color: #303133; } }
  }
  .add-rectification { padding-top: 10px; }
  .rect-content-display { background: #f5f7fa; padding: 10px 14px; border-radius: 4px; line-height: 1.6; color: #606266; white-space: pre-wrap; }
}
</style>
