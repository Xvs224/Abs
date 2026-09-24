<template>
  <div class="student-proposals">
    <StageBanner module-key="proposal" />
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <span>开题报告</span>
          <el-button type="primary" :icon="Plus" @click="openCreate" :disabled="isLocked" v-if="!currentProposal && myTopicId">新建开题报告</el-button>
        </div>
      </template>

      <div v-if="currentProposal">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="论文题目">{{ currentProposal.topic_title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(currentProposal.status)">{{ statusText(currentProposal.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="字数">{{ currentProposal.word_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDate(currentProposal.submit_time) }}</el-descriptions-item>
          <el-descriptions-item label="审核时间">{{ formatDate(currentProposal.review_time) }}</el-descriptions-item>
          <el-descriptions-item label="开题报告文档" :span="2">
            <template v-if="currentProposal.file_name">
              <el-button type="primary" link :icon="Download" @click="handleDownload(currentProposal.file_id)">
                {{ currentProposal.file_name }}
              </el-button>
            </template>
            <span v-else class="no-file">未上传</span>
          </el-descriptions-item>
          <el-descriptions-item label="研究内容" :span="2">{{ currentProposal.research_content || '-' }}</el-descriptions-item>
          <el-descriptions-item label="研究方法" :span="2">{{ currentProposal.research_method || '-' }}</el-descriptions-item>
          <el-descriptions-item label="技术路线" :span="2">{{ currentProposal.technical_route || '-' }}</el-descriptions-item>
          <el-descriptions-item label="预期成果" :span="2">{{ currentProposal.expected_results || '-' }}</el-descriptions-item>
          <el-descriptions-item label="进度安排" :span="2">{{ currentProposal.schedule_plan || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审核意见" :span="2" v-if="currentProposal.review_opinion">
            <span :class="{ 'reject-text': currentProposal.status === 'rejected' }">{{ currentProposal.review_opinion }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <div class="proposal-actions" v-if="canEdit">
          <el-button type="primary" @click="openEdit" :disabled="isLocked">编辑</el-button>
          <el-button type="success" @click="handleSubmit" :disabled="isLocked" v-if="currentProposal.status === 'draft' || currentProposal.status === 'rejected'">提交审核</el-button>
        </div>
      </div>

      <el-empty v-else :description="myTopicId ? '您还未创建开题报告' : '请先完成选题确认，选题通过后才能创建开题报告'">
        <el-button type="primary" @click="openCreate" :disabled="isLocked" v-if="myTopicId">新建开题报告</el-button>
        <el-button type="primary" @click="$router.push('/student/topics')" v-else>去选题</el-button>
      </el-empty>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editMode ? '编辑开题报告' : '新建开题报告'" width="700px" top="5vh">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="研究内容" prop="research_content">
          <el-input type="textarea" v-model="formData.research_content" :rows="4" placeholder="请描述研究内容" />
        </el-form-item>
        <el-form-item label="研究方法" prop="research_method">
          <el-input type="textarea" v-model="formData.research_method" :rows="3" placeholder="请描述研究方法" />
        </el-form-item>
        <el-form-item label="技术路线" prop="technical_route">
          <el-input type="textarea" v-model="formData.technical_route" :rows="3" placeholder="请描述技术路线" />
        </el-form-item>
        <el-form-item label="预期成果" prop="expected_results">
          <el-input type="textarea" v-model="formData.expected_results" :rows="3" placeholder="请描述预期成果" />
        </el-form-item>
        <el-form-item label="进度安排" prop="schedule_plan">
          <el-input type="textarea" v-model="formData.schedule_plan" :rows="4" placeholder="请描述进度安排" />
        </el-form-item>
        <el-form-item label="开题报告" prop="file_id" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :on-exceed="handleExceed"
            :file-list="fileList"
            accept=".doc,.docx,.pdf"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">将开题报告文档拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 doc、docx、pdf 格式，单文件不超过 50MB</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button @click="handleSaveDraft" :disabled="isLocked">保存草稿</el-button>
        <el-button type="primary" @click="handleSubmitForm" :disabled="isLocked">提交审核</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import StageBanner from '@/views/common/StageBanner.vue'
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Download, UploadFilled } from '@element-plus/icons-vue'
import studentApi from '@/api/student'
import { useStageLock } from '@/composables/useStageLock'

const { isLocked } = useStageLock('proposal')

const currentProposal = ref(null)
const dialogVisible = ref(false)
const editMode = ref(false)
const formRef = ref(null)
const uploadRef = ref(null)
const fileList = ref([])
const uploadedFile = ref(null) // { id, file_path, file_name }

const formData = reactive({
  research_content: '', research_method: '', technical_route: '',
  expected_results: '', schedule_plan: '',
  file_id: ''
})

const formRules = {
  research_content: [{ required: true, message: '请输入研究内容', trigger: 'blur' }],
  research_method: [{ required: true, message: '请输入研究方法', trigger: 'blur' }],
  file_id: [{ required: true, message: '请上传开题报告文档', trigger: 'change' }]
}

const canEdit = computed(() => {
  if (!currentProposal.value) return false
  return ['draft', 'rejected'].includes(currentProposal.value.status)
})

const statusText = (s) => ({ draft: '草稿中', submitted: '待审核', approved: '已通过', rejected: '已驳回' })[s] || s
const statusType = (s) => ({ draft: 'info', submitted: 'warning', approved: 'success', rejected: 'danger' })[s] || 'info'
const formatDate = (dt) => dt ? new Date(dt).toLocaleString('zh-CN') : '-'

const myTopicId = ref(null)

const loadProposal = async () => {
  try {
    const [proposalRes, topicRes] = await Promise.all([
      studentApi.getMyProposal(),
      studentApi.getMyTopic()
    ])
    if (proposalRes?.items?.length > 0) {
      currentProposal.value = proposalRes.items[0]
    }
    if (topicRes?.items?.length > 0) {
      myTopicId.value = topicRes.items[0].id
    }
  } catch (e) { /* silent */ }
}

const handleFileChange = (file) => {
  // 校验文件类型
  const fileName = file.name || ''
  const ext = fileName.substring(fileName.lastIndexOf('.')).toLowerCase()
  if (!['.doc', '.docx', '.pdf'].includes(ext)) {
    ElMessage.error('仅支持 doc、docx、pdf 格式')
    fileList.value = []
    formData.file_id = ''
    return
  }
  // 校验文件大小（50MB）
  if (file.size && file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 50MB')
    fileList.value = []
    formData.file_id = ''
    return
  }
  fileList.value = [file]
  formData.file_id = file.name
}

const handleFileRemove = () => {
  fileList.value = []
  uploadedFile.value = null
  formData.file_id = ''
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件，请先移除已选文件')
}

const uploadFileToServer = async () => {
  if (!fileList.value || fileList.value.length === 0) {
    throw new Error('请上传开题报告文档')
  }
  const rawFile = fileList.value[0].raw || fileList.value[0]
  const res = await studentApi.uploadFile(rawFile, 'proposal')
  return {
    id: res.id,
    file_path: res.file_path,
    file_name: res.original_name
  }
}

const openCreate = () => {
  editMode.value = false
  Object.assign(formData, {
    research_content: '', research_method: '', technical_route: '',
    expected_results: '', schedule_plan: '',
    file_id: ''
  })
  fileList.value = []
  uploadedFile.value = null
  dialogVisible.value = true
}

const openEdit = () => {
  editMode.value = true
  Object.assign(formData, {
    research_content: currentProposal.value.research_content || '',
    research_method: currentProposal.value.research_method || '',
    technical_route: currentProposal.value.technical_route || '',
    expected_results: currentProposal.value.expected_results || '',
    schedule_plan: currentProposal.value.schedule_plan || '',
    file_id: currentProposal.value.file_id ? (currentProposal.value.file_name || '已上传') : ''
  })
  // 回显已上传文件
  if (currentProposal.value.file_name) {
    fileList.value = [{
      name: currentProposal.value.file_name,
      url: currentProposal.value.file_path
    }]
    uploadedFile.value = {
      id: currentProposal.value.file_id,
      file_path: currentProposal.value.file_path,
      file_name: currentProposal.value.file_name
    }
  } else {
    fileList.value = []
    uploadedFile.value = null
  }
  dialogVisible.value = true
}

const buildPayload = () => {
  const data = { ...formData, topic_id: myTopicId.value }
  if (uploadedFile.value) {
    data.file_id = uploadedFile.value.id
    data.file_path = uploadedFile.value.file_path
    data.file_name = uploadedFile.value.file_name
  }
  return data
}

const handleSaveDraft = async () => {
  try {
    // 如果有新选择的文件，先上传
    if (fileList.value.length > 0 && !uploadedFile.value) {
      uploadedFile.value = await uploadFileToServer()
    }
    const data = buildPayload()
    if (editMode.value) {
      await studentApi.updateProposal(currentProposal.value.id, data)
    } else {
      await studentApi.createProposal(data)
    }
    ElMessage.success('草稿已保存')
    dialogVisible.value = false
    loadProposal()
  } catch (e) { /* silent */ }
}

const handleSubmitForm = async () => {
  await formRef.value.validate()
  // 提交时必须有文件
  if (fileList.value.length === 0 && !uploadedFile.value) {
    ElMessage.warning('请上传开题报告文档')
    return
  }
  try {
    // 如果有新选择的文件，先上传
    if (fileList.value.length > 0 && !uploadedFile.value) {
      uploadedFile.value = await uploadFileToServer()
    }
    const data = buildPayload()
    if (editMode.value) {
      await studentApi.updateProposal(currentProposal.value.id, data)
      await studentApi.submitProposal(currentProposal.value.id)
    } else {
      const res = await studentApi.createProposal(data)
      if (res?.id) await studentApi.submitProposal(res.id)
    }
    ElMessage.success('开题报告已提交审核')
    dialogVisible.value = false
    loadProposal()
  } catch (e) { /* silent */ }
}

const handleSubmit = async () => {
  try {
    await studentApi.submitProposal(currentProposal.value.id)
    ElMessage.success('已提交审核，等待教师审核')
    loadProposal()
  } catch (e) { /* silent */ }
}

const handleDownload = async (fileId) => {
  if (!fileId) return
  try {
    const response = await studentApi.downloadFile(fileId)
    const blob = response.data || response
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.download = currentProposal.value.file_name || '开题报告'
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('下载失败:', e)
  }
}

onMounted(loadProposal)
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.reject-text { color: #f56c6c; }
.no-file { color: #909399; }

.proposal-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

:deep(.el-upload-dragger) {
  padding: 20px;
}
</style>
