<template>
  <div class="system-logs-page">
    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" class="search-form">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="模块">
              <el-select v-model="searchForm.module" placeholder="全部模块" clearable style="width: 100%">
                <el-option label="用户管理" value="user" />
                <el-option label="选题管理" value="topic" />
                <el-option label="开题管理" value="proposal" />
                <el-option label="过程指导" value="guidance" />
                <el-option label="中期检查" value="midterm" />
                <el-option label="论文管理" value="thesis" />
                <el-option label="评阅答辩" value="review" />
                <el-option label="归档管理" value="archive" />
                <el-option label="系统管理" value="system" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="操作类型">
              <el-select v-model="searchForm.action_type" placeholder="全部类型" clearable style="width: 100%">
                <el-option label="新增" value="create" />
                <el-option label="修改" value="update" />
                <el-option label="删除" value="delete" />
                <el-option label="查询" value="query" />
                <el-option label="审核" value="review" />
                <el-option label="上传" value="upload" />
                <el-option label="下载" value="download" />
                <el-option label="登录" value="login" />
                <el-option label="登出" value="logout" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="操作用户">
              <el-input
                v-model="searchForm.username"
                placeholder="输入用户名搜索"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="操作时间">
              <el-date-picker
                v-model="searchForm.date_range"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24" class="search-actions">
            <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            <el-button :icon="Refresh" @click="handleReset">重置</el-button>
            <el-button :icon="Download" @click="handleExport">导出</el-button>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card class="table-card" shadow="never">
      <div class="table-toolbar">
        <span class="table-title">操作日志</span>
        <el-button :icon="RefreshRight" @click="loadList">刷新</el-button>
      </div>

      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="module" label="模块" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="moduleTagType(row.module)" size="small">
              {{ moduleLabel(row.module) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action_type" label="操作类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action_type)" size="small">
              {{ actionLabel(row.action_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action_desc" label="操作描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="username" label="操作用户" width="100" />
        <el-table-column prop="ip" label="IP地址" width="130" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="操作时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">详情</el-button>
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
      title="日志详情"
      width="650px"
    >
      <el-descriptions :column="2" border v-if="currentDetail">
        <el-descriptions-item label="模块">
          <el-tag :type="moduleTagType(currentDetail.module)" size="small">
            {{ moduleLabel(currentDetail.module) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="操作类型">
          <el-tag :type="actionTagType(currentDetail.action_type)" size="small">
            {{ actionLabel(currentDetail.action_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="操作用户">{{ currentDetail.username || '-' }}</el-descriptions-item>
        <el-descriptions-item label="操作状态">
          <el-tag :type="currentDetail.status === 'success' ? 'success' : 'danger'" size="small">
            {{ currentDetail.status === 'success' ? '成功' : '失败' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentDetail.ip || '-' }}</el-descriptions-item>
        <el-descriptions-item label="操作时间">{{ formatTime(currentDetail.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="操作描述" :span="2">
          {{ currentDetail.action_desc || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="请求方法">{{ currentDetail.method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="请求路径">{{ currentDetail.path || '-' }}</el-descriptions-item>
        <el-descriptions-item label="请求参数" :span="2">
          <div class="json-content">
            <pre>{{ formatJson(currentDetail.request_params) }}</pre>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="响应结果" :span="2" v-if="currentDetail.response">
          <div class="json-content">
            <pre>{{ formatJson(currentDetail.response) }}</pre>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2" v-if="currentDetail.error_message">
          <div class="error-content">{{ currentDetail.error_message }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="耗时">{{ currentDetail.duration ? currentDetail.duration + ' ms' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="浏览器/设备">{{ currentDetail.user_agent || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshRight, Download } from '@element-plus/icons-vue'
import request from '@/utils/request'
import dayjs from 'dayjs'

const loading = ref(false)
const detailVisible = ref(false)
const currentDetail = ref(null)

const tableData = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const searchForm = reactive({
  module: '',
  action_type: '',
  username: '',
  date_range: []
})

const moduleLabel = (module) => {
  const map = {
    user: '用户管理',
    topic: '选题管理',
    proposal: '开题管理',
    guidance: '过程指导',
    midterm: '中期检查',
    thesis: '论文管理',
    review: '评阅答辩',
    archive: '归档管理',
    system: '系统管理'
  }
  return map[module] || module
}

const moduleTagType = (module) => {
  const map = {
    user: 'primary',
    topic: 'success',
    proposal: 'warning',
    guidance: 'info',
    midterm: 'warning',
    thesis: 'primary',
    review: 'success',
    archive: 'info',
    system: 'danger'
  }
  return map[module] || 'info'
}

const actionLabel = (action) => {
  const map = {
    create: '新增',
    update: '修改',
    delete: '删除',
    query: '查询',
    review: '审核',
    upload: '上传',
    download: '下载',
    login: '登录',
    logout: '登出'
  }
  return map[action] || action
}

const actionTagType = (action) => {
  const map = {
    create: 'success',
    update: 'warning',
    delete: 'danger',
    query: 'info',
    review: 'primary',
    upload: 'success',
    download: 'info',
    login: 'success',
    logout: 'info'
  }
  return map[action] || 'info'
}

const formatTime = (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'

const formatJson = (data) => {
  if (!data) return '-'
  try {
    if (typeof data === 'string') {
      return JSON.stringify(JSON.parse(data), null, 2)
    }
    return JSON.stringify(data, null, 2)
  } catch {
    return data
  }
}

const loadList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      module: searchForm.module || undefined,
      action_type: searchForm.action_type || undefined,
      username: searchForm.username || undefined
    }
    if (searchForm.date_range && searchForm.date_range.length === 2) {
      params.start_time = dayjs(searchForm.date_range[0]).format('YYYY-MM-DD HH:mm:ss')
      params.end_time = dayjs(searchForm.date_range[1]).format('YYYY-MM-DD HH:mm:ss')
    }
    const res = await request.get('/logs', params)
    tableData.value = res.items || res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载日志列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadList()
}

const handleReset = () => {
  searchForm.module = ''
  searchForm.action_type = ''
  searchForm.username = ''
  searchForm.date_range = []
  pagination.page = 1
  loadList()
}

const handleViewDetail = async (row) => {
  detailVisible.value = true
  currentDetail.value = null
  try {
    const res = await request.get(`/logs/${row.id}`)
    currentDetail.value = res
  } catch (error) {
    console.error('获取详情失败:', error)
  }
}

const handleExport = () => {
  ElMessage.info('导出功能开发中')
}

onMounted(() => {
  loadList()
})
</script>

<style scoped lang="scss">
.system-logs-page {
  .search-card {
    margin-bottom: 16px;

    .search-actions {
      text-align: right;
    }
  }

  .table-card {
    .table-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      .table-title {
        font-size: 15px;
        font-weight: 600;
        color: #303133;
      }
    }

    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: 20px;
    }
  }

  .json-content {
    background: #f5f7fa;
    padding: 12px;
    border-radius: 4px;
    max-height: 200px;
    overflow-y: auto;

    pre {
      margin: 0;
      font-size: 12px;
      line-height: 1.5;
      color: #606266;
      white-space: pre-wrap;
      word-break: break-all;
    }
  }

  .error-content {
    background: #fef0f0;
    color: #f56c6c;
    padding: 12px;
    border-radius: 4px;
    white-space: pre-wrap;
    word-break: break-all;
  }
}
</style>
