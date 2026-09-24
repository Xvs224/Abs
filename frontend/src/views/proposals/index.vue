<template>
  <div class="proposals-page">
    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="草稿" value="draft" />
            <el-option label="待审核" value="submitted" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索题目/学生/导师"
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

    <!-- 操作栏和表格 -->
    <el-card class="table-card" shadow="never">
      <div class="table-toolbar">
        <div class="toolbar-left">
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
            <el-button type="primary" link @click="handleView(row)">{{ row.topic_title || '-' }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="student_name" label="学生" width="100" />
        <el-table-column prop="teacher_name" label="指导教师" width="100" />
        <el-table-column prop="word_count" label="字数" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submit_time" label="提交时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.submit_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">查看</el-button>
            <template v-if="row.status === 'submitted'">
              <el-button type="success" link size="small" v-if='isTeacher' @click="handleReview(row, 'approved')">
                通过
              </el-button>
              <el-button type="danger" link size="small" v-if='isTeacher' @click="handleReview(row, 'rejected')">
                拒绝
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
      title="开题报告详情"
      width="700px"
    >
      <div v-loading="detailLoading" class="proposal-detail">
        <template v-if="currentDetail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="论文题目" :span="2">{{ currentDetail.topic_title || '-' }}</el-descriptions-item>
            <el-descriptions-item label="学生">{{ currentDetail.student_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="指导教师">{{ currentDetail.teacher_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusTagType(currentDetail.status)" size="small">
                {{ statusLabel(currentDetail.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="字数">{{ currentDetail.word_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="提交时间">{{ formatTime(currentDetail.submit_time) }}</el-descriptions-item>
            <el-descriptions-item label="审核时间" v-if="currentDetail.review_time">{{ formatTime(currentDetail.review_time) }}</el-descriptions-item>
            <el-descriptions-item label="开题报告文档" :span="2">
              <template v-if="currentDetail.file_name">
                <el-button type="primary" link @click="handleDownloadFile(currentDetail)">
                  <el-icon><Document /></el-icon>
                  {{ currentDetail.file_name }}
                </el-button>
              </template>
              <span v-else style="color: #909399">未上传</span>
            </el-descriptions-item>
          </el-descriptions>

          <div class="detail-section">
            <div class="section-title">研究内容</div>
            <div class="section-content">{{ currentDetail.research_content || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">研究方法</div>
            <div class="section-content">{{ currentDetail.research_method || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">技术路线</div>
            <div class="section-content">{{ currentDetail.technical_route || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">预期成果</div>
            <div class="section-content">{{ currentDetail.expected_results || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">进度安排</div>
            <div class="section-content">{{ currentDetail.schedule_plan || '-' }}</div>
          </div>

          <div class="detail-section" v-if="currentDetail.review_opinion">
            <div class="section-title">审核意见</div>
            <div class="section-content review-comment">{{ currentDetail.review_opinion }}</div>
          </div>
        </template>
      </div>
    </el-dialog>

    <!-- 审核对话框 -->
    <el-dialog
      v-model="reviewVisible"
      :title="reviewAction === 'approved' ? '审核通过' : '审核拒绝'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="reviewForm" label-width="80px">
        <el-form-item label="审核意见">
          <el-input
            v-model="reviewForm.comment"
            type="textarea"
            :rows="4"
            :placeholder="reviewAction === 'approved' ? '请输入审核意见（选填）' : '请输入拒绝原因'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button :type="reviewAction === 'approved' ? 'success' : 'danger'" :loading="reviewLoading" v-if='isTeacher' @click="submitReview">
          确认{{ reviewAction === 'approved' ? '通过' : '拒绝' }}
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
const detailVisible = ref(false)
const detailLoading = ref(false)
const reviewVisible = ref(false)
const reviewLoading = ref(false)
const currentRow = ref(null)
const currentDetail = ref(null)
const reviewAction = ref('approved')

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
  comment: ''
})

const statusLabel = (status) => {
  const map = {
    draft: '草稿',
    submitted: '待审核',
    approved: '已通过',
    rejected: '已驳回'
  }
  return map[status] || status
}

const statusTagType = (status) => {
  const map = {
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

const formatTime = (time) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/proposals', {
      page: pagination.page,
      page_size: pagination.page_size,
      status: searchForm.status || undefined,
      keyword: searchForm.keyword || undefined
    })
    tableData.value = res.items || res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载开题列表失败:', error)
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
    const res = await request.get(`/proposals/${row.id}`)
    currentDetail.value = res
  } catch (error) {
    console.error('获取详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该开题报告吗？', '提示', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    try {
      await request.delete(`/proposals/${row.id}`)
      ElMessage.success('删除成功')
      loadList()
    } catch (e) { console.error('删除失败:', e) }
  }).catch(() => {})
}

const handleResubmit = (row) => {
  ElMessageBox.confirm('确定要重置该开题报告为草稿状态吗？', '重交确认', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    try {
      await request.post(`/proposals/${row.id}/resubmit`)
      ElMessage.success('已重置为草稿，可重新提交')
      loadList()
    } catch (e) { console.error('重交失败:', e) }
  }).catch(() => {})
}

const handleReview = (row, action) => {
  currentRow.value = row
  reviewAction.value = action
  reviewForm.comment = ''
  reviewVisible.value = true
}

const submitReview = async () => {
  if (reviewAction.value === 'rejected' && !reviewForm.comment.trim()) {
    ElMessage.warning('请填写拒绝原因')
    return
  }
  try {
    reviewLoading.value = true
    await request.post(`/proposals/${currentRow.value.id}/review`, {
      status: reviewAction.value,
      review_opinion: reviewForm.comment
    })
    ElMessage.success(reviewAction.value === 'approved' ? '审核通过' : '已拒绝')
    reviewVisible.value = false
    loadList()
  } catch (error) {
    console.error('审核失败:', error)
  } finally {
    reviewLoading.value = false
  }
}

const handleDownloadFile = async (row) => {
  if (!row.file_id) {
    ElMessage.warning('文件ID不存在')
    return
  }
  try {
    const response = await request.download(`/files/${row.file_id}/download`)
    const blob = response.data || response
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.download = row.file_name || '开题报告'
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载失败:', error)
  }
}

onMounted(() => {
  loadList()
})
</script>

<style scoped lang="scss">
.proposals-page {
  .search-card {
    margin-bottom: 16px;
  }

  .table-card {
    .table-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: 20px;
    }
  }

  .proposal-detail {
    .detail-section {
      margin-top: 16px;

      .section-title {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 8px;
        padding-left: 8px;
        border-left: 3px solid #409eff;
      }

      .section-content {
        background: #f5f7fa;
        padding: 12px 16px;
        border-radius: 4px;
        line-height: 1.8;
        color: #606266;
        white-space: pre-wrap;
        word-break: break-all;

        &.review-comment {
          background: #fdf6ec;
          color: #e6a23c;
        }
      }
    }
  }
}
</style>
