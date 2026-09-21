<template>
  <div class="anomaly-page">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="5">
        <div class="stat-card card-total">
          <div class="stat-icon">
            <el-icon size="24"><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total || 0 }}</div>
            <div class="stat-label">异常总数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card card-l1">
          <div class="stat-content">
            <div class="stat-value">{{ stats.L1 || 0 }}</div>
            <div class="stat-label">L1 提示</div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card card-l2">
          <div class="stat-content">
            <div class="stat-value">{{ stats.L2 || 0 }}</div>
            <div class="stat-label">L2 警告</div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card card-l3">
          <div class="stat-content">
            <div class="stat-value">{{ stats.L3 || 0 }}</div>
            <div class="stat-label">L3 告警</div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card card-pending">
          <div class="stat-content">
            <div class="stat-value">{{ stats.pending || 0 }}</div>
            <div class="stat-label">待处理</div>
          </div>
        </div>
      </el-col>
      <el-col :span="3">
        <div class="action-card">
          <el-button type="primary" :icon="VideoPlay" @click="handleDetect">
            触发检测
          </el-button>
          <el-button :icon="DataAnalysis" @click="handleEvaluate">
            准确性评估
          </el-button>
        </div>
      </el-col>
    </el-row>

    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="等级">
          <el-select v-model="searchForm.severity_level" placeholder="全部等级" clearable style="width: 120px">
            <el-option label="L1 提示" value="L1" />
            <el-option label="L2 警告" value="L2" />
            <el-option label="L3 告警" value="L3" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.review_status" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="待复核" value="pending" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已忽略" value="ignored" />
            <el-option label="已处理" value="resolved" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.type" placeholder="全部类型" clearable style="width: 140px">
            <el-option label="进度异常" value="progress" />
            <el-option label="内容重复" value="duplicate" />
            <el-option label="格式错误" value="format" />
            <el-option label="提交异常" value="submission" />
            <el-option label="指导缺失" value="guidance" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索特征/描述"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card class="table-card" shadow="never">
      <div class="table-toolbar">
        <span class="table-title">异常记录列表</span>
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
        <el-table-column prop="feature_name" label="异常特征" min-width="160" show-overflow-tooltip />
        <el-table-column prop="severity_level" label="等级" width="90" align="center">
          <template #default="{ row }">
            <span :class="`level-tag level-${row.severity_level}`">{{ row.severity_level }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="typeTagType(row.type)" size="small">
              {{ typeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="related_student" label="关联学生" width="100" />
        <el-table-column prop="description" label="异常描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="review_status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.review_status)" size="small">
              {{ statusLabel(row.review_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detection_time" label="检测时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.detection_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">详情</el-button>
            <el-button
              v-if="row.review_status === 'pending'"
              type="success"
              link
              size="small"
              @click="handleReview(row)"
            >
              复核
            </el-button>
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
      title="异常详情"
      width="650px"
    >
      <div v-loading="detailLoading" class="anomaly-detail">
        <template v-if="currentDetail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="异常特征" :span="2">
              <span class="feature-name">{{ currentDetail.feature_name }}</span>
              <span :class="`level-tag level-${currentDetail.severity_level}`" style="margin-left: 10px">
                {{ currentDetail.severity_level }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="异常类型">{{ typeLabel(currentDetail.type) }}</el-descriptions-item>
            <el-descriptions-item label="复核状态">
              <el-tag :type="statusTagType(currentDetail.review_status)" size="small">
                {{ statusLabel(currentDetail.review_status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="关联学生">{{ currentDetail.related_student || '-' }}</el-descriptions-item>
            <el-descriptions-item label="关联教师">{{ currentDetail.related_teacher || '-' }}</el-descriptions-item>
            <el-descriptions-item label="检测时间" :span="2">{{ formatTime(currentDetail.detection_time) }}</el-descriptions-item>
            <el-descriptions-item label="异常描述" :span="2">
              <div class="desc-text">{{ currentDetail.description || '-' }}</div>
            </el-descriptions-item>
            <el-descriptions-item label="异常详情" :span="2">
              <div class="detail-text">{{ currentDetail.detail || '-' }}</div>
            </el-descriptions-item>
            <el-descriptions-item label="置信度" v-if="currentDetail.confidence !== undefined">
              <el-progress :percentage="Math.round(currentDetail.confidence * 100)" :stroke-width="12" />
            </el-descriptions-item>
            <el-descriptions-item label="数据来源">{{ currentDetail.data_source || '-' }}</el-descriptions-item>
          </el-descriptions>

          <!-- 复核历史 -->
          <div class="review-history" v-if="reviewHistory.length">
            <div class="section-title">复核历史</div>
            <el-timeline>
              <el-timeline-item
                v-for="(item, index) in reviewHistory"
                :key="index"
                :timestamp="formatTime(item.reviewed_at)"
                placement="top"
                :type="item.review_result === 'confirmed' ? 'success' : item.review_result === 'ignored' ? 'info' : 'warning'"
              >
                <div class="review-item">
                  <div class="reviewer">
                    <strong>{{ item.reviewer_name || '系统' }}</strong>
                    <el-tag size="small" :type="item.review_result === 'confirmed' ? 'success' : item.review_result === 'ignored' ? 'info' : 'warning'">
                      {{ reviewResultLabel(item.review_result) }}
                    </el-tag>
                  </div>
                  <div class="review-comment" v-if="item.comment">{{ item.comment }}</div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
        </template>
      </div>
    </el-dialog>

    <!-- 人工复核对话框 -->
    <el-dialog
      v-model="reviewVisible"
      title="人工复核"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="reviewForm" label-width="80px">
        <el-form-item label="复核结果">
          <el-radio-group v-model="reviewForm.review_result">
            <el-radio value="confirmed">确认异常</el-radio>
            <el-radio value="ignored">忽略误报</el-radio>
            <el-radio value="resolved">已处理</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="复核意见">
          <el-input
            v-model="reviewForm.comment"
            type="textarea"
            :rows="4"
            placeholder="请输入复核意见（选填）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewLoading" @click="submitReview">
          提交复核
        </el-button>
      </template>
    </el-dialog>

    <!-- 准确性评估对话框 -->
    <el-dialog
      v-model="evaluateVisible"
      title="准确性评估"
      width="550px"
    >
      <div v-loading="evaluateLoading" class="evaluate-content">
        <template v-if="evaluateResult">
          <el-row :gutter="20" class="evaluate-stats">
            <el-col :span="8">
              <div class="eval-stat">
                <div class="eval-value">{{ evaluateResult.precision || 0 }}%</div>
                <div class="eval-label">精确率</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="eval-stat">
                <div class="eval-value">{{ evaluateResult.recall || 0 }}%</div>
                <div class="eval-label">召回率</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="eval-stat">
                <div class="eval-value">{{ evaluateResult.f1_score || 0 }}%</div>
                <div class="eval-label">F1 分数</div>
              </div>
            </el-col>
          </el-row>
          <el-descriptions :column="1" border class="mt-20">
            <el-descriptions-item label="已复核总数">{{ evaluateResult.reviewed_total || 0 }}</el-descriptions-item>
            <el-descriptions-item label="确认异常数">{{ evaluateResult.true_positive || 0 }}</el-descriptions-item>
            <el-descriptions-item label="误报数">{{ evaluateResult.false_positive || 0 }}</el-descriptions-item>
            <el-descriptions-item label="漏报数">{{ evaluateResult.false_negative || 0 }}</el-descriptions-item>
          </el-descriptions>
          <div class="eval-note">
            <el-icon><InfoFilled /></el-icon>
            评估数据基于已人工复核的记录计算
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Warning, VideoPlay, DataAnalysis, Search, Refresh, RefreshRight, InfoFilled
} from '@element-plus/icons-vue'
import {
  getAnomalyList, getAnomalyDetail, getAnomalyStats, getAnomalyReviews,
  reviewAnomaly, detectAnomaly, evaluateAnomaly
} from '@/api/anomaly'
import dayjs from 'dayjs'

const loading = ref(false)
const detailLoading = ref(false)
const reviewLoading = ref(false)
const evaluateLoading = ref(false)
const detailVisible = ref(false)
const reviewVisible = ref(false)
const evaluateVisible = ref(false)
const currentDetail = ref(null)
const reviewHistory = ref([])
const stats = ref({})
const evaluateResult = ref(null)

const tableData = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const searchForm = reactive({
  severity_level: '',
  review_status: '',
  type: '',
  keyword: ''
})

const reviewForm = reactive({
  review_result: 'confirmed',
  comment: ''
})

let currentRow = null

const typeLabel = (type) => {
  const map = {
    progress: '进度异常',
    duplicate: '内容重复',
    format: '格式错误',
    submission: '提交异常',
    guidance: '指导缺失'
  }
  return map[type] || type
}

const typeTagType = (type) => {
  const map = {
    progress: 'warning',
    duplicate: 'danger',
    format: 'info',
    submission: 'warning',
    guidance: 'primary'
  }
  return map[type] || 'info'
}

const statusLabel = (status) => {
  const map = {
    pending: '待复核',
    confirmed: '已确认',
    ignored: '已忽略',
    resolved: '已处理'
  }
  return map[status] || status
}

const statusTagType = (status) => {
  const map = {
    pending: 'warning',
    confirmed: 'danger',
    ignored: 'info',
    resolved: 'success'
  }
  return map[status] || 'info'
}

const reviewResultLabel = (result) => {
  const map = {
    confirmed: '确认异常',
    ignored: '忽略误报',
    resolved: '已处理'
  }
  return map[result] || result
}

const formatTime = (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'

const loadStats = async () => {
  try {
    const res = await getAnomalyStats()
    stats.value = res
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await getAnomalyList({
      page: pagination.page,
      page_size: pagination.page_size,
      severity_level: searchForm.severity_level || undefined,
      review_status: searchForm.review_status || undefined,
      type: searchForm.type || undefined,
      keyword: searchForm.keyword || undefined
    })
    tableData.value = res.items || res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载异常列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadList()
}

const handleReset = () => {
  searchForm.severity_level = ''
  searchForm.review_status = ''
  searchForm.type = ''
  searchForm.keyword = ''
  pagination.page = 1
  loadList()
}

const handleViewDetail = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  currentDetail.value = null
  reviewHistory.value = []
  try {
    const [detailRes, reviewsRes] = await Promise.all([
      getAnomalyDetail(row.id),
      getAnomalyReviews(row.id)
    ])
    currentDetail.value = detailRes
    reviewHistory.value = reviewsRes.items || reviewsRes.data || []
  } catch (error) {
    console.error('获取详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}

const handleReview = (row) => {
  currentRow = row
  reviewForm.review_result = 'confirmed'
  reviewForm.comment = ''
  reviewVisible.value = true
}

const submitReview = async () => {
  try {
    reviewLoading.value = true
    await reviewAnomaly(currentRow.id, reviewForm)
    ElMessage.success('复核提交成功')
    reviewVisible.value = false
    loadList()
    loadStats()
  } catch (error) {
    console.error('复核失败:', error)
  } finally {
    reviewLoading.value = false
  }
}

const handleDetect = async () => {
  try {
    ElMessage.info('正在启动异常检测，请稍候...')
    await detectAnomaly({})
    ElMessage.success('检测任务已启动')
    loadList()
    loadStats()
  } catch (error) {
    console.error('触发检测失败:', error)
  }
}

const handleEvaluate = async () => {
  evaluateVisible.value = true
  evaluateLoading.value = true
  evaluateResult.value = null
  try {
    const res = await evaluateAnomaly({})
    evaluateResult.value = res
  } catch (error) {
    console.error('评估失败:', error)
  } finally {
    evaluateLoading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadList()
})
</script>

<style scoped lang="scss">
.anomaly-page {
  .stat-row {
    margin-bottom: 16px;

    .stat-card {
      display: flex;
      align-items: center;
      padding: 16px 20px;
      border-radius: 8px;
      background: #fff;
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

      .stat-icon {
        width: 44px;
        height: 44px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        color: #fff;
      }

      .stat-content {
        .stat-value {
          font-size: 24px;
          font-weight: 700;
          line-height: 1.2;
          color: #303133;
        }

        .stat-label {
          font-size: 12px;
          color: #909399;
          margin-top: 4px;
        }
      }

      &.card-total {
        .stat-icon { background: linear-gradient(135deg, #667eea, #764ba2); }
        .stat-value { color: #764ba2; }
      }

      &.card-l1 .stat-value { color: #409eff; }
      &.card-l2 .stat-value { color: #e6a23c; }
      &.card-l3 .stat-value { color: #f56c6c; }
      &.card-pending .stat-value { color: #909399; }
    }

    .action-card {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 10px 0;

      .el-button {
        width: 100%;
      }
    }
  }

  .level-tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;

    &.level-L1 {
      color: #409eff;
      background: #ecf5ff;
    }

    &.level-L2 {
      color: #e6a23c;
      background: #fdf6ec;
    }

    &.level-L3 {
      color: #f56c6c;
      background: #fef0f0;
    }
  }

  .search-card {
    margin-bottom: 16px;
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

  .anomaly-detail {
    .feature-name {
      font-size: 15px;
      font-weight: 600;
      color: #303133;
    }

    .desc-text, .detail-text {
      white-space: pre-wrap;
      line-height: 1.6;
      color: #606266;
    }

    .review-history {
      margin-top: 20px;

      .section-title {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 12px;
      }

      .review-item {
        .reviewer {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
        }

        .review-comment {
          font-size: 12px;
          color: #606266;
        }
      }
    }
  }

  .evaluate-content {
    .evaluate-stats {
      .eval-stat {
        text-align: center;
        padding: 20px;
        background: #f5f7fa;
        border-radius: 8px;

        .eval-value {
          font-size: 28px;
          font-weight: 700;
          color: #409eff;
        }

        .eval-label {
          font-size: 13px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }

    .eval-note {
      margin-top: 16px;
      padding: 10px 12px;
      background: #ecf5ff;
      border-radius: 4px;
      font-size: 12px;
      color: #409eff;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .mt-20 {
      margin-top: 20px;
    }
  }
}
</style>
