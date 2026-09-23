<template>
  <div class="student-thesis">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <span>{{ stageTitle }}</span>
          <el-button type="primary" :icon="Upload" @click="openUpload">
            {{ filteredVersions.length > 0 ? '重新上传' : '上传' }}
          </el-button>
        </div>
      </template>

      <div class="version-timeline" v-loading="loading">
        <el-timeline>
          <el-timeline-item
            v-for="item in filteredVersions"
            :key="item.id"
            :timestamp="formatDateTime(item.submit_time)"
            placement="top"
            :type="item.version_num === latestVersion ? 'primary' : 'info'"
            size="large"
          >
            <el-card shadow="hover" class="version-card">
              <div class="version-header">
                <div class="version-title">
                  <el-tag type="primary" size="small">v{{ item.version_num }}</el-tag>
                  <span v-if="item.version_num === latestVersion" class="latest-badge">最新版本</span>
                  <el-tag
                    :type="formatStatusType(item.format_check_status)"
                    size="small"
                    effect="plain"
                  >{{ formatStatusText(item.format_check_status) }}</el-tag>
                </div>
                <div class="version-meta">
                  <span>{{ item.file_name }}</span>
                  <span>{{ formatFileSize(item.file_size) }}</span>
                </div>
              </div>

              <div class="version-body" v-if="item.change_log">
                <span class="label">修改说明：</span>{{ item.change_log }}
              </div>

              <div class="version-stats">
                <span class="stat"><el-icon><Document /></el-icon> {{ item.word_count || 0 }} 字</span>
                <span class="stat"><el-icon><Files /></el-icon> {{ item.page_count || 0 }} 页</span>
                <span class="stat"><el-icon><Reading /></el-icon> {{ item.reference_count || 0 }} 参考文献</span>
                <span class="stat" v-if="item.format_score">格式得分: {{ item.format_score }}</span>
              </div>

              <div class="version-actions">
                <el-button text type="primary" @click="handleFormatCheck(item)" v-if="item.format_check_status === 'pending'">
                  格式检测
                </el-button>
                <el-button text type="primary" @click="viewFormatDetail(item)" v-if="item.format_check_status !== 'pending'">
                  查看检测报告
                </el-button>
                <el-button text type="warning" @click="openUpload">
                  修改
                </el-button>
                <el-button text type="danger" :icon="Delete" @click="handleDelete(item)">
                  删除
                </el-button>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-if="!loading && filteredVersions.length === 0" :description="`暂无${stageTitle}，请上传`">
          <el-button type="primary" @click="openUpload">上传{{ stageTitle }}</el-button>
        </el-empty>
      </div>
    </el-card>

    <el-dialog v-model="uploadVisible" :title="`上传${stageTitle}`" width="500px">
      <el-form ref="uploadFormRef" :model="uploadForm" label-width="100px">
        <el-form-item label="选择文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-exceed="() => ElMessage.warning('只能上传一个文件')"
            accept=".doc,.docx,.pdf"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 .doc / .docx / .pdf 格式</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="修改说明">
          <el-input type="textarea" v-model="uploadForm.change_log" :rows="3" placeholder="请描述本次修改内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="formatDialogVisible" title="格式检测报告" width="700px">
      <div v-if="formatDetail">
        <el-row :gutter="16" class="format-summary">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ formatDetail.total_score || 0 }}</div>
              <div class="summary-label">总得分</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ formatDetail.passed_count || 0 }}</div>
              <div class="summary-label">通过项</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value warn">{{ formatDetail.failed_count || 0 }}</div>
              <div class="summary-label">不通过项</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ formatDetail.total_items || 0 }}</div>
              <div class="summary-label">总检测项</div>
            </div>
          </el-col>
        </el-row>

        <el-table :data="formatCheckItems" stripe size="small" style="margin-top: 16px;">
          <el-table-column prop="name" label="检测项" />
          <el-table-column prop="status" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.passed ? 'success' : 'danger'" size="small">
                {{ row.passed ? '通过' : '不通过' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" show-overflow-tooltip />
        </el-table>

        <div v-if="formatDetail.problems_summary" class="problems-section">
          <h4>问题汇总</h4>
          <p>{{ formatDetail.problems_summary }}</p>
        </div>
        <div v-if="formatDetail.suggestions" class="suggestions-section">
          <h4>修改建议</h4>
          <p>{{ formatDetail.suggestions }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, UploadFilled, Delete } from '@element-plus/icons-vue'
import studentApi from '@/api/student'

const route = useRoute()
// 根据路由确定版本阶段: draft1=一稿, draft2=二稿, final=终审
const versionStage = computed(() => {
  if (route.path.includes('/draft2')) return 'draft2'
  if (route.path.includes('/final')) return 'final'
  return 'draft1'
})
const stageTitle = computed(() => ({
  draft1: '论文一稿',
  draft2: '论文二稿',
  final: '论文终审'
}[versionStage.value]))
// 当前阶段对应的版本号
const currentVersionNum = computed(() => ({
  draft1: 1,
  draft2: 2,
  final: 3
}[versionStage.value]))

const versions = ref([])
const loading = ref(false)
const uploadVisible = ref(false)
const uploading = ref(false)
const uploadRef = ref(null)
const selectedFile = ref(null)
const formatDialogVisible = ref(false)
const formatDetail = ref(null)
const myTopicId = ref(null)

const uploadForm = reactive({ change_log: '' })

const latestVersion = computed(() => {
  if (versions.value.length === 0) return 0
  return Math.max(...versions.value.map(v => v.version_num || 0))
})

// 按阶段筛选版本：一稿(v1)、二稿(v2)、终稿(v3)
const filteredVersions = computed(() => {
  if (versionStage.value === 'draft1') {
    return versions.value.filter(v => v.version_num === 1)
  } else if (versionStage.value === 'draft2') {
    return versions.value.filter(v => v.version_num === 2)
  }
  return versions.value.filter(v => v.version_num === 3)
})

const formatCheckItems = computed(() => {
  if (!formatDetail.value?.check_items) return []
  const items = formatDetail.value.check_items
  if (Array.isArray(items)) {
    return items.map(it => ({
      name: it.name,
      passed: it.passed !== false,
      detail: it.detail || it.message || (it.passed === false ? '不通过' : '通过')
    }))
  }
  if (typeof items === 'object') {
    return Object.entries(items).map(([name, val]) => ({
      name,
      passed: val.passed !== false,
      detail: val.detail || val.message || (val.passed === false ? '不通过' : '通过')
    }))
  }
  return []
})

const formatDateTime = (dt) => dt ? new Date(dt).toLocaleString('zh-CN') : '-'
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
const formatStatusText = (s) => ({ pending: '待检测', done: '已检测', failed: '检测失败', checking: '检测中' })[s] || s
const formatStatusType = (s) => ({ pending: 'info', done: 'success', failed: 'danger', checking: 'warning' })[s] || 'info'

const loadVersions = async () => {
  loading.value = true
  try {
    const [thesisRes, topicRes] = await Promise.all([
      studentApi.getMyThesisVersions(),
      studentApi.getMyTopic()
    ])
    versions.value = thesisRes?.items || []
    if (topicRes?.items?.length > 0) {
      myTopicId.value = topicRes.items[0].id
    }
  } catch (e) { /* silent */ }
  finally { loading.value = false }
}

const openUpload = () => {
  uploadForm.change_log = ''
  selectedFile.value = null
  uploadVisible.value = true
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  if (!myTopicId.value) {
    ElMessage.warning('请先完成选题后再上传论文')
    return
  }
  uploading.value = true
  try {
    await studentApi.uploadThesisVersion(selectedFile.value, {
      topic_id: myTopicId.value,
      version_name: `v${currentVersionNum.value}`,
      change_log: uploadForm.change_log,
      version_num: currentVersionNum.value,
      auto_check: true
    })
    ElMessage.success(filteredVersions.value.length > 0 ? `${stageTitle.value}已更新` : `${stageTitle.value}已上传`)
    uploadVisible.value = false
    loadVersions()
  } catch (e) { /* silent */ }
  finally { uploading.value = false }
}

const handleDelete = async (item) => {
  try {
    await ElMessageBox.confirm(`确定要删除${stageTitle.value}吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await studentApi.deleteThesisVersion(item.id)
    ElMessage.success('删除成功')
    loadVersions()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败:', e)
    }
  }
}

const handleFormatCheck = async (item) => {
  try {
    await studentApi.triggerFormatCheck(item.id)
    ElMessage.success('格式检测已触发')
    loadVersions()
  } catch (e) { /* silent */ }
}

const viewFormatDetail = async (item) => {
  try {
    const res = await studentApi.getFormatCheckResult(item.id)
    formatDetail.value = res
    formatDialogVisible.value = true
  } catch (e) { /* silent */ }
}

onMounted(loadVersions)
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.version-card {
  .version-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .version-title {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .latest-badge {
      background: #67c23a;
      color: #fff;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;
    }

    .version-meta {
      display: flex;
      gap: 12px;
      font-size: 13px;
      color: #909399;
    }
  }

  .version-body {
    margin-top: 8px;
    font-size: 13px;
    color: #606266;

    .label { color: #909399; }
  }

  .version-stats {
    margin-top: 12px;
    display: flex;
    gap: 20px;
    font-size: 13px;
    color: #606266;

    .stat {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  .version-actions {
    margin-top: 12px;
    display: flex;
    gap: 8px;
  }
}

.format-summary {
  text-align: center;

  .summary-item {
    padding: 16px;
    background: #f5f7fa;
    border-radius: 8px;
  }

  .summary-value {
    font-size: 28px;
    font-weight: 700;
    color: #409eff;

    &.warn { color: #f56c6c; }
  }

  .summary-label {
    font-size: 13px;
    color: #909399;
    margin-top: 4px;
  }
}

.problems-section, .suggestions-section {
  margin-top: 16px;

  h4 {
    margin: 0 0 8px;
    font-size: 14px;
    color: #303133;
  }

  p {
    margin: 0;
    font-size: 13px;
    color: #606266;
    line-height: 1.6;
  }
}

.problems-section { border-left: 3px solid #f56c6c; padding-left: 12px; }
.suggestions-section { border-left: 3px solid #67c23a; padding-left: 12px; }
</style>
