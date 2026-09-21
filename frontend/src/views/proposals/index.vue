<template>
  <div class="proposals-page">
    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="草稿" value="draft" />
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="需修改" value="revision" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索标题/学生/导师"
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
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增开题</el-button>
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
        <el-table-column prop="title" label="论文题目" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">{{ row.title }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="student_name" label="学生" width="100" />
        <el-table-column prop="teacher_name" label="指导教师" width="100" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submitted_at" label="提交时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.submitted_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">查看</el-button>
            <el-button
              v-if="row.status === 'draft' || row.status === 'revision'"
              type="success"
              link
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              type="warning"
              link
              size="small"
              @click="handleSubmit(row)"
            >
              提交
            </el-button>
            <template v-if="row.status === 'pending'">
              <el-button type="success" link size="small" @click="handleReview(row, 'approved')">
                通过
              </el-button>
              <el-button type="danger" link size="small" @click="handleReview(row, 'rejected')">
                拒绝
              </el-button>
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

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="proposal-form"
      >
        <el-form-item label="论文题目" prop="title">
          <el-input v-model="formData.title" placeholder="请输入论文题目" />
        </el-form-item>
        <el-form-item label="选题背景" prop="background">
          <el-input
            v-model="formData.background"
            type="textarea"
            :rows="3"
            placeholder="请输入选题背景与意义"
          />
        </el-form-item>
        <el-form-item label="研究内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="3"
            placeholder="请输入主要研究内容"
          />
        </el-form-item>
        <el-form-item label="研究方法" prop="method">
          <el-input
            v-model="formData.method"
            type="textarea"
            :rows="3"
            placeholder="请输入研究方法与技术路线"
          />
        </el-form-item>
        <el-form-item label="进度安排" prop="schedule">
          <el-input
            v-model="formData.schedule"
            type="textarea"
            :rows="3"
            placeholder="请输入研究进度安排"
          />
        </el-form-item>
        <el-form-item label="预期成果" prop="expected_outcome">
          <el-input
            v-model="formData.expected_outcome"
            type="textarea"
            :rows="2"
            placeholder="请输入预期成果"
          />
        </el-form-item>
        <el-form-item label="参考文献" prop="references">
          <el-input
            v-model="formData.references"
            type="textarea"
            :rows="3"
            placeholder="请输入主要参考文献"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button :loading="dialogLoading" @click="handleSaveDraft">保存草稿</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="handleSubmitForm">
          提交审核
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="开题报告详情"
      width="700px"
    >
      <div v-loading="detailLoading" class="proposal-detail">
        <template v-if="currentDetail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="论文题目" :span="2">{{ currentDetail.title }}</el-descriptions-item>
            <el-descriptions-item label="学生">{{ currentDetail.student_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="指导教师">{{ currentDetail.teacher_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusTagType(currentDetail.status)" size="small">
                {{ statusLabel(currentDetail.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="提交时间">{{ formatTime(currentDetail.submitted_at) }}</el-descriptions-item>
          </el-descriptions>

          <div class="detail-section">
            <div class="section-title">选题背景与意义</div>
            <div class="section-content">{{ currentDetail.background || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">主要研究内容</div>
            <div class="section-content">{{ currentDetail.content || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">研究方法与技术路线</div>
            <div class="section-content">{{ currentDetail.method || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">研究进度安排</div>
            <div class="section-content">{{ currentDetail.schedule || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">预期成果</div>
            <div class="section-content">{{ currentDetail.expected_outcome || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">主要参考文献</div>
            <div class="section-content">{{ currentDetail.references || '-' }}</div>
          </div>

          <div class="detail-section" v-if="currentDetail.review_comment">
            <div class="section-title">审核意见</div>
            <div class="section-content review-comment">{{ currentDetail.review_comment }}</div>
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
        <el-button :type="reviewAction === 'approved' ? 'success' : 'danger'" :loading="reviewLoading" @click="submitReview">
          确认{{ reviewAction === 'approved' ? '通过' : '拒绝' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, RefreshRight } from '@element-plus/icons-vue'
import request from '@/utils/request'
import dayjs from 'dayjs'

const loading = ref(false)
const dialogVisible = ref(false)
const dialogLoading = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const reviewVisible = ref(false)
const reviewLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
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

const formData = reactive({
  id: null,
  title: '',
  background: '',
  content: '',
  method: '',
  schedule: '',
  expected_outcome: '',
  references: ''
})

const reviewForm = reactive({
  comment: ''
})

const formRules = {
  title: [
    { required: true, message: '请输入论文题目', trigger: 'blur' },
    { min: 5, max: 100, message: '长度在 5 到 100 个字符', trigger: 'blur' }
  ],
  background: [
    { required: true, message: '请输入选题背景', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入研究内容', trigger: 'blur' }
  ],
  method: [
    { required: true, message: '请输入研究方法', trigger: 'blur' }
  ],
  schedule: [
    { required: true, message: '请输入进度安排', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑开题报告' : '新增开题报告')

const statusLabel = (status) => {
  const map = {
    draft: '草稿',
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    revision: '需修改'
  }
  return map[status] || status
}

const statusTagType = (status) => {
  const map = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    revision: 'warning'
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

const resetForm = () => {
  formData.id = null
  formData.title = ''
  formData.background = ''
  formData.content = ''
  formData.method = ''
  formData.schedule = ''
  formData.expected_outcome = ''
  formData.references = ''
  formRef.value?.resetFields()
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true
  try {
    const res = await request.get(`/proposals/${row.id}`)
    formData.id = res.id
    formData.title = res.title
    formData.background = res.background
    formData.content = res.content
    formData.method = res.method
    formData.schedule = res.schedule
    formData.expected_outcome = res.expected_outcome
    formData.references = res.references
    dialogVisible.value = true
  } catch (error) {
    console.error('获取详情失败:', error)
  }
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

const handleSaveDraft = async () => {
  try {
    dialogLoading.value = true
    const data = { ...formData, status: 'draft' }
    if (isEdit.value) {
      await request.put(`/proposals/${formData.id}`, data)
    } else {
      await request.post('/proposals', data)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadList()
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    dialogLoading.value = false
  }
}

const handleSubmitForm = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    dialogLoading.value = true
    const data = { ...formData, status: 'pending' }
    if (isEdit.value) {
      await request.put(`/proposals/${formData.id}`, data)
    } else {
      await request.post('/proposals', data)
    }
    ElMessage.success('提交成功')
    dialogVisible.value = false
    loadList()
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error)
    }
  } finally {
    dialogLoading.value = false
  }
}

const handleSubmit = (row) => {
  ElMessageBox.confirm('确定要提交该开题报告审核吗？', '提交确认', {
    confirmButtonText: '确定提交',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await request.put(`/proposals/${row.id}/submit`)
      ElMessage.success('提交成功')
      loadList()
    } catch (error) {
      console.error('提交失败:', error)
    }
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
      comment: reviewForm.comment
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

  .proposal-form {
    padding-right: 20px;

    :deep(.el-textarea__inner) {
      resize: vertical;
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
