<template>
  <div class="thesis-page">
    <!-- 操作栏 -->
    <el-card class="header-card" shadow="never">
      <div class="page-header">
        <div class="header-info">
          <h2 class="page-title">论文版本管理</h2>
          <p class="page-desc">管理论文的各个版本，支持上传、格式检测和版本对比</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" :icon="Upload" @click="handleUpload">
            上传新版本
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
            <el-input
              v-model="searchKeyword"
              placeholder="搜索版本备注"
              clearable
              size="default"
              style="width: 200px"
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
          v-for="(item, index) in versionList"
          :key="item.id"
          :timestamp="formatTime(item.created_at)"
          placement="top"
          :type="index === 0 ? 'primary' : 'info'"
          :size="index === 0 ? 'large' : 'normal'"
        >
          <div class="version-item">
            <div class="version-header">
              <div class="version-info">
                <span class="version-tag" :class="{ latest: index === 0 }">
                  V{{ item.version_no }}
                  <el-tag v-if="index === 0" type="success" size="small" effect="dark" class="latest-tag">
                    最新版本
                  </el-tag>
                </span>
                <span class="version-title">{{ item.title || '未命名版本' }}</span>
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
                {{ item.uploader_name || '未知' }}
              </span>
            </div>

            <div class="version-desc" v-if="item.remark">
              {{ item.remark }}
            </div>

            <!-- 格式检测结果 -->
            <div class="format-result" v-if="item.format_check_status === 'completed' && item.format_result">
              <el-divider content-position="left">
                <span class="divider-title">格式检测结果</span>
              </el-divider>
              <div class="format-stats">
                <div class="stat-item">
                  <span class="stat-label">总问题数</span>
                  <span class="stat-value total">{{ item.format_result.total || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">严重错误</span>
                  <span class="stat-value error">{{ item.format_result.error || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">警告</span>
                  <span class="stat-value warning">{{ item.format_result.warning || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">建议</span>
                  <span class="stat-value info">{{ item.format_result.info || 0 }}</span>
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

      <el-empty v-if="!loading && versionList.length === 0" description="暂无版本记录" />

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
      title="上传新版本"
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
        <el-form-item label="版本备注" prop="remark">
          <el-input
            v-model="uploadForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入版本更新说明（选填）"
          />
        </el-form-item>
        <el-form-item label="自动检测">
          <el-switch v-model="uploadForm.auto_check" active-text="上传后自动检测格式" />
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
            <el-tag type="info">V{{ compareVersions[1]?.version_no }}</el-tag>
            <span class="version-time">{{ formatTime(compareVersions[1]?.created_at) }}</span>
          </div>
          <el-icon class="compare-icon"><Switch /></el-icon>
          <div class="compare-version right">
            <el-tag type="primary">V{{ compareVersions[0]?.version_no }}</el-tag>
            <span class="version-time">{{ formatTime(compareVersions[0]?.created_at) }}</span>
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
      <el-table :data="formatIssues" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="issueTypeTag(row.level)" size="small">
              {{ issueLevelLabel(row.level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" width="120" />
        <el-table-column prop="description" label="问题描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="suggestion" label="修改建议" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload, RefreshRight, Search, Document, Files, User, View, Download,
  MagicStick, ScaleToOriginal, Delete, UploadFilled, Switch
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import dayjs from 'dayjs'

const loading = ref(false)
const uploadVisible = ref(false)
const uploadLoading = ref(false)
const compareVisible = ref(false)
const formatDetailVisible = ref(false)
const uploadFormRef = ref(null)
const uploadRef = ref(null)
const searchKeyword = ref('')

const versionList = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const fileList = ref([])
const uploadForm = reactive({
  remark: '',
  auto_check: true
})

const uploadRules = {
  remark: []
}

const compareVersions = ref([])
const formatIssues = ref([])

const formatCheckLabel = (status) => {
  const map = {
    pending: '待检测',
    checking: '检测中',
    completed: '检测完成',
    failed: '检测失败'
  }
  return map[status] || '未知'
}

const formatCheckTagType = (status) => {
  const map = {
    pending: 'info',
    checking: 'warning',
    completed: 'success',
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

const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/thesis/versions', {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchKeyword.value || undefined
    })
    versionList.value = res.items || res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载版本列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleUpload = () => {
  uploadForm.remark = ''
  uploadForm.auto_check = true
  fileList.value = []
  uploadVisible.value = true
}

const handleFileChange = (file, fileList) => {
  fileList.value = fileList
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
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
    formData.append('remark', uploadForm.remark)
    formData.append('auto_check', uploadForm.auto_check)
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

const handlePreview = (item) => {
  ElMessage.info(`预览版本 V${item.version_no}`)
}

const handleDownload = (item) => {
  ElMessage.info(`下载版本 V${item.version_no}`)
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

const viewFormatDetail = (item) => {
  // 模拟数据
  formatIssues.value = [
    { level: 'error', location: '第3页 第2段', description: '字体大小不符合要求', suggestion: '将字体大小调整为小四（12pt）' },
    { level: 'warning', location: '第5页 图3-1', description: '图片未编号或编号格式错误', suggestion: '按照章节编号格式重命名图片' },
    { level: 'info', location: '第10页 参考文献', description: '参考文献格式建议优化', suggestion: '按照GB/T 7714标准调整格式' },
    ...(item.format_result?.details || [])
  ]
  formatDetailVisible.value = true
}

const handleCompare = (item) => {
  // 将当前版本和选中版本进行对比
  compareVersions.value = [versionList.value[0], item]
  compareVisible.value = true
}

const handleDelete = (item) => {
  ElMessageBox.confirm(`确定要删除版本 V${item.version_no} 吗？`, '删除确认', {
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
}
</style>
