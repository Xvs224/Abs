<template>
  <div class="student-midterm">
    <StageBanner module-key="midterm" />
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <span>中期检查</span>
          <el-button type="primary" :icon="Plus" @click="openCreate" :disabled="isLocked" v-if="!currentMidterm">新建中期检查</el-button>
        </div>
      </template>

      <!-- 阶段流程指示器 -->
      <el-steps :active="stepActive" finish-status="success" align-center class="step-bar">
        <el-step title="中期检查表" description="填写并提交检查表" />
        <el-step title="教师指导" description="教师给出指导意见" />
        <el-step title="提交PPT" description="上传演示文稿" />
        <el-step title="最终评审" description="教师最终评审" />
      </el-steps>

      <div v-if="currentMidterm">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="论文题目">{{ currentMidterm.topic_title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(currentMidterm.status)">{{ statusText(currentMidterm.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="完成进度" :span="2">
            <el-progress :percentage="currentMidterm.progress_percentage || 0" :stroke-width="10" />
          </el-descriptions-item>

          <!-- 阶段1：中期检查表 -->
          <el-descriptions-item label="中期检查表" :span="2">
            <template v-if="currentMidterm.file_name">
              <el-button type="primary" link :icon="Download" @click="handleDownload(currentMidterm.file_id, currentMidterm.file_name)">
                {{ currentMidterm.file_name }}
              </el-button>
            </template>
            <span v-else style="color:#909399">未上传</span>
          </el-descriptions-item>
          <el-descriptions-item label="进度描述" :span="2">{{ currentMidterm.progress_description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="已完成工作" :span="2">{{ currentMidterm.completed_work || '-' }}</el-descriptions-item>
          <el-descriptions-item label="剩余工作" :span="2">{{ currentMidterm.remaining_work || '-' }}</el-descriptions-item>
          <el-descriptions-item label="存在问题" :span="2">{{ currentMidterm.existing_problems || '-' }}</el-descriptions-item>
          <el-descriptions-item label="后续计划" :span="2">{{ currentMidterm.next_plan || '-' }}</el-descriptions-item>

          <!-- 教师指导意见 -->
          <el-descriptions-item label="教师指导意见" :span="2" v-if="currentMidterm.teacher_guidance">
            <div class="guidance-text">{{ currentMidterm.teacher_guidance }}</div>
          </el-descriptions-item>

          <!-- 阶段2：PPT -->
          <el-descriptions-item label="演示文稿(PPT)" :span="2">
            <template v-if="currentMidterm.ppt_file_name">
              <el-button type="primary" link :icon="Download" @click="handleDownload(currentMidterm.ppt_file_id, currentMidterm.ppt_file_name)">
                {{ currentMidterm.ppt_file_name }}
              </el-button>
            </template>
            <span v-else style="color:#e6a23c">
              <el-icon><Warning /></el-icon> 需上交演示文稿(PPT)，教师指导后可上传
            </span>
          </el-descriptions-item>

          <el-descriptions-item label="教师评分">{{ currentMidterm.teacher_score || '-' }}</el-descriptions-item>
          <el-descriptions-item label="最终成绩">{{ currentMidterm.final_score || '-' }}</el-descriptions-item>
          <el-descriptions-item label="评审时间">{{ formatDate(currentMidterm.check_time) }}</el-descriptions-item>
          <el-descriptions-item label="教师评审意见" :span="2" v-if="currentMidterm.teacher_opinion">
            {{ currentMidterm.teacher_opinion }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- PPT上交提示 -->
        <el-alert
          v-if="currentMidterm.status === 'guided' && !currentMidterm.ppt_file_name"
          type="warning"
          :closable="false"
          show-icon
          class="ppt-tip"
          title="请上交演示文稿(PPT)"
          description="教师已完成指导，请及时上传中期检查演示文稿(PPT)，提交后进入最终评审阶段。支持 ppt、pptx 格式。"
        />

        <!-- 操作按钮区 -->
        <div class="midterm-actions" v-if="canEdit">
          <el-button type="primary" @click="openEdit" :disabled="isLocked" v-if="showEditBtn">编辑检查表</el-button>
          <el-button type="success" @click="handleSubmit" :disabled="isLocked" v-if="currentMidterm.status === 'draft'">提交检查表</el-button>
          <el-button type="warning" @click="openPPTUpload" :disabled="isLocked" v-if="currentMidterm.status === 'guided'">上传PPT</el-button>
        </div>

        <!-- 整改任务 -->
        <div class="rectification-section" v-if="['rectifying', 'rectified'].includes(currentMidterm.status)">
          <h4>整改任务</h4>
          <el-table :data="rectifications" stripe size="small" v-loading="loadingRect">
            <el-table-column prop="problem_description" label="问题描述" min-width="140" show-overflow-tooltip />
            <el-table-column prop="requirement" label="整改要求" min-width="140" show-overflow-tooltip />
            <el-table-column prop="rectification_content" label="整改内容" min-width="140" show-overflow-tooltip />
            <el-table-column label="整改PPT" width="120">
              <template #default="{ row }">
                <el-button
                  v-if="row.rectification_ppt_name"
                  type="primary" link size="small"
                  @click="handleRectPPTDownload(row)"
                >{{ row.rectification_ppt_name }}</el-button>
                <span v-else style="color:#909399">未上传</span>
              </template>
            </el-table-column>
            <el-table-column label="整改材料" width="120">
              <template #default="{ row }">
                <el-button
                  v-if="row.rectification_file_name"
                  type="primary" link size="small"
                  @click="handleRectFileDownload(row)"
                >{{ row.rectification_file_name }}</el-button>
                <span v-else style="color:#909399">未上传</span>
              </template>
            </el-table-column>
            <el-table-column prop="deadline" label="截止日期" width="110">
              <template #default="{ row }">{{ formatDate(row.deadline) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="rectStatusType(row.status)" size="small">{{ rectStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button
                  v-if="row.status === 'pending'"
                  text type="primary" size="small"
                  @click="openRectSubmit(row)"
                  :disabled="isLocked"
                >提交整改</el-button>
                <span v-else style="color:#909399">-</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <el-empty v-else description="您还未创建中期检查">
        <el-button type="primary" @click="openCreate" :disabled="isLocked">新建中期检查</el-button>
      </el-empty>
    </el-card>

    <!-- 中期检查表编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editMode ? '编辑中期检查表' : '新建中期检查表'" width="700px" top="5vh">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px;"
        title="中期检查流程说明"
        description="1. 填写并提交中期检查表 → 2. 等待教师指导 → 3. 上交演示文稿(PPT) → 4. 教师最终评审"
      />
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="完成进度" prop="progress_percentage">
          <el-slider v-model="formData.progress_percentage" :max="100" show-input />
        </el-form-item>
        <el-form-item label="进度描述" prop="progress_description">
          <el-input type="textarea" v-model="formData.progress_description" :rows="3" placeholder="请描述毕业设计的整体进展情况" />
        </el-form-item>
        <el-form-item label="已完成工作" prop="completed_work">
          <el-input type="textarea" v-model="formData.completed_work" :rows="3" placeholder="请描述已完成的工作" />
        </el-form-item>
        <el-form-item label="剩余工作" prop="remaining_work">
          <el-input type="textarea" v-model="formData.remaining_work" :rows="3" placeholder="请描述尚需完成的工作" />
        </el-form-item>
        <el-form-item label="存在问题" prop="existing_problems">
          <el-input type="textarea" v-model="formData.existing_problems" :rows="3" placeholder="请描述当前存在的问题" />
        </el-form-item>
        <el-form-item label="后续计划" prop="next_plan">
          <el-input type="textarea" v-model="formData.next_plan" :rows="3" placeholder="请描述后续工作计划" />
        </el-form-item>
        <el-form-item label="中期检查表" prop="file_id" required>
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="fileList"
            accept=".doc,.docx,.pdf"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">将中期检查表拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 doc、docx、pdf 格式</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button @click="handleSaveDraft" :disabled="isLocked">保存草稿</el-button>
        <el-button type="primary" @click="handleSubmitForm" :disabled="isLocked">提交检查表</el-button>
      </template>
    </el-dialog>

    <!-- PPT上传对话框 -->
    <el-dialog v-model="pptDialogVisible" title="上传中期检查演示文稿(PPT)" width="500px" top="10vh">
      <el-upload
        :auto-upload="false"
        :limit="1"
        :on-change="handlePPTChange"
        :on-remove="handlePPTRemove"
        :file-list="pptFileList"
        accept=".ppt,.pptx"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将PPT文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 ppt、pptx 格式</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="pptDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="pptSubmitting" @click="handlePPTSubmit" :disabled="isLocked">提交PPT</el-button>
      </template>
    </el-dialog>

    <!-- 整改对话框 -->
    <el-dialog v-model="rectDialogVisible" title="提交整改材料" width="560px">
      <el-form ref="rectFormRef" :model="rectForm" :rules="rectFormRules" label-width="100px">
        <el-form-item label="问题描述">
          <span>{{ rectForm.problem_description }}</span>
        </el-form-item>
        <el-form-item label="整改要求">
          <span>{{ rectForm.requirement }}</span>
        </el-form-item>
        <el-form-item label="整改内容" prop="rectification_content">
          <el-input type="textarea" v-model="rectForm.rectification_content" :rows="4" placeholder="请详细描述整改情况" />
        </el-form-item>
        <el-form-item label="整改PPT">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="handleRectPPTChange"
            :on-remove="handleRectPPTRemove"
            :file-list="rectPPTList"
            accept=".ppt,.pptx"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">将整改PPT拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 ppt、pptx 格式（可选，如PPT需要修改请上传）</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="整改材料">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="handleRectFileChange"
            :on-remove="handleRectFileRemove"
            :file-list="rectFileList"
            accept=".doc,.docx,.pdf,.zip,.rar"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">将整改材料拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 doc、docx、pdf、zip、rar 格式（可选）</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rectDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="rectSubmitting" @click="handleRectSubmit" :disabled="isLocked">提交整改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import StageBanner from '@/views/common/StageBanner.vue'
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Download, UploadFilled, Warning } from '@element-plus/icons-vue'
import studentApi from '@/api/student'
import request from '@/utils/request'
import { useStageLock } from '@/composables/useStageLock'

const { isLocked } = useStageLock('midterm')

const currentMidterm = ref(null)
const rectifications = ref([])
const loadingRect = ref(false)
const dialogVisible = ref(false)
const pptDialogVisible = ref(false)
const editMode = ref(false)
const formRef = ref(null)
const rectDialogVisible = ref(false)
const rectFormRef = ref(null)
const fileList = ref([])
const uploadedFile = ref(null)
const pptFileList = ref([])
const uploadedPPT = ref(null)
const pptSubmitting = ref(false)

const formData = reactive({
  progress_percentage: 0,
  progress_description: '',
  completed_work: '',
  remaining_work: '',
  existing_problems: '',
  next_plan: '',
  file_id: ''
})

const formRules = {
  completed_work: [{ required: true, message: '请输入已完成工作', trigger: 'blur' }],
  file_id: [{ required: true, message: '请上传中期检查表', trigger: 'change' }]
}

const rectForm = reactive({
  id: null,
  problem_description: '',
  requirement: '',
  rectification_content: ''
})

const rectFormRules = {
  rectification_content: [{ required: true, message: '请输入整改内容', trigger: 'blur' }]
}

const rectFileList = ref([])
const uploadedRectFile = ref(null)
const rectPPTList = ref([])
const uploadedRectPPT = ref(null)
const rectSubmitting = ref(false)

const stepActive = computed(() => {
  if (!currentMidterm.value) return 0
  const map = { draft: 0, form_submitted: 1, guided: 2, ppt_submitted: 3, passed: 3, failed: 3, rectifying: 3, rectified: 3 }
  return map[currentMidterm.value.status] ?? 0
})

const canEdit = computed(() => {
  if (!currentMidterm.value) return false
  return ['draft', 'guided', 'rectifying', 'failed', 'rectified'].includes(currentMidterm.value.status)
})

const showEditBtn = computed(() => {
  if (!currentMidterm.value) return false
  return ['draft', 'failed', 'rectified'].includes(currentMidterm.value.status)
})

const statusText = (s) => ({
  draft: '草稿中', form_submitted: '待指导', guided: '已指导，待提交PPT',
  ppt_submitted: '待评审', passed: '已通过', rectifying: '需整改',
  failed: '未通过', rectified: '整改完成'
})[s] || s

const statusType = (s) => ({
  draft: 'info', form_submitted: 'warning', guided: '', ppt_submitted: 'warning',
  passed: 'success', rectifying: 'warning', failed: 'danger', rectified: 'success'
})[s] || 'info'

const rectStatusText = (s) => ({ pending: '待整改', submitted: '已提交', passed: '已通过', failed: '未通过' })[s] || s
const rectStatusType = (s) => ({ pending: 'warning', submitted: 'info', passed: 'success', failed: 'danger' })[s] || 'info'
const formatDate = (dt) => dt ? new Date(dt).toLocaleDateString('zh-CN') : '-'

const myTopicId = ref(null)

const loadMidterm = async () => {
  try {
    const [midtermRes, topicRes] = await Promise.all([
      studentApi.getMyMidterm(),
      studentApi.getMyTopic()
    ])
    if (midtermRes?.items?.length > 0) {
      currentMidterm.value = midtermRes.items[0]
      if (['rectifying', 'rectified'].includes(currentMidterm.value.status)) {
        loadRectifications(currentMidterm.value.id)
      }
    }
    if (topicRes?.items?.length > 0) {
      myTopicId.value = topicRes.items[0].id
    }
  } catch (e) { /* silent */ }
}

const loadRectifications = async (midtermId) => {
  loadingRect.value = true
  try {
    const res = await studentApi.getMyRectifications({ midterm_id: midtermId })
    rectifications.value = res?.items || []
  } catch (e) { /* silent */ }
  finally { loadingRect.value = false }
}

const handleFileChange = (file) => {
  const ext = (file.name || '').substring((file.name || '').lastIndexOf('.')).toLowerCase()
  if (!['.doc', '.docx', '.pdf'].includes(ext)) {
    ElMessage.error('仅支持 doc、docx、pdf 格式')
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

const handlePPTChange = (file) => {
  const ext = (file.name || '').substring((file.name || '').lastIndexOf('.')).toLowerCase()
  if (!['.ppt', '.pptx'].includes(ext)) {
    ElMessage.error('仅支持 ppt、pptx 格式')
    pptFileList.value = []
    return
  }
  pptFileList.value = [file]
}

const handlePPTRemove = () => {
  pptFileList.value = []
  uploadedPPT.value = null
}

const uploadFileToServer = async (fileList, module) => {
  if (!fileList.value || fileList.value.length === 0) {
    throw new Error('请选择文件')
  }
  const rawFile = fileList.value[0].raw || fileList.value[0]
  const res = await studentApi.uploadFile(rawFile, module)
  return { id: res.id, file_path: res.file_path, file_name: res.original_name }
}

const openCreate = () => {
  editMode.value = false
  Object.assign(formData, { progress_percentage: 0, progress_description: '', completed_work: '', remaining_work: '', existing_problems: '', next_plan: '', file_id: '' })
  fileList.value = []
  uploadedFile.value = null
  dialogVisible.value = true
}

const openEdit = () => {
  editMode.value = true
  Object.assign(formData, {
    progress_percentage: currentMidterm.value.progress_percentage || 0,
    progress_description: currentMidterm.value.progress_description || '',
    completed_work: currentMidterm.value.completed_work || '',
    remaining_work: currentMidterm.value.remaining_work || '',
    existing_problems: currentMidterm.value.existing_problems || '',
    next_plan: currentMidterm.value.next_plan || '',
    file_id: currentMidterm.value.file_id ? (currentMidterm.value.file_name || '已上传') : ''
  })
  if (currentMidterm.value.file_name) {
    fileList.value = [{ name: currentMidterm.value.file_name, url: currentMidterm.value.file_path }]
    uploadedFile.value = {
      id: currentMidterm.value.file_id,
      file_path: currentMidterm.value.file_path,
      file_name: currentMidterm.value.file_name
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
    if (fileList.value.length > 0 && !uploadedFile.value) {
      uploadedFile.value = await uploadFileToServer(fileList, 'midterm')
    }
    const data = buildPayload()
    if (editMode.value) {
      await studentApi.updateMidterm(currentMidterm.value.id, data)
    } else {
      await studentApi.createMidterm(data)
    }
    ElMessage.success('草稿已保存')
    dialogVisible.value = false
    loadMidterm()
  } catch (e) { /* silent */ }
}

const handleSubmitForm = async () => {
  await formRef.value.validate()
  if (fileList.value.length === 0 && !uploadedFile.value) {
    ElMessage.warning('请上传中期检查表')
    return
  }
  try {
    if (fileList.value.length > 0 && !uploadedFile.value) {
      uploadedFile.value = await uploadFileToServer(fileList, 'midterm')
    }
    const data = buildPayload()
    if (editMode.value) {
      await studentApi.updateMidterm(currentMidterm.value.id, data)
      await studentApi.submitMidterm(currentMidterm.value.id)
    } else {
      const res = await studentApi.createMidterm(data)
      if (res?.id) await studentApi.submitMidterm(res.id)
    }
    ElMessage.success('中期检查表已提交，等待教师指导')
    dialogVisible.value = false
    loadMidterm()
  } catch (e) { /* silent */ }
}

const handleSubmit = async () => {
  try {
    await studentApi.submitMidterm(currentMidterm.value.id)
    ElMessage.success('中期检查表已提交，等待教师指导')
    loadMidterm()
  } catch (e) { /* silent */ }
}

const openPPTUpload = () => {
  pptFileList.value = []
  uploadedPPT.value = null
  pptDialogVisible.value = true
}

const handlePPTSubmit = async () => {
  if (pptFileList.value.length === 0) {
    ElMessage.warning('请选择PPT文件')
    return
  }
  try {
    pptSubmitting.value = true
    uploadedPPT.value = await uploadFileToServer(pptFileList, 'midterm_ppt')
    await studentApi.submitMidtermPPT(currentMidterm.value.id, {
      ppt_file_id: uploadedPPT.value.id,
      ppt_file_path: uploadedPPT.value.file_path,
      ppt_file_name: uploadedPPT.value.file_name
    })
    ElMessage.success('PPT已提交，等待最终评审')
    pptDialogVisible.value = false
    loadMidterm()
  } catch (e) { /* silent */ }
  finally { pptSubmitting.value = false }
}

const handleDownload = async (fileId, fileName) => {
  if (!fileId) return
  try {
    const response = await studentApi.downloadFile(fileId)
    const blob = response.data || response
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    if (fileName) link.download = fileName
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) { console.error('下载失败:', e) }
}

const openRectSubmit = (row) => {
  Object.assign(rectForm, {
    id: row.id,
    problem_description: row.problem_description,
    requirement: row.requirement,
    rectification_content: ''
  })
  rectFileList.value = []
  uploadedRectFile.value = null
  rectPPTList.value = []
  uploadedRectPPT.value = null
  rectDialogVisible.value = true
}

const handleRectFileChange = (file) => {
  const ext = (file.name || '').substring((file.name || '').lastIndexOf('.')).toLowerCase()
  if (!['.doc', '.docx', '.pdf', '.zip', '.rar'].includes(ext)) {
    ElMessage.error('仅支持 doc、docx、pdf、zip、rar 格式')
    rectFileList.value = []
    return
  }
  rectFileList.value = [file]
}

const handleRectFileRemove = () => {
  rectFileList.value = []
  uploadedRectFile.value = null
}

const handleRectPPTChange = (file) => {
  const ext = (file.name || '').substring((file.name || '').lastIndexOf('.')).toLowerCase()
  if (!['.ppt', '.pptx'].includes(ext)) {
    ElMessage.error('仅支持 ppt、pptx 格式')
    rectPPTList.value = []
    return
  }
  rectPPTList.value = [file]
}

const handleRectPPTRemove = () => {
  rectPPTList.value = []
  uploadedRectPPT.value = null
}

const handleRectSubmit = async () => {
  try {
    await rectFormRef.value.validate()
    rectSubmitting.value = true
    const payload = { rectification_content: rectForm.rectification_content }
    if (rectFileList.value.length > 0) {
      uploadedRectFile.value = await uploadFileToServer(rectFileList, 'midterm_rect')
      payload.rectification_file_path = uploadedRectFile.value.file_path
      payload.rectification_file_name = uploadedRectFile.value.file_name
    }
    if (rectPPTList.value.length > 0) {
      uploadedRectPPT.value = await uploadFileToServer(rectPPTList, 'midterm_rect_ppt')
      payload.rectification_ppt_path = uploadedRectPPT.value.file_path
      payload.rectification_ppt_name = uploadedRectPPT.value.file_name
    }
    await studentApi.submitRectification(rectForm.id, payload)
    ElMessage.success('整改材料已提交')
    rectDialogVisible.value = false
    loadRectifications(currentMidterm.value.id)
  } catch (e) { /* silent */ }
  finally { rectSubmitting.value = false }
}

const handleRectFileDownload = async (row) => {
  if (!row.rectification_file_path) return
  try {
    // 通过文件路径下载
    const response = await request.get('/files/download', { path: row.rectification_file_path }, { responseType: 'blob' })
    const blob = response.data || response
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.download = row.rectification_file_name || '整改材料'
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) { console.error('下载失败:', e) }
}

const handleRectPPTDownload = async (row) => {
  if (!row.rectification_ppt_path) return
  try {
    const response = await request.get('/files/download', { path: row.rectification_ppt_path }, { responseType: 'blob' })
    const blob = response.data || response
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.download = row.rectification_ppt_name || '整改PPT'
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) { console.error('下载失败:', e) }
}

onMounted(loadMidterm)
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.step-bar {
  margin-bottom: 20px;
}

.guidance-text {
  background: #ecf5ff;
  padding: 10px 14px;
  border-radius: 4px;
  color: #409eff;
  white-space: pre-wrap;
}

.midterm-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

.ppt-tip {
  margin-top: 16px;
}

.rectification-section {
  margin-top: 24px;
  h4 {
    margin: 0 0 12px;
    font-size: 15px;
    color: #303133;
    padding-left: 8px;
    border-left: 3px solid #e6a23c;
  }
}

:deep(.el-upload-dragger) {
  padding: 20px;
}
</style>
