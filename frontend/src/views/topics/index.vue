<template>
  <div class="topics-page">
    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="已撤回" value="withdrawn" />
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
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增选题</el-button>
          <el-button :icon="RefreshRight" @click="loadList">刷新</el-button>
        </div>
        <div class="toolbar-right">
          <el-button type="warning" :icon="Warning" @click="handleDuplicateCheck">
            重复检测
          </el-button>
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
        <el-table-column prop="title" label="选题名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">{{ row.title }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="student_name" label="学生" width="100" />
        <el-table-column prop="teacher_name" label="指导教师" width="100" />
        <el-table-column prop="department" label="院系" width="140" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <template v-if="row.status === 'pending'">
              <el-button type="success" link size="small" @click="handleReview(row, 'approved')">
                通过
              </el-button>
              <el-button type="danger" link size="small" @click="handleReview(row, 'rejected')">
                拒绝
              </el-button>
            </template>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
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
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="topic-form"
      >
        <el-form-item label="选题名称" prop="title">
          <el-input v-model="formData.title" placeholder="请输入选题名称" />
        </el-form-item>
        <el-form-item label="选题来源" prop="source">
          <el-select v-model="formData.source" placeholder="请选择选题来源" style="width: 100%">
            <el-option label="教师命题" value="teacher" />
            <el-option label="学生自拟" value="student" />
            <el-option label="企业项目" value="enterprise" />
            <el-option label="科研项目" value="research" />
          </el-select>
        </el-form-item>
        <el-form-item label="选题类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择选题类型" style="width: 100%">
            <el-option label="理论研究" value="theory" />
            <el-option label="应用研究" value="application" />
            <el-option label="设计开发" value="design" />
            <el-option label="实验研究" value="experiment" />
          </el-select>
        </el-form-item>
        <el-form-item label="学生" prop="student_id" v-if="userStore.role !== 'student'">
          <el-input v-model="formData.student_id" placeholder="请输入学生学号" />
        </el-form-item>
        <el-form-item label="指导教师" prop="teacher_id" v-if="userStore.role !== 'teacher'">
          <el-input v-model="formData.teacher_id" placeholder="请输入教师工号" />
        </el-form-item>
        <el-form-item label="选题描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入选题描述"
          />
        </el-form-item>
        <el-form-item label="关键词" prop="keywords">
          <el-input v-model="formData.keywords" placeholder="多个关键词用逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="选题详情"
      width="600px"
    >
      <el-descriptions :column="2" border v-if="currentRow">
        <el-descriptions-item label="选题名称" :span="2">{{ currentRow.title }}</el-descriptions-item>
        <el-descriptions-item label="学生">{{ currentRow.student_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="指导教师">{{ currentRow.teacher_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="选题来源">{{ sourceLabel(currentRow.source) }}</el-descriptions-item>
        <el-descriptions-item label="选题类型">{{ typeLabel(currentRow.type) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(currentRow.status)" size="small">
            {{ statusLabel(currentRow.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ formatTime(currentRow.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="关键词" :span="2">{{ currentRow.keywords || '-' }}</el-descriptions-item>
        <el-descriptions-item label="选题描述" :span="2">
          <div class="description-text">{{ currentRow.description || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="审核意见" :span="2" v-if="currentRow.review_comment">
          <div class="description-text">{{ currentRow.review_comment }}</div>
        </el-descriptions-item>
      </el-descriptions>
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

    <!-- 重复检测结果对话框 -->
    <el-dialog
      v-model="duplicateVisible"
      title="重复检测结果"
      width="600px"
    >
      <div v-loading="duplicateLoading">
        <el-alert
          v-if="duplicateResult && duplicateResult.count > 0"
          :title="`检测到 ${duplicateResult.count} 个相似选题`"
          type="warning"
          :closable="false"
          show-icon
          class="mb-20"
        />
        <el-alert
          v-else-if="duplicateResult && duplicateResult.count === 0"
          title="未检测到相似选题"
          type="success"
          :closable="false"
          show-icon
          class="mb-20"
        />
        <el-table v-if="duplicateResult?.items?.length" :data="duplicateResult.items" border>
          <el-table-column prop="title" label="选题名称" show-overflow-tooltip />
          <el-table-column prop="student_name" label="学生" width="100" />
          <el-table-column prop="teacher_name" label="指导教师" width="100" />
          <el-table-column prop="similarity" label="相似度" width="100">
            <template #default="{ row }">
              <el-tag :type="row.similarity > 80 ? 'danger' : row.similarity > 60 ? 'warning' : 'info'" size="small">
                {{ row.similarity }}%
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, RefreshRight, Warning } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { getTopicList, createTopic, updateTopic, deleteTopic, reviewTopic, checkDuplicate } from '@/api/topic'
import dayjs from 'dayjs'

const userStore = useUserStore()
const loading = ref(false)
const dialogVisible = ref(false)
const dialogLoading = ref(false)
const detailVisible = ref(false)
const reviewVisible = ref(false)
const reviewLoading = ref(false)
const duplicateVisible = ref(false)
const duplicateLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const currentRow = ref(null)
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
  source: '',
  type: '',
  student_id: '',
  teacher_id: '',
  description: '',
  keywords: ''
})

const reviewForm = reactive({
  comment: ''
})

const duplicateResult = ref(null)

const formRules = {
  title: [
    { required: true, message: '请输入选题名称', trigger: 'blur' },
    { min: 5, max: 100, message: '长度在 5 到 100 个字符', trigger: 'blur' }
  ],
  source: [
    { required: true, message: '请选择选题来源', trigger: 'change' }
  ],
  type: [
    { required: true, message: '请选择选题类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入选题描述', trigger: 'blur' },
    { min: 10, message: '描述不少于 10 个字符', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑选题' : '新增选题')

const statusLabel = (status) => {
  const map = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    withdrawn: '已撤回'
  }
  return map[status] || status
}

const statusTagType = (status) => {
  const map = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    withdrawn: 'info'
  }
  return map[status] || 'info'
}

const sourceLabel = (source) => {
  const map = {
    teacher: '教师命题',
    student: '学生自拟',
    enterprise: '企业项目',
    research: '科研项目'
  }
  return map[source] || source || '-'
}

const typeLabel = (type) => {
  const map = {
    theory: '理论研究',
    application: '应用研究',
    design: '设计开发',
    experiment: '实验研究'
  }
  return map[type] || type || '-'
}

const formatTime = (time) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await getTopicList({
      page: pagination.page,
      page_size: pagination.page_size,
      status: searchForm.status || undefined,
      keyword: searchForm.keyword || undefined
    })
    tableData.value = res.items || res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载选题列表失败:', error)
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
  formData.source = ''
  formData.type = ''
  formData.student_id = ''
  formData.teacher_id = ''
  formData.description = ''
  formData.keywords = ''
  formRef.value?.resetFields()
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  formData.id = row.id
  formData.title = row.title
  formData.source = row.source
  formData.type = row.type
  formData.student_id = row.student_id
  formData.teacher_id = row.teacher_id
  formData.description = row.description
  formData.keywords = row.keywords
  dialogVisible.value = true
}

const handleView = (row) => {
  currentRow.value = row
  detailVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    dialogLoading.value = true
    if (isEdit.value) {
      await updateTopic(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      await createTopic(formData)
      ElMessage.success('创建成功')
    }
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

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该选题吗？此操作不可恢复。', '删除确认', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteTopic(row.id)
      ElMessage.success('删除成功')
      loadList()
    } catch (error) {
      console.error('删除失败:', error)
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
    await reviewTopic(currentRow.value.id, {
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

const handleDuplicateCheck = async () => {
  duplicateVisible.value = true
  duplicateLoading.value = true
  duplicateResult.value = null
  try {
    const res = await checkDuplicate('')
    duplicateResult.value = res
  } catch (error) {
    console.error('重复检测失败:', error)
  } finally {
    duplicateLoading.value = false
  }
}

onMounted(() => {
  loadList()
})
</script>

<style scoped lang="scss">
.topics-page {
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

  .topic-form {
    padding-right: 20px;
  }

  .description-text {
    white-space: pre-wrap;
    line-height: 1.6;
    color: #606266;
  }

  .mb-20 {
    margin-bottom: 20px;
  }
}
</style>
