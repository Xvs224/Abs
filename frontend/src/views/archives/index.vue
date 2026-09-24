<template>
  <div class="archives-page">
    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="待审核" value="pending" />
            <el-option label="已归档" value="archived" />
            <el-option label="已退回" value="returned" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索学生/论文题目"
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

    <!-- 列表 -->
    <el-card class="table-card" shadow="never">
      <div class="table-toolbar">
        <div class="toolbar-left">
          <span class="table-title">归档列表</span>
        </div>
        <div class="toolbar-right">
          <el-button :icon="RefreshRight" @click="loadList">刷新</el-button>
        </div>
      </div>

      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="topic_title" label="论文题目" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">{{ row.topic_title }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="student_name" label="学生" width="100" />
        <el-table-column prop="teacher_name" label="指导教师" width="100" />
        <el-table-column prop="final_score" label="答辩成绩" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.final_score !== undefined && row.final_score !== null" :class="scoreClass(row.final_score)">
              {{ row.final_score }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="archive_time" label="归档时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.archive_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">查看详情</el-button>
            <template v-if="row.status === 'pending'">
              <el-button type="success" link size="small" @click="handleApprove(row)">
                通过
              </el-button>
              <el-button type="danger" link size="small" @click="handleReject(row)">
                退回
              </el-button>
            </template>
            <!-- 管理员可删除/重交 -->
            <template v-if="isAdmin">
              <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
              <el-button type="warning" link size="small" @click="handleResubmit(row)">重交</el-button>
            </template>
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
    <el-dialog
      v-model="detailVisible"
      title="归档详情"
      width="700px"
    >
      <div v-loading="detailLoading" class="archive-detail">
        <template v-if="currentDetail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="论文题目" :span="2">{{ currentDetail.topic_title }}</el-descriptions-item>
            <el-descriptions-item label="学生">{{ currentDetail.student_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="学号">{{ currentDetail.student_id || '-' }}</el-descriptions-item>
            <el-descriptions-item label="指导教师">{{ currentDetail.teacher_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="归档编号">{{ currentDetail.archive_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="答辩成绩">
              <span v-if="currentDetail.final_score !== undefined" :class="scoreClass(currentDetail.final_score)">
                {{ currentDetail.final_score }}
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="答辩结果">
              <el-tag :type="finalGradeTagType(currentDetail.final_grade)" size="small">
                {{ finalGradeLabel(currentDetail.final_grade) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="归档状态">
              <el-tag :type="statusTagType(currentDetail.status)" size="small">
                {{ statusLabel(currentDetail.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="归档时间" :span="2">{{ formatTime(currentDetail.archive_time) }}</el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">归档材料</el-divider>
          <div class="archive-files">
            <div v-for="(file, idx) in archiveFileList(currentDetail)" :key="idx" class="file-item">
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ file.name }}</span>
              <el-button type="primary" link size="small" @click="handleDownload(file.path)">下载</el-button>
            </div>
            <el-empty v-if="archiveFileList(currentDetail).length === 0" description="暂无归档材料" :image-size="60" />
          </div>

          <el-divider content-position="left" v-if="currentDetail.return_reason">退回原因</el-divider>
          <div v-if="currentDetail.return_reason" class="review-comment">
            {{ currentDetail.return_reason }}
          </div>
        </template>
      </div>
    </el-dialog>

    <!-- 审核对话框 -->
    <el-dialog
      v-model="reviewVisible"
      :title="reviewAction === 'archived' ? '审核通过' : '退回'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="reviewForm" label-width="80px">
        <el-form-item label="退回原因" v-if="reviewAction === 'returned'">
          <el-input
            v-model="reviewForm.return_reason"
            type="textarea"
            :rows="4"
            placeholder="请输入退回原因"
          />
        </el-form-item>
        <el-form-item label="审核意见" v-else>
          <el-input
            v-model="reviewForm.return_reason"
            type="textarea"
            :rows="4"
            placeholder="请输入审核意见（选填）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button :type="reviewAction === 'archived' ? 'success' : 'danger'" :loading="reviewLoading" v-if='isTeacher' @click="submitReview">
          确认{{ reviewAction === 'archived' ? '通过' : '退回' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { useUserStore } from '@/store/user' 
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, RefreshRight, Document } from '@element-plus/icons-vue'
import request from '@/utils/request'
import dayjs from 'dayjs'


const userStore = useUserStore()
const isTeacher = computed(() => userStore.userInfo?.role === 'teacher')
const isAdmin = computed(() => userStore.userInfo?.role === 'admin')

const loading = ref(false)
const detailLoading = ref(false)
const reviewLoading = ref(false)
const detailVisible = ref(false)
const reviewVisible = ref(false)
const currentDetail = ref(null)
const reviewAction = ref('archived')

const tableData = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const searchForm = reactive({
  status: '',
  keyword: ''
})

const reviewForm = reactive({
  return_reason: ''
})

let currentRow = null

const statusLabel = (status) => {
  const map = {
    pending: '待审核',
    archived: '已归档',
    returned: '已退回'
  }
  return map[status] || status
}

const statusTagType = (status) => {
  const map = {
    pending: 'warning',
    archived: 'success',
    returned: 'danger'
  }
  return map[status] || 'info'
}

const finalGradeLabel = (grade) => {
  const map = {
    excellent: '优秀',
    good: '良好',
    medium: '中等',
    pass: '合格',
    fail: '不合格'
  }
  return map[grade] || grade || '-'
}

const finalGradeTagType = (grade) => {
  const map = {
    excellent: 'success',
    good: 'primary',
    pass: 'info',
    fail: 'danger'
  }
  return map[grade] || 'info'
}

const scoreClass = (score) => {
  if (score >= 90) return 'score-excellent'
  if (score >= 80) return 'score-good'
  if (score >= 60) return 'score-pass'
  return 'score-fail'
}

const formatTime = (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'

const handleDownload = async (filePath) => {
  if (!filePath) {
    ElMessage.warning('文件路径为空')
    return
  }
  try {
    const token = userStore.token || ''
    const url = `/api/files/download?path=${encodeURIComponent(filePath)}`
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
    if (!res.ok) throw new Error('下载失败')
    const blob = await res.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = filePath.split(/[\\/]/).pop() || 'download'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(downloadUrl)
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败：' + (error.message || '未知错误'))
  }
}

const archiveFileList = (detail) => {
  if (!detail) return []
  const files = []
  if (detail.thesis_file) files.push({ name: '最终论文', path: detail.thesis_file })
  if (detail.proposal_file) files.push({ name: '开题报告', path: detail.proposal_file })
  if (detail.midterm_file) files.push({ name: '中期检查', path: detail.midterm_file })
  if (detail.review_file) files.push({ name: '评阅书', path: detail.review_file })
  if (detail.defense_file) files.push({ name: '答辩材料', path: detail.defense_file })
  if (detail.other_materials) files.push({ name: '其他材料', path: detail.other_materials })
  return files
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/archives', {
      page: pagination.page,
      page_size: pagination.page_size,
      status: searchForm.status || undefined,
      keyword: searchForm.keyword || undefined
    })
    tableData.value = res.items || res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载归档列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadList()
}

const handleReset = () => {
  searchForm.status = ''
  searchForm.keyword = ''
  pagination.page = 1
  loadList()
}

const handleView = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  currentDetail.value = null
  try {
    const res = await request.get(`/archives/${row.id}`)
    currentDetail.value = res
  } catch (error) {
    console.error('获取详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该成果归档吗？', '提示', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    try {
      await request.delete(`/archives/${row.id}`)
      ElMessage.success('删除成功')
      loadList()
    } catch (e) { console.error('删除失败:', e) }
  }).catch(() => {})
}

const handleResubmit = (row) => {
  ElMessageBox.confirm('确定要重置该归档为待审核状态吗？', '重交确认', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    try {
      await request.post(`/archives/${row.id}/resubmit`)
      ElMessage.success('已重置，可重新提交')
      loadList()
    } catch (e) { console.error('重交失败:', e) }
  }).catch(() => {})
}

const handleApprove = (row) => {
  currentRow = row
  reviewAction.value = 'archived'
  reviewForm.return_reason = ''
  reviewVisible.value = true
}

const handleReject = (row) => {
  currentRow = row
  reviewAction.value = 'returned'
  reviewForm.return_reason = ''
  reviewVisible.value = true
}

const submitReview = async () => {
  if (reviewAction.value === 'returned' && !reviewForm.return_reason.trim()) {
    ElMessage.warning('请填写退回原因')
    return
  }
  try {
    reviewLoading.value = true
    await request.post(`/archives/${currentRow.id}/review`, {
      status: reviewAction.value,
      return_reason: reviewForm.return_reason
    })
    ElMessage.success(reviewAction.value === 'archived' ? '审核通过' : '已退回')
    reviewVisible.value = false
    loadList()
  } catch (error) {
    console.error('审核失败:', error)
  } finally {
    reviewLoading.value = false
  }
}

onMounted(() => {
  loadList()
})
</script>

<style scoped lang="scss">
.archives-page {
  .search-card {
    margin-bottom: 16px;
  }

  .table-card {
    .table-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      .table-title {
        font-size: 15px;
        font-weight: 600;
        color: #303133;
      }
    }

    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: 20px;
    }
  }

  .archive-detail {
    .archive-files {
      padding: 10px 0;

      .file-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        background: #f5f7fa;
        border-radius: 4px;
        margin-bottom: 8px;

        .el-icon {
          color: #409eff;
          font-size: 18px;
        }

        .file-name {
          flex: 1;
          font-size: 13px;
          color: #303133;
        }

        .file-size {
          font-size: 12px;
          color: #909399;
        }
      }
    }

    .review-comment {
      background: #fdf6ec;
      padding: 12px 16px;
      border-radius: 4px;
      color: #e6a23c;
      line-height: 1.6;
    }
  }

  .text-muted {
    color: #909399;
  }

  .score-excellent {
    color: #67c23a;
    font-weight: 600;
  }

  .score-good {
    color: #409eff;
    font-weight: 600;
  }

  .score-pass {
    color: #e6a23c;
    font-weight: 600;
  }

  .score-fail {
    color: #f56c6c;
    font-weight: 600;
  }
}
</style>
