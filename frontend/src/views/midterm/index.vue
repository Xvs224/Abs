<template>
  <div class="midterm-page">
    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="待提交" value="draft" />
            <el-option label="待评审" value="pending" />
            <el-option label="已通过" value="passed" />
            <el-option label="需整改" value="rectification" />
            <el-option label="已完成" value="completed" />
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
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增中期检查</el-button>
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
        <el-table-column prop="title" label="论文题目" min-width="200" show-overflow-tooltip />
        <el-table-column prop="student_name" label="学生" width="100" />
        <el-table-column prop="teacher_name" label="指导教师" width="100" />
        <el-table-column prop="progress" label="完成进度" width="140">
          <template #default="{ row }">
            <el-progress :percentage="row.progress || 0" :status="row.progress >= 80 ? 'success' : row.progress >= 50 ? '' : 'warning'" />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
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
        <el-table-column label="操作" width="260" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">查看详情</el-button>
            <el-button
              v-if="row.status === 'draft' || row.status === 'rectification'"
              type="success"
              link
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              type="warning"
              link
              size="small"
              @click="handleReview(row)"
            >
              评审
            </el-button>
            <el-button
              v-if="row.status === 'rectification'"
              type="danger"
              link
              size="small"
              @click="handleRectification(row)"
            >
              整改记录
            </el-button>
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
      title="中期检查详情"
      width="700px"
    >
      <div v-loading="detailLoading" class="midterm-detail">
        <template v-if="currentDetail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="论文题目" :span="2">{{ currentDetail.title }}</el-descriptions-item>
            <el-descriptions-item label="学生">{{ currentDetail.student_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="指导教师">{{ currentDetail.teacher_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="完成进度">
              <el-progress :percentage="currentDetail.progress || 0" />
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusTagType(currentDetail.status)" size="small">
                {{ statusLabel(currentDetail.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="提交时间" :span="2">{{ formatTime(currentDetail.submitted_at) }}</el-descriptions-item>
          </el-descriptions>

          <div class="detail-section">
            <div class="section-title">已完成工作</div>
            <div class="section-content">{{ currentDetail.completed_work || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">存在问题</div>
            <div class="section-content problem">{{ currentDetail.problems || '-' }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">后续计划</div>
            <div class="section-content">{{ currentDetail.next_plan || '-' }}</div>
          </div>

          <div class="detail-section" v-if="currentDetail.review_comment">
            <div class="section-title">评审意见</div>
            <div class="section-content review">{{ currentDetail.review_comment }}</div>
          </div>
        </template>
      </div>
    </el-dialog>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="midterm-form"
      >
        <el-form-item label="论文题目" prop="title">
          <el-input v-model="formData.title" placeholder="请输入论文题目" />
        </el-form-item>
        <el-form-item label="完成进度" prop="progress">
          <el-slider v-model="formData.progress" :min="0" :max="100" show-input />
        </el-form-item>
        <el-form-item label="已完成工作" prop="completed_work">
          <el-input
            v-model="formData.completed_work"
            type="textarea"
            :rows="4"
            placeholder="请描述已完成的工作内容"
          />
        </el-form-item>
        <el-form-item label="存在问题" prop="problems">
          <el-input
            v-model="formData.problems"
            type="textarea"
            :rows="3"
            placeholder="请描述存在的问题与困难"
          />
        </el-form-item>
        <el-form-item label="后续计划" prop="next_plan">
          <el-input
            v-model="formData.next_plan"
            type="textarea"
            :rows="3"
            placeholder="请描述后续研究计划"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button :loading="dialogLoading" @click="handleSaveDraft">保存草稿</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="handleSubmit">提交评审</el-button>
      </template>
    </el-dialog>

    <!-- 评审对话框 -->
    <el-dialog
      v-model="reviewVisible"
      title="中期评审"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="reviewForm" label-width="80px">
        <el-form-item label="评审结果" prop="result">
          <el-radio-group v-model="reviewForm.result">
            <el-radio value="passed">通过</el-radio>
            <el-radio value="rectification">需整改</el-radio>
            <el-radio value="failed">不通过</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="评审意见" prop="comment">
          <el-input
            v-model="reviewForm.comment"
            type="textarea"
            :rows="4"
            placeholder="请输入评审意见"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewLoading" @click="submitReview">确认评审</el-button>
      </template>
    </el-dialog>

    <!-- 整改记录对话框 -->
    <el-dialog
      v-model="rectificationVisible"
      title="整改记录管理"
      width="650px"
    >
      <div class="rectification-container">
        <div class="rect-header">
          <span class="rect-title">整改记录列表</span>
          <el-button type="primary" size="small" :icon="Plus" @click="showAddRectification = true">
            新增整改
          </el-button>
        </div>
        <el-table :data="rectificationList" v-loading="rectLoading" border size="small">
          <el-table-column prop="content" label="整改内容" min-width="200" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">
                {{ row.status === 'completed' ? '已完成' : '整改中' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="150">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button
                v-if="row.status !== 'completed'"
                type="success"
                link
                size="small"
                @click="handleRecheck(row)"
              >
                复检
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 新增整改表单 -->
      <el-divider v-if="showAddRectification" />
      <div v-if="showAddRectification" class="add-rectification">
        <el-form :model="rectForm" label-width="80px">
          <el-form-item label="整改内容">
            <el-input
              v-model="rectForm.content"
              type="textarea"
              :rows="3"
              placeholder="请输入整改内容"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="rectSubmitting" size="small" @click="submitRectification">
              提交整改
            </el-button>
            <el-button size="small" @click="showAddRectification = false">取消</el-button>
          </el-form-item>
        </el-form>
      </div>
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
const detailLoading = ref(false)
const dialogVisible = ref(false)
const dialogLoading = ref(false)
const detailVisible = ref(false)
const reviewVisible = ref(false)
const reviewLoading = ref(false)
const rectificationVisible = ref(false)
const rectLoading = ref(false)
const rectSubmitting = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const currentRow = ref(null)
const currentDetail = ref(null)
const showAddRectification = ref(false)

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
  progress: 50,
  completed_work: '',
  problems: '',
  next_plan: ''
})

const reviewForm = reactive({
  result: 'passed',
  comment: ''
})

const rectificationList = ref([])
const rectForm = reactive({
  content: ''
})

const formRules = {
  title: [{ required: true, message: '请输入论文题目', trigger: 'blur' }],
  progress: [{ required: true, message: '请设置完成进度', trigger: 'change' }],
  completed_work: [{ required: true, message: '请输入已完成工作', trigger: 'blur' }],
  next_plan: [{ required: true, message: '请输入后续计划', trigger: 'blur' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑中期检查' : '新增中期检查')

const statusLabel = (status) => {
  const map = {
    draft: '待提交',
    pending: '待评审',
    passed: '已通过',
    rectification: '需整改',
    failed: '未通过',
    completed: '已完成'
  }
  return map[status] || status
}

const statusTagType = (status) => {
  const map = {
    draft: 'info',
    pending: 'warning',
    passed: 'success',
    rectification: 'danger',
    failed: 'danger',
    completed: 'success'
  }
  return map[status] || 'info'
}

const formatTime = (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'

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
  } catch (error) {
    console.error('加载中期检查列表失败:', error)
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
  formData.progress = 50
  formData.completed_work = ''
  formData.problems = ''
  formData.next_plan = ''
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
    const res = await request.get(`/midterm/${row.id}`)
    formData.id = res.id
    formData.title = res.title
    formData.progress = res.progress || 50
    formData.completed_work = res.completed_work
    formData.problems = res.problems
    formData.next_plan = res.next_plan
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
    const res = await request.get(`/midterm/${row.id}`)
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
      await request.put(`/midterm/${formData.id}`, data)
    } else {
      await request.post('/midterm', data)
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

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    dialogLoading.value = true
    const data = { ...formData, status: 'pending' }
    if (isEdit.value) {
      await request.put(`/midterm/${formData.id}`, data)
    } else {
      await request.post('/midterm', data)
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

const handleReview = (row) => {
  currentRow.value = row
  reviewForm.result = 'passed'
  reviewForm.comment = ''
  reviewVisible.value = true
}

const submitReview = async () => {
  try {
    reviewLoading.value = true
    await request.post(`/midterm/${currentRow.value.id}/review`, reviewForm)
    ElMessage.success('评审成功')
    reviewVisible.value = false
    loadList()
  } catch (error) {
    console.error('评审失败:', error)
  } finally {
    reviewLoading.value = false
  }
}

const handleRectification = async (row) => {
  currentRow.value = row
  rectificationVisible.value = true
  rectLoading.value = true
  showAddRectification.value = false
  try {
    const res = await request.get(`/midterm/${row.id}/rectifications`)
    rectificationList.value = res.items || res.data || []
  } catch (error) {
    console.error('加载整改记录失败:', error)
  } finally {
    rectLoading.value = false
  }
}

const submitRectification = async () => {
  if (!rectForm.content.trim()) {
    ElMessage.warning('请输入整改内容')
    return
  }
  try {
    rectSubmitting.value = true
    await request.post(`/midterm/${currentRow.value.id}/rectifications`, rectForm)
    ElMessage.success('提交成功')
    rectForm.content = ''
    showAddRectification.value = false
    // 刷新整改列表
    const res = await request.get(`/midterm/${currentRow.value.id}/rectifications`)
    rectificationList.value = res.items || res.data || []
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    rectSubmitting.value = false
  }
}

const handleRecheck = (row) => {
  ElMessageBox.confirm('确认该整改项已完成并通过复检？', '复检确认', {
    confirmButtonText: '确认通过',
    cancelButtonText: '取消',
    type: 'success'
  }).then(async () => {
    try {
      await request.put(`/midterm/rectifications/${row.id}/recheck`, { status: 'completed' })
      ElMessage.success('复检通过')
      const res = await request.get(`/midterm/${currentRow.value.id}/rectifications`)
      rectificationList.value = res.items || res.data || []
    } catch (error) {
      console.error('复检失败:', error)
    }
  }).catch(() => {})
}

onMounted(() => {
  loadList()
})
</script>

<style scoped lang="scss">
.midterm-page {
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

  .midterm-form {
    padding-right: 20px;
  }

  .midterm-detail {
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

        &.problem {
          background: #fef0f0;
          color: #f56c6c;
        }

        &.review {
          background: #ecf5ff;
          color: #409eff;
        }
      }
    }
  }

  .rectification-container {
    .rect-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .rect-title {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
      }
    }
  }

  .add-rectification {
    padding-top: 10px;
  }
}
</style>
