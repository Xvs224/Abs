<template>
  <div class="student-topics">
    <StageBanner module-key="topic" />
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <span>选题管理</span>
          <div v-if="!currentTopic" class="header-actions">
            <el-button type="primary" :icon="Reading" @click="openSelectDialog" :disabled="isLocked">开始选题</el-button>
            <el-button type="success" :icon="EditPen" @click="openSelfPropose" :disabled="isLocked">自拟选题</el-button>
          </div>
        </div>
      </template>

      <!-- 已有选题 -->
      <div v-if="currentTopic" class="topic-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="选题名称" :span="2">{{ currentTopic.title }}</el-descriptions-item>
          <el-descriptions-item label="选题类型">
            <el-tag :type="currentTopic.source_type === 'teacher' ? 'primary' : 'success'" size="small">
              {{ currentTopic.source_type === 'teacher' ? '教师发布' : '学生自拟' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="指导教师">{{ currentTopic.teacher_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="研究方向">{{ currentTopic.direction || '-' }}</el-descriptions-item>
          <el-descriptions-item label="难度">
            <el-tag size="small">{{ difficultyText(currentTopic.difficulty) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="工作量">
            <el-tag size="small">{{ workloadText(currentTopic.workload) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(currentTopic.status)">{{ statusText(currentTopic.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="关键词">{{ currentTopic.keywords || '-' }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDate(currentTopic.submit_time) }}</el-descriptions-item>
          <el-descriptions-item label="研究背景" :span="2">{{ currentTopic.background || '-' }}</el-descriptions-item>
          <el-descriptions-item label="研究意义" :span="2">{{ currentTopic.significance || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审核意见" :span="2" v-if="currentTopic.reject_reason">
            <span class="reject-reason">{{ currentTopic.reject_reason }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <div class="topic-actions">
          <template v-if="currentTopic.status === 'pending'">
            <el-button type="danger" plain @click="handleCancel" :disabled="isLocked">取消选题</el-button>
          </template>
          <template v-if="currentTopic.status === 'rejected'">
            <el-button type="primary" @click="openEdit" :disabled="isLocked">修改选题</el-button>
            <el-button type="success" @click="handleResubmit" :disabled="isLocked">修改后重新提交</el-button>
            <el-button type="danger" plain @click="handleDelete" :disabled="isLocked">删除选题</el-button>
          </template>
        </div>
      </div>

      <!-- 无选题 -->
      <el-empty v-else description="您还未选择选题，请从下方选择方式开始">
        <div class="empty-actions">
          <el-button type="primary" :icon="Reading" @click="openSelectDialog" :disabled="isLocked" size="large">开始选题</el-button>
          <el-button type="success" :icon="EditPen" @click="openSelfPropose" :disabled="isLocked" size="large">自拟选题</el-button>
        </div>
      </el-empty>
    </el-card>

    <!-- 开始选题 - 可选选题列表 -->
    <el-dialog
      v-model="selectDialogVisible"
      title="选择选题"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="select-search">
        <el-input
          v-model="selectKeyword"
          placeholder="搜索选题名称/研究方向"
          clearable
          style="width: 300px"
          @keyup.enter="loadAvailableTopics"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="loadAvailableTopics">搜索</el-button>
      </div>

      <el-table
        :data="availableTopics"
        v-loading="availableLoading"
        stripe
        border
        style="width: 100%; margin-top: 16px"
        max-height="400"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="title" label="选题名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="teacher_name" label="发布教师" width="100" />
        <el-table-column prop="direction" label="研究方向" width="120" show-overflow-tooltip />
        <el-table-column prop="difficulty" label="难度" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ difficultyText(row.difficulty) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="workload" label="工作量" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ workloadText(row.workload) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleSelect(row)" :disabled="isLocked">选择</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="select-tip" v-if="availableTopics.length === 0 && !availableLoading">
        <el-empty description="暂无可选选题" :image-size="80" />
      </div>

      <template #footer>
        <el-button @click="selectDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 自拟选题对话框 -->
    <el-dialog
      v-model="selfProposeDialogVisible"
      :title="editMode ? '修改选题' : '自拟选题'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="selfFormRef" :model="selfForm" :rules="selfFormRules" label-width="100px">
        <el-form-item label="选题名称" prop="title">
          <el-input v-model="selfForm.title" placeholder="请输入选题名称" />
        </el-form-item>
        <el-form-item label="研究方向" prop="direction">
          <el-input v-model="selfForm.direction" placeholder="请输入研究方向" />
        </el-form-item>
        <el-form-item label="指导教师" prop="teacher_id">
          <el-select v-model="selfForm.teacher_id" placeholder="请选择指导教师（选填）" clearable style="width: 100%">
            <el-option
              v-for="t in teacherList"
              :key="t.id"
              :label="t.real_name"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="难度" prop="difficulty">
          <el-radio-group v-model="selfForm.difficulty">
            <el-radio value="easy">简单</el-radio>
            <el-radio value="medium">中等</el-radio>
            <el-radio value="hard">困难</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="工作量" prop="workload">
          <el-radio-group v-model="selfForm.workload">
            <el-radio value="light">较轻</el-radio>
            <el-radio value="medium">中等</el-radio>
            <el-radio value="heavy">较重</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="关键词" prop="keywords">
          <el-input v-model="selfForm.keywords" placeholder="多个关键词用逗号分隔" />
        </el-form-item>
        <el-form-item label="选题背景" prop="background">
          <el-input type="textarea" v-model="selfForm.background" :rows="3" placeholder="请描述选题背景" />
        </el-form-item>
        <el-form-item label="研究意义" prop="significance">
          <el-input type="textarea" v-model="selfForm.significance" :rows="3" placeholder="请描述研究意义" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="selfProposeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="selfLoading" @click="handleSelfProposeSubmit" :disabled="isLocked">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import StageBanner from '@/views/common/StageBanner.vue'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Reading, EditPen, Search } from '@element-plus/icons-vue'
import studentApi from '@/api/student'
import { useStageLock } from '@/composables/useStageLock'

const { isLocked } = useStageLock('topic')

const currentTopic = ref(null)
const selectDialogVisible = ref(false)
const selfProposeDialogVisible = ref(false)
const editMode = ref(false)
const selfFormRef = ref(null)
const selfLoading = ref(false)
const availableLoading = ref(false)
const availableTopics = ref([])
const selectKeyword = ref('')
const teacherList = ref([])

const selfForm = reactive({
  title: '', direction: '', teacher_id: null, difficulty: 'medium',
  workload: 'medium', keywords: '', background: '', significance: ''
})

const selfFormRules = {
  title: [{ required: true, message: '请输入选题名称', trigger: 'blur' }],
  background: [{ required: true, message: '请输入选题背景', trigger: 'blur' }]
}

const difficultyText = (d) => ({ easy: '简单', medium: '中等', hard: '困难' })[d] || d
const workloadText = (w) => ({ light: '较轻', medium: '中等', heavy: '较重' })[w] || w
const statusText = (s) => ({ available: '待选择', pending: '待审核', approved: '已通过', rejected: '已驳回', withdrawn: '已撤回' })[s] || s
const statusType = (s) => ({ available: 'info', pending: 'warning', approved: 'success', rejected: 'danger', withdrawn: 'info' })[s] || 'info'
const formatDate = (dt) => dt ? new Date(dt).toLocaleString('zh-CN') : '-'

const loadTopic = async () => {
  try {
    const res = await studentApi.getMyTopic()
    if (res?.items?.length > 0) {
      currentTopic.value = res.items[0]
    } else {
      currentTopic.value = null
    }
  } catch (e) { /* silent */ }
}

const loadTeacherList = async () => {
  try {
    // 尝试获取教师列表，如果没有该接口则忽略
    const { getUserList } = await import('@/api/user')
    const res = await getUserList({ role: 'teacher', page_size: 100 })
    teacherList.value = res.items || res.data?.items || []
  } catch (e) {
    teacherList.value = []
  }
}

const loadAvailableTopics = async () => {
  availableLoading.value = true
  try {
    const res = await studentApi.getAvailableTopics({ keyword: selectKeyword.value || undefined })
    availableTopics.value = res.items || []
  } catch (e) {
    availableTopics.value = []
  } finally {
    availableLoading.value = false
  }
}

const openSelectDialog = () => {
  selectKeyword.value = ''
  availableTopics.value = []
  selectDialogVisible.value = true
  loadAvailableTopics()
}

const handleSelect = async (row) => {
  try {
    await ElMessageBox.confirm(`确定选择「${row.title}」作为您的选题吗？`, '确认选择', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    await studentApi.selectTopic(row.id)
    ElMessage.success('选题成功，等待教师审核')
    selectDialogVisible.value = false
    loadTopic()
  } catch (e) {
    if (e !== 'cancel') {
      // 错误已由拦截器处理
    }
  }
}

const openSelfPropose = () => {
  editMode.value = false
  Object.assign(selfForm, {
    title: '', direction: '', teacher_id: null, difficulty: 'medium',
    workload: 'medium', keywords: '', background: '', significance: ''
  })
  loadTeacherList()
  selfProposeDialogVisible.value = true
}

const openEdit = () => {
  editMode.value = true
  Object.assign(selfForm, {
    title: currentTopic.value.title,
    direction: currentTopic.value.direction,
    teacher_id: currentTopic.value.teacher_id,
    difficulty: currentTopic.value.difficulty,
    workload: currentTopic.value.workload,
    keywords: currentTopic.value.keywords,
    background: currentTopic.value.background,
    significance: currentTopic.value.significance
  })
  loadTeacherList()
  selfProposeDialogVisible.value = true
}

const handleSelfProposeSubmit = async () => {
  if (!selfFormRef.value) return
  try {
    await selfFormRef.value.validate()
    selfLoading.value = true
    if (editMode.value) {
      await studentApi.updateTopic(currentTopic.value.id, selfForm)
      ElMessage.success('选题已修改')
    } else {
      await studentApi.selfProposeTopic(selfForm)
      ElMessage.success('选题已提交，等待审核')
    }
    selfProposeDialogVisible.value = false
    loadTopic()
  } catch (e) {
    if (e !== false) {
      // 错误已由拦截器处理
    }
  } finally {
    selfLoading.value = false
  }
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消选择该选题吗？', '提示', { type: 'warning' })
    await studentApi.cancelTopic(currentTopic.value.id)
    ElMessage.success('已取消选题')
    currentTopic.value = null
    loadTopic()
  } catch (e) { /* silent */ }
}

const handleResubmit = async () => {
  try {
    await studentApi.resubmitTopic(currentTopic.value.id)
    ElMessage.success('选题已重新提交，等待审核')
    loadTopic()
  } catch (e) { /* handled by interceptor */ }
}

const handleDelete = async () => {
  await ElMessageBox.confirm('确定要删除此选题吗？', '提示', { type: 'warning' })
  try {
    await studentApi.deleteTopic(currentTopic.value.id)
    ElMessage.success('选题已删除')
    currentTopic.value = null
    loadTopic()
  } catch (e) { /* silent */ }
}

onMounted(loadTopic)
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.topic-detail {
  max-width: 800px;
}

.reject-reason {
  color: #f56c6c;
}

.topic-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

.empty-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 20px;
}

.select-search {
  display: flex;
  gap: 12px;
  align-items: center;
}

.select-tip {
  margin-top: 16px;
}
</style>
