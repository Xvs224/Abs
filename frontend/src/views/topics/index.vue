<template>
  <div class="topics-page">
    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="待选择" value="available" />
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.source_type" placeholder="全部类型" clearable style="width: 140px">
            <el-option label="教师发布" value="teacher" />
            <el-option label="学生自拟" value="student" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索标题/学生"
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
          <el-button type="primary" :icon="Plus" v-if='isTeacher' @click="openPublishDialog">发布选题</el-button>
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
        <el-table-column prop="title" label="选题名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">{{ row.title }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="source_type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.source_type === 'teacher' ? 'primary' : 'success'" size="small">
              {{ row.source_type === 'teacher' ? '教师发布' : '学生自拟' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="student_name" label="选择学生" width="100">
          <template #default="{ row }">
            {{ row.student_name || '-' }}
          </template>
        </el-table-column>
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
        <el-table-column label="操作" width="260" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">详情</el-button>
            <template v-if="row.source_type === 'teacher' && row.status === 'available'">
              <el-button type="warning" link size="small" @click="handleEditPublished(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click="handleDelete(row)">下架</el-button>
            </template>
            <template v-if="row.status === 'pending'">
              <el-button type="success" link size="small" v-if='isTeacher' @click="handleReview(row, 'approved')">
                通过
              </el-button>
              <el-button type="danger" link size="small" v-if='isTeacher' @click="handleReview(row, 'rejected')">
                拒绝
              </el-button>
            </template>
            <template v-if="row.source_type === 'student' && row.status === 'rejected'">
              <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
              <el-button type="warning" link size="small" @click="handleResubmit(row)">重交</el-button>
            </template>
            <!-- 管理员可对任意选题删除/重交 -->
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

    <!-- 发布选题对话框 -->
    <el-dialog
      v-model="publishDialogVisible"
      :title="isEditPublished ? '编辑选题' : '发布选题'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="publishFormRef"
        :model="publishForm"
        :rules="publishFormRules"
        label-width="100px"
        class="topic-form"
      >
        <el-form-item label="选题名称" prop="title">
          <el-input v-model="publishForm.title" placeholder="请输入选题名称" />
        </el-form-item>
        <el-form-item label="研究方向" prop="direction">
          <el-input v-model="publishForm.direction" placeholder="请输入研究方向" />
        </el-form-item>
        <el-form-item label="难度" prop="difficulty">
          <el-radio-group v-model="publishForm.difficulty">
            <el-radio value="easy">简单</el-radio>
            <el-radio value="medium">中等</el-radio>
            <el-radio value="hard">困难</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="工作量" prop="workload">
          <el-radio-group v-model="publishForm.workload">
            <el-radio value="light">较轻</el-radio>
            <el-radio value="medium">中等</el-radio>
            <el-radio value="heavy">较重</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="关键词" prop="keywords">
          <el-input v-model="publishForm.keywords" placeholder="多个关键词用逗号分隔" />
        </el-form-item>
        <el-form-item label="研究背景" prop="background">
          <el-input
            v-model="publishForm.background"
            type="textarea"
            :rows="4"
            placeholder="请输入研究背景"
          />
        </el-form-item>
        <el-form-item label="研究意义" prop="significance">
          <el-input
            v-model="publishForm.significance"
            type="textarea"
            :rows="3"
            placeholder="请输入研究意义"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="publishLoading" v-if='isTeacher' @click="handlePublishSubmit">
          {{ isEditPublished ? '保存' : '发布' }}
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
        <el-descriptions-item label="选题类型">
          <el-tag :type="currentRow.source_type === 'teacher' ? 'primary' : 'success'" size="small">
            {{ currentRow.source_type === 'teacher' ? '教师发布' : '学生自拟' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="学生">{{ currentRow.student_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="研究方向">{{ currentRow.direction || '-' }}</el-descriptions-item>
        <el-descriptions-item label="难度">
          <el-tag size="small">{{ difficultyText(currentRow.difficulty) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(currentRow.status)" size="small">
            {{ statusLabel(currentRow.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="工作量">
          <el-tag size="small">{{ workloadText(currentRow.workload) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ formatTime(currentRow.submit_time) }}</el-descriptions-item>
        <el-descriptions-item label="关键词" :span="2">{{ currentRow.keywords || '-' }}</el-descriptions-item>
        <el-descriptions-item label="研究背景" :span="2">
          <div class="description-text">{{ currentRow.background || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="研究意义" :span="2">
          <div class="description-text">{{ currentRow.significance || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="拒绝原因" :span="2" v-if="currentRow.reject_reason">
          <div class="description-text reject-reason">{{ currentRow.reject_reason }}</div>
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
import { Search, Refresh, Plus, RefreshRight } from '@element-plus/icons-vue'
import { getTopicList, publishTopic, updateTopic, deleteTopic, reviewTopic, resubmitTopic } from '@/api/topic'
import dayjs from 'dayjs'


const userStore = useUserStore()
const isTeacher = computed(() => userStore.userInfo?.role === 'teacher')
const isAdmin = computed(() => userStore.userInfo?.role === 'admin')

const loading = ref(false)
const publishDialogVisible = ref(false)
const publishLoading = ref(false)
const detailVisible = ref(false)
const reviewVisible = ref(false)
const reviewLoading = ref(false)
const publishFormRef = ref(null)
const isEditPublished = ref(false)
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
  source_type: '',
  keyword: ''
})

const publishForm = reactive({
  id: null,
  title: '',
  direction: '',
  difficulty: 'medium',
  workload: 'medium',
  keywords: '',
  background: '',
  significance: ''
})

const reviewForm = reactive({
  comment: ''
})

const publishFormRules = {
  title: [
    { required: true, message: '请输入选题名称', trigger: 'blur' },
    { min: 5, max: 200, message: '长度在 5 到 200 个字符', trigger: 'blur' }
  ],
  background: [
    { required: true, message: '请输入研究背景', trigger: 'blur' }
  ]
}

const statusLabel = (status) => {
  const map = {
    available: '待选择',
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    withdrawn: '已撤回'
  }
  return map[status] || status
}

const statusTagType = (status) => {
  const map = {
    available: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    withdrawn: 'info'
  }
  return map[status] || 'info'
}

const difficultyText = (d) => ({ easy: '简单', medium: '中等', hard: '困难' })[d] || d
const workloadText = (w) => ({ light: '较轻', medium: '中等', heavy: '较重' })[w] || w

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
      source_type: searchForm.source_type || undefined,
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
  searchForm.source_type = ''
  searchForm.keyword = ''
  pagination.page = 1
  loadList()
}

const resetPublishForm = () => {
  publishForm.id = null
  publishForm.title = ''
  publishForm.direction = ''
  publishForm.difficulty = 'medium'
  publishForm.workload = 'medium'
  publishForm.keywords = ''
  publishForm.background = ''
  publishForm.significance = ''
  publishFormRef.value?.resetFields()
}

const openPublishDialog = () => {
  isEditPublished.value = false
  resetPublishForm()
  publishDialogVisible.value = true
}

const handleEditPublished = (row) => {
  isEditPublished.value = true
  publishForm.id = row.id
  publishForm.title = row.title
  publishForm.direction = row.direction
  publishForm.difficulty = row.difficulty
  publishForm.workload = row.workload
  publishForm.keywords = row.keywords
  publishForm.background = row.background
  publishForm.significance = row.significance
  publishDialogVisible.value = true
}

const handlePublishSubmit = async () => {
  if (!publishFormRef.value) return
  try {
    await publishFormRef.value.validate()
    publishLoading.value = true
    if (isEditPublished.value) {
      await updateTopic(publishForm.id, publishForm)
      ElMessage.success('更新成功')
    } else {
      await publishTopic(publishForm)
      ElMessage.success('发布成功')
    }
    publishDialogVisible.value = false
    loadList()
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error)
    }
  } finally {
    publishLoading.value = false
  }
}

const handleView = (row) => {
  currentRow.value = row
  detailVisible.value = true
}

const handleDelete = (row) => {
  const tip = row.source_type === 'teacher' ? '确定要下架该选题吗？' : '确定要删除该选题吗？'
  ElMessageBox.confirm(tip, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteTopic(row.id)
      ElMessage.success('操作成功')
      loadList()
    } catch (error) {
      console.error('操作失败:', error)
    }
  }).catch(() => {})
}

const handleResubmit = (row) => {
  ElMessageBox.confirm('确定要重置该选题为待审核状态吗？', '重交确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await resubmitTopic(row.id)
      ElMessage.success('已重置，可重新提交')
      loadList()
    } catch (error) {
      console.error('重交失败:', error)
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
      reject_reason: reviewForm.comment
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

  .reject-reason {
    color: #f56c6c;
  }
}
</style>
