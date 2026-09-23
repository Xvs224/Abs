<template>
  <div class="student-archives">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <span>成果归档</span>
          <el-button type="primary" :icon="Plus" @click="openCreate" v-if="!currentArchive">提交归档申请</el-button>
        </div>
      </template>

      <div v-if="currentArchive">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(currentArchive.status)">{{ statusText(currentArchive.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="归档编号" v-if="currentArchive.archive_no">{{ currentArchive.archive_no }}</el-descriptions-item>
          <el-descriptions-item label="答辩成绩" v-if="currentArchive.final_score">{{ currentArchive.final_score }} 分</el-descriptions-item>
          <el-descriptions-item label="成绩等级" v-if="currentArchive.final_grade">
            <el-tag type="success" size="small">{{ currentArchive.final_grade }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDate(currentArchive.create_time) }}</el-descriptions-item>
          <el-descriptions-item label="归档时间" v-if="currentArchive.archive_time">{{ formatDate(currentArchive.archive_time) }}</el-descriptions-item>
          <el-descriptions-item label="归档位置" :span="2" v-if="currentArchive.archive_location">{{ currentArchive.archive_location }}</el-descriptions-item>
          <el-descriptions-item label="审核意见" :span="2" v-if="currentArchive.return_reason">
            <span class="reject-text">{{ currentArchive.return_reason }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <div class="archive-materials" v-if="materials.length > 0">
          <h4>归档材料</h4>
          <el-table :data="materials" stripe size="small">
            <el-table-column prop="name" label="材料名称" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'uploaded' ? 'success' : 'info'" size="small">
                  {{ row.status === 'uploaded' ? '已上传' : '未上传' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <el-empty v-else description="您还未提交归档申请">
        <el-button type="primary" @click="openCreate">提交归档申请</el-button>
      </el-empty>
    </el-card>

    <el-dialog v-model="dialogVisible" title="提交归档申请" width="500px">
      <el-alert title="提交归档申请后，请等待指导教师审核。" type="info" :closable="false" style="margin-bottom: 16px;" />
      <el-form ref="formRef" :model="formData" label-width="100px">
        <el-form-item label="论文终稿">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="(file) => handleFileChange('thesis', file)"
            accept=".doc,.docx,.pdf"
          >
            <el-button type="primary" plain>选择文件</el-button>
          </el-upload>
          <span v-if="formData.thesis_file_name" class="file-name">{{ formData.thesis_file_name }}</span>
        </el-form-item>
        <el-form-item label="开题报告">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="(file) => handleFileChange('proposal', file)"
            accept=".doc,.docx,.pdf"
          >
            <el-button plain>选择文件</el-button>
          </el-upload>
          <span v-if="formData.proposal_file_name" class="file-name">{{ formData.proposal_file_name }}</span>
        </el-form-item>
        <el-form-item label="中期检查">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="(file) => handleFileChange('midterm', file)"
            accept=".doc,.docx,.pdf"
          >
            <el-button plain>选择文件</el-button>
          </el-upload>
          <span v-if="formData.midterm_file_name" class="file-name">{{ formData.midterm_file_name }}</span>
        </el-form-item>
        <el-form-item label="其他材料">
          <el-input type="textarea" v-model="formData.other_materials" :rows="2" placeholder="如有其他归档材料请说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import studentApi from '@/api/student'

const currentArchive = ref(null)
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const formData = reactive({
  thesis_file: null,
  thesis_file_name: '',
  proposal_file: null,
  proposal_file_name: '',
  midterm_file: null,
  midterm_file_name: '',
  other_materials: ''
})

const materials = computed(() => {
  if (!currentArchive.value) return []
  return [
    { name: '论文终稿', status: currentArchive.value.thesis_file ? 'uploaded' : 'missing' },
    { name: '开题报告', status: currentArchive.value.proposal_file ? 'uploaded' : 'missing' },
    { name: '中期检查报告', status: currentArchive.value.midterm_file ? 'uploaded' : 'missing' },
    { name: '评阅意见书', status: currentArchive.value.review_file ? 'uploaded' : 'missing' },
    { name: '答辩记录', status: currentArchive.value.defense_file ? 'uploaded' : 'missing' }
  ]
})

const statusText = (s) => ({ pending: '待审核', archived: '已归档', returned: '已退回' })[s] || s
const statusType = (s) => ({ pending: 'warning', archived: 'success', returned: 'danger' })[s] || 'info'
const formatDate = (dt) => dt ? new Date(dt).toLocaleDateString('zh-CN') : '-'

const myTopicId = ref(null)
const myLatestVersionId = ref(null)

const loadArchive = async () => {
  try {
    const [archiveRes, topicRes, thesisRes] = await Promise.all([
      studentApi.getMyArchives(),
      studentApi.getMyTopic(),
      studentApi.getMyThesisVersions()
    ])
    if (archiveRes?.items?.length > 0) {
      currentArchive.value = archiveRes.items[0]
    }
    if (topicRes?.items?.length > 0) {
      myTopicId.value = topicRes.items[0].id
    }
    if (thesisRes?.items?.length > 0) {
      myLatestVersionId.value = thesisRes.items[0].id
    }
  } catch (e) { /* silent */ }
}

const openCreate = () => {
  Object.assign(formData, {
    thesis_file: null, thesis_file_name: '',
    proposal_file: null, proposal_file_name: '',
    midterm_file: null, midterm_file_name: '',
    other_materials: ''
  })
  dialogVisible.value = true
}

const handleFileChange = (type, file) => {
  formData[`${type}_file`] = file.raw
  formData[`${type}_file_name`] = file.name
}

const handleSubmit = async () => {
  if (!myTopicId.value) {
    ElMessage.warning('请先完成选题后再提交归档')
    return
  }
  submitting.value = true
  try {
    const uploadResults = {}
    if (formData.thesis_file) {
      const res = await studentApi.uploadFile(formData.thesis_file, 'archive')
      uploadResults.thesis_file = res?.file_path || ''
    }
    if (formData.proposal_file) {
      const res = await studentApi.uploadFile(formData.proposal_file, 'archive')
      uploadResults.proposal_file = res?.file_path || ''
    }
    if (formData.midterm_file) {
      const res = await studentApi.uploadFile(formData.midterm_file, 'archive')
      uploadResults.midterm_file = res?.file_path || ''
    }
    if (formData.other_materials) {
      uploadResults.other_materials = formData.other_materials
    }

    const createData = {
      topic_id: myTopicId.value,
      final_version_id: myLatestVersionId.value
    }
    const createRes = await studentApi.createArchive(createData)

    const archiveId = createRes?.id || (currentArchive.value?.id)
    if (archiveId && Object.keys(uploadResults).length > 0) {
      await studentApi.updateArchive(archiveId, uploadResults)
    }

    ElMessage.success('归档申请已提交')
    dialogVisible.value = false
    loadArchive()
  } catch (e) { /* silent */ }
  finally { submitting.value = false }
}

onMounted(loadArchive)
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

.file-name { margin-left: 8px; color: #67c23a; font-size: 13px; }

.archive-materials {
  margin-top: 24px;

  h4 {
    margin: 0 0 12px;
    font-size: 15px;
    color: #303133;
    padding-left: 8px;
    border-left: 3px solid #409eff;
  }
}
</style>
