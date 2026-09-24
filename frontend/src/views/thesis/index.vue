<template>
  <div class="thesis-page">
    <StageBanner :module-key="thesisModuleKey" />
    <!-- 操作栏 -->
    <el-card class="header-card" shadow="never">
      <div class="page-header">
        <div class="header-info">
          <h2 class="page-title">论文版本管理</h2>
          <p class="page-desc">管理论文的各个版本，支持上传、格式检测和版本对比</p>
        </div>
        <div class="header-actions">
          <el-button v-if="isStudent" type="primary" :icon="Upload" @click="handleUpload">
            {{ filteredVersionList.length > 0 ? '重新上传' : '上传' }}
          </el-button>
          <el-button :icon="RefreshRight" @click="loadList">刷新</el-button>
        </div>
      </div>
    </el-card>

    <!-- 版本列表 -->
    <el-card class="version-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>版本历史</span>
          <div class="header-right">
            <el-select
              v-if="isTeacher"
              v-model="filterStudentId"
              placeholder="全部学生"
              clearable
              filterable
              size="default"
              style="width: 180px; margin-right: 8px"
              :loading="studentLoading"
              @change="loadList"
            >
              <el-option
                v-for="s in studentOptions"
                :key="s.id"
                :label="s.real_name"
                :value="s.id"
              />
            </el-select>
            <el-input
              v-model="searchKeyword"
              placeholder="搜索论文题目/学生/变更日志"
              clearable
              size="default"
              style="width: 220px"
              @keyup.enter="loadList"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </template>

      <el-timeline v-loading="loading">
        <el-timeline-item
          v-for="(item, index) in filteredVersionList"
          :key="item.id"
          :timestamp="formatTime(item.submit_time)"
          placement="top"
          :type="index === 0 ? 'primary' : 'info'"
          :size="index === 0 ? 'large' : 'normal'"
        >
          <div class="version-item">
            <div class="version-header">
              <div class="version-info">
                <span class="version-tag" :class="{ latest: index === 0 }">
                  V{{ item.version_num }}
                  <el-tag v-if="index === 0" type="success" size="small" effect="dark" class="latest-tag">
                    最新版本
                  </el-tag>
                </span>
                <span class="version-title">{{ item.version_name || '未命名版本' }}</span>
              </div>
              <div class="version-status">
                <el-tag :type="formatCheckTagType(item.format_check_status)" size="small">
                  {{ formatCheckLabel(item.format_check_status) }}
                </el-tag>
              </div>
            </div>

            <div class="version-meta">
              <span class="meta-item">
                <el-icon><Document /></el-icon>
                {{ item.file_name || '未命名.pdf' }}
              </span>
              <span class="meta-item" v-if="item.file_size">
                <el-icon><Files /></el-icon>
                {{ formatFileSize(item.file_size) }}
              </span>
              <span class="meta-item">
                <el-icon><User /></el-icon>
                {{ item.student_name || '未知' }}
              </span>
            </div>

            <div class="version-desc" v-if="item.change_log">
              {{ item.change_log }}
            </div>

            <!-- 格式检测结果 -->
            <div class="format-result" v-if="item.format_check_status === 'done' && formatResults[item.id]">
              <el-divider content-position="left">
                <span class="divider-title">格式检测结果</span>
              </el-divider>
              <div class="format-stats">
                <div class="stat-item">
                  <span class="stat-label">总得分</span>
                  <span class="stat-value total">{{ formatResults[item.id].total_score || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">通过项</span>
                  <span class="stat-value success">{{ formatResults[item.id].passed_count || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">不通过项</span>
                  <span class="stat-value error">{{ formatResults[item.id].failed_count || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">总检测项</span>
                  <span class="stat-value info">{{ formatResults[item.id].total_items || 0 }}</span>
                </div>
              </div>
              <el-button type="primary" link size="small" @click="viewFormatDetail(item)">
                查看详细报告
              </el-button>
            </div>

            <div class="version-actions">
              <el-button type="primary" link size="small" :icon="View" @click="handlePreview(item)">
                预览
              </el-button>
              <el-button type="success" link size="small" :icon="Download" @click="handleDownload(item)">
                下载
              </el-button>
              <el-button
                v-if="item.format_check_status === 'pending'"
                type="warning"
                link
                size="small"
                :icon="MagicStick"
                @click="handleFormatCheck(item)"
              >
                格式检测
              </el-button>
              <el-button
                v-if="index > 0"
                type="info"
                link
                size="small"
                :icon="ScaleToOriginal"
                @click="handleCompare(item)"
              >
                版本对比
              </el-button>
              <el-button type="danger" link size="small" :icon="Delete" @click="handleDelete(item)">
                删除
              </el-button>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>

      <el-empty v-if="!loading && filteredVersionList.length === 0" description="暂无版本记录" />

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[5, 10, 20]"
          :total="pagination.total"
          layout="total, prev, pager, next"
          background
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadVisible"
      :title="`上传${versionStage === 'draft1' ? '一稿' : versionStage === 'draft2' ? '二稿' : '终审'}`"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-width="80px">
        <el-form-item label="文件">
          <el-upload
            ref="uploadRef"
            class="upload-demo"
            drag
            action="#"
            :auto-upload="false"
            :limit="1"
            :file-list="fileList"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            accept=".pdf,.doc,.docx"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、DOC、DOCX 格式，单个文件不超过 50MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="变更日志" prop="change_log">
          <el-input
            v-model="uploadForm.change_log"
            type="textarea"
            :rows="3"
            placeholder="请输入版本更新说明（选填）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploadLoading" @click="submitUpload">
          确认上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 版本对比对话框 -->
    <el-dialog
      v-model="compareVisible"
      title="版本对比"
      width="900px"
    >
      <div class="compare-container">
        <div class="compare-header">
          <div class="compare-version left">
            <el-tag type="info">V{{ compareVersions[1]?.version_num }}</el-tag>
            <span class="version-time">{{ formatTime(compareVersions[1]?.submit_time) }}</span>
          </div>
          <el-icon class="compare-icon"><Switch /></el-icon>
          <div class="compare-version right">
            <el-tag type="primary">V{{ compareVersions[0]?.version_num }}</el-tag>
            <span class="version-time">{{ formatTime(compareVersions[0]?.submit_time) }}</span>
          </div>
        </div>
        <div class="compare-content">
          <el-alert title="版本对比功能" type="info" :closable="false">
            <p>对比两个版本之间的差异，包括内容变更、格式调整等。</p>
            <p class="compare-tip">完整的版本对比功能需要后端支持，此处为入口展示。</p>
          </el-alert>
        </div>
      </div>
    </el-dialog>

    <!-- 格式检测详情对话框 -->
    <el-dialog
      v-model="formatDetailVisible"
      title="格式检测详情"
      width="700px"
    >
      <div v-if="formatSummary" class="format-summary-bar">
        <span>总得分：<b>{{ formatSummary.total_score }}</b> / {{ formatSummary.max_score }}</span>
        <span>通过项：<b class="text-success">{{ formatSummary.passed_count }}</b></span>
        <span>不通过项：<b class="text-danger">{{ formatSummary.failed_count }}</b></span>
      </div>
      <el-table :data="formatIssues" border stripe v-loading="formatDetailLoading" style="margin-top: 12px;">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="检测项" min-width="120" />
        <el-table-column label="结果" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.passed ? 'success' : 'danger'" size="small">
              {{ row.passed ? '通过' : '不通过' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="详情" min-width="220" show-overflow-tooltip />
        <el-table-column label="得分" width="100" align="center">
          <template #default="{ row }">
            {{ row.score }} / {{ row.max_score }}
          </template>
        </el-table-column>
      </el-table>
      <div v-if="formatSummary?.problems_summary" class="problems-section">
        <h4>问题汇总</h4>
        <p>{{ formatSummary.problems_summary }}</p>
      </div>
      <div v-if="formatSummary?.suggestions" class="suggestions-section">
        <h4>修改建议</h4>
        <p>{{ formatSummary.suggestions }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import StageBanner from '@/views/common/StageBanner.vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload, RefreshRight, Search, Document, Files, User, View, Download,
  MagicStick, ScaleToOriginal, Delete, UploadFilled, Switch
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import dayjs from 'dayjs'
import { useUserStore } from '@/store/user'

const route = useRoute()
const userStore = useUserStore()
const isTeacher = computed(() => userStore.userInfo?.role === 'teacher')
const isStudent = computed(() => userStore.userInfo?.role === 'student')
// 根据路由确定版本阶段: draft1=一稿, draft2=二稿, final=终审
const versionStage = computed(() => {
  if (route.path.includes('/draft2')) return 'draft2'
  if (route.path.includes('/final')) return 'final'
  return 'draft1'
})
// 阶段时间配置的 module_key 映射
const thesisModuleKey = computed(() => ({
  draft1: 'thesis_draft',
  draft2: 'thesis_revision',
  final: 'thesis_final',
}[versionStage.value]))
// 当前阶段对应的版本号
const currentVersionNum = computed(() => ({
  draft1: 1,
  draft2: 2,
  final: 3
}[versionStage.value]))

const loading = ref(false)
const uploadVisible = ref(false)
const uploadLoading = ref(false)
const compareVisible = ref(false)
const formatDetailVisible = ref(false)
const formatDetailLoading = ref(false)
const uploadFormRef = ref(null)
const uploadRef = ref(null)
const searchKeyword = ref('')
const filterStudentId = ref(null)

// 学生列表（教师端筛选查看）
const studentOptions = ref([])
const studentLoading = ref(false)

const versionList = ref([])
// 按阶段筛选版本：一稿(v1)、二稿(v2)、终审(v3及以上)
const filteredVersionList = computed(() => {
  if (versionStage.value === 'draft1') {
    return versionList.value.filter(v => v.version_num === 1)
  } else if (versionStage.value === 'draft2') {
    return versionList.value.filter(v => v.version_num === 2)
  } else {
    return versionList.value.filter(v => v.version_num === 3)
  }
})
const formatResults = reactive({})
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const fileList = ref([])
const uploadForm = reactive({
  change_log: ''
})

const uploadRules = {
  change_log: []
}

const compareVersions = ref([])
const formatIssues = ref([])
const formatSummary = ref(null)

const formatCheckLabel = (status) => {
  const map = {
    pending: '待检测',
    done: '检测完成',
    failed: '检测失败'
  }
  return map[status] || '未知'
}

const formatCheckTagType = (status) => {
  const map = {
    pending: 'info',
    done: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const issueLevelLabel = (level) => {
  const map = { error: '错误', warning: '警告', info: '建议' }
  return map[level] || level
}

const issueTypeTag = (level) => {
  const map = { error: 'danger', warning: 'warning', info: 'info' }
  return map[level] || 'info'
}

const formatTime = (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const fetchFormatResult = async (item) => {
  if (formatResults[item.id]) return
  try {
    const res = await request.get(`/thesis/versions/${item.id}/format-check`)
    formatResults[item.id] = res
  } catch (error) {
    console.error('获取格式检测结果失败:', error)
  }
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/thesis/versions', {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchKeyword.value || undefined,
      student_id: filterStudentId.value || undefined
    })
    versionList.value = res.items || res.data || []
    pagination.total = res.total || 0
    versionList.value.forEach(item => {
      if (item.format_check_status === 'done') {
        fetchFormatResult(item)
      }
    })
  } catch (error) {
    console.error('加载版本列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleUpload = () => {
  uploadForm.change_log = ''
  fileList.value = []
  uploadVisible.value = true
}

const handleFileChange = (file, fileList) => {
  fileList.value = fileList
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const loadStudents = async () => {
  studentLoading.value = true
  try {
    const res = await request.get('/users', { page: 1, page_size: 100, role: 'student' })
    studentOptions.value = res.items || res.data || []
  } catch (error) {
    console.error('加载学生列表失败:', error)
  } finally {
    studentLoading.value = false
  }
}

const submitUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  try {
    uploadLoading.value = true
    const formData = new FormData()
    formData.append('file', fileList.value[0].raw)
    formData.append('change_log', uploadForm.change_log)
    formData.append('version_num', currentVersionNum.value)
    await request.post('/thesis/versions', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('上传成功')
    uploadVisible.value = false
    loadList()
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    uploadLoading.value = false
  }
}

const handlePreview = async (item) => {
  try {
    const ext = (item.file_name || '').split('.').pop().toLowerCase()
    // 仅 PDF 可在浏览器内预览，doc/docx 提示下载
    if (ext !== 'pdf') {
      ElMessage.info(`${ext.toUpperCase()} 格式暂不支持在线预览，请下载后查看`)
      return
    }
    const res = await request.download(`/thesis/versions/${item.id}/download`)
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error('预览失败，请稍后重试')
  }
}

const handleDownload = async (item) => {
  try {
    const res = await request.download(`/thesis/versions/${item.id}/download`)
    const blob = new Blob([res.data])
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = item.file_name || `thesis_v${item.version_num}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('下载已开始')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败，请稍后重试')
  }
}

const handleFormatCheck = async (item) => {
  try {
    ElMessage.info('开始格式检测，请稍候...')
    await request.post(`/thesis/versions/${item.id}/format-check`)
    ElMessage.success('格式检测已启动')
    loadList()
  } catch (error) {
    console.error('启动检测失败:', error)
  }
}

const viewFormatDetail = async (item) => {
  formatDetailVisible.value = true
  formatDetailLoading.value = true
  formatIssues.value = []
  formatSummary.value = null
  try {
    const res = await request.get(`/thesis/versions/${item.id}/format-check`)
    formatIssues.value = Array.isArray(res?.check_items) ? res.check_items : []
    formatSummary.value = res
  } catch (error) {
    console.error('获取格式检测详情失败:', error)
  } finally {
    formatDetailLoading.value = false
  }
}

const handleCompare = (item) => {
  compareVersions.value = [versionList.value[0], item]
  compareVisible.value = true
}

const handleDelete = (item) => {
  ElMessageBox.confirm(`确定要删除版本 V${item.version_num} 吗？`, '删除确认', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await request.delete(`/thesis/versions/${item.id}`)
      ElMessage.success('删除成功')
      loadList()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }).catch(() => {})
}

onMounted(() => {
  if (isTeacher.value) {
    loadStudents()
  }
  loadList()
})
</script>

<style scoped lang="scss">
.thesis-page {
  .header-card {
    margin-bottom: 16px;

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-info {
        .page-title {
          font-size: 20px;
          font-weight: 600;
          color: #303133;
          margin: 0 0 4px 0;
        }

        .page-desc {
          font-size: 13px;
          color: #909399;
          margin: 0;
        }
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .version-item {
    padding: 8px 0;

    .version-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;

      .version-info {
        display: flex;
        align-items: center;
        gap: 10px;

        .version-tag {
          font-size: 15px;
          font-weight: 600;
          color: #909399;
          display: flex;
          align-items: center;
          gap: 8px;

          &.latest {
            color: #409eff;
          }

          .latest-tag {
            font-size: 11px;
          }
        }

        .version-title {
          font-size: 15px;
          color: #303133;
        }
      }
    }

    .version-meta {
      display: flex;
      gap: 20px;
      margin-bottom: 8px;

      .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #909399;

        .el-icon {
          font-size: 13px;
        }
      }
    }

    .version-desc {
      font-size: 13px;
      color: #606266;
      margin-bottom: 10px;
      padding: 8px 12px;
      background: #f5f7fa;
      border-radius: 4px;
    }

    .format-result {
      margin: 12px 0;

      .divider-title {
        font-size: 13px;
        color: #606266;
      }

      .format-stats {
        display: flex;
        gap: 30px;
        margin-bottom: 8px;

        .stat-item {
          display: flex;
          flex-direction: column;
          align-items: center;

          .stat-label {
            font-size: 12px;
            color: #909399;
            margin-bottom: 4px;
          }

          .stat-value {
            font-size: 20px;
            font-weight: 600;

            &.total { color: #303133; }
            &.success { color: #67c23a; }
            &.error { color: #f56c6c; }
            &.warning { color: #e6a23c; }
            &.info { color: #909399; }
          }
        }
      }
    }

    .version-actions {
      display: flex;
      gap: 4px;
      margin-top: 8px;
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }

  .upload-demo {
    width: 100%;

    :deep(.el-upload-dragger) {
      width: 100%;
    }
  }

  .compare-container {
    .compare-header {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 20px;
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid #ebeef5;

      .compare-version {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;

        .version-time {
          font-size: 12px;
          color: #909399;
        }

        &.left { text-align: right; }
        &.right { text-align: left; }
      }

      .compare-icon {
        font-size: 24px;
        color: #409eff;
      }
    }

    .compare-content {
      .compare-tip {
        margin-top: 8px;
        font-size: 12px;
        color: #909399;
      }
    }
  }

  .format-summary-bar {
    display: flex;
    gap: 24px;
    padding: 12px 16px;
    background: #f5f7fa;
    border-radius: 6px;
    font-size: 14px;
    color: #606266;

    b { font-size: 18px; color: #409eff; }
    .text-success { color: #67c23a; }
    .text-danger { color: #f56c6c; }
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
      white-space: pre-line;
    }
  }

  .problems-section { border-left: 3px solid #f56c6c; padding-left: 12px; }
  .suggestions-section { border-left: 3px solid #67c23a; padding-left: 12px; }
}
</style>
