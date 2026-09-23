<template>
  <div class="student-anomaly">
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <div class="stat-card" :class="{ active: filter.level === '' }" @click="filter.level = ''; loadList()">
          <div class="stat-value">{{ stats.total || 0 }}</div>
          <div class="stat-label">异常总数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card l1" :class="{ active: filter.level === 'L1' }" @click="filter.level = 'L1'; loadList()">
          <div class="stat-value">{{ stats.L1 || 0 }}</div>
          <div class="stat-label">L1 提示</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card l2" :class="{ active: filter.level === 'L2' }" @click="filter.level = 'L2'; loadList()">
          <div class="stat-value">{{ stats.L2 || 0 }}</div>
          <div class="stat-label">L2 警告</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card l3" :class="{ active: filter.level === 'L3' }" @click="filter.level = 'L3'; loadList()">
          <div class="stat-value">{{ stats.L3 || 0 }}</div>
          <div class="stat-label">L3 告警</div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>异常提示列表</span>
          <el-button text :icon="Refresh" @click="loadAll">刷新</el-button>
        </div>
      </template>

      <el-table :data="records" stripe v-loading="loading">
        <el-table-column prop="severity_level" label="等级" width="60">
          <template #default="{ row }">
            <el-tag :type="severityType(row.severity_level)" size="small">{{ row.severity_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">{{ typeLabel(row.type) }}</template>
        </el-table-column>
        <el-table-column prop="description" label="异常描述" show-overflow-tooltip />
        <el-table-column prop="suggestion" label="处理建议" show-overflow-tooltip />
        <el-table-column prop="review_status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="reviewStatusType(row.review_status)" size="small">
              {{ reviewStatusText(row.review_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detection_time" label="检测时间" width="110">
          <template #default="{ row }">{{ formatDate(row.detection_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button text type="primary" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="filter.page"
        v-model:page-size="filter.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end;"
        @size-change="loadList"
        @current-change="loadList"
      />
    </el-card>

    <el-dialog v-model="detailVisible" title="异常详情" width="600px">
      <el-descriptions :column="2" border v-if="currentDetail">
        <el-descriptions-item label="等级">
          <el-tag :type="severityType(currentDetail.severity_level)" size="small">{{ currentDetail.severity_level }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="类型">{{ typeLabel(currentDetail.type) }}</el-descriptions-item>
        <el-descriptions-item label="异常描述" :span="2">{{ currentDetail.description }}</el-descriptions-item>
        <el-descriptions-item label="处理建议" :span="2">{{ currentDetail.suggestion }}</el-descriptions-item>
        <el-descriptions-item label="异常分数">{{ currentDetail.anomaly_score }}</el-descriptions-item>
        <el-descriptions-item label="置信度">{{ (currentDetail.confidence * 100).toFixed(1) }}%</el-descriptions-item>
        <el-descriptions-item label="复核状态">
          <el-tag :type="reviewStatusType(currentDetail.review_status)" size="small">
            {{ reviewStatusText(currentDetail.review_status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="检测时间">{{ formatDateTime(currentDetail.detection_time) }}</el-descriptions-item>
        <el-descriptions-item label="复核意见" :span="2" v-if="currentDetail.review_opinion">
          {{ currentDetail.review_opinion }}
        </el-descriptions-item>
        <el-descriptions-item label="复核人" v-if="currentDetail.reviewer_name">{{ currentDetail.reviewer_name }}</el-descriptions-item>
        <el-descriptions-item label="复核时间" v-if="currentDetail.review_time">{{ formatDate(currentDetail.review_time) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import studentApi from '@/api/student'

const stats = ref({})
const records = ref([])
const total = ref(0)
const loading = ref(false)
const detailVisible = ref(false)
const currentDetail = ref(null)

const filter = reactive({
  level: '',
  page: 1,
  page_size: 10
})

const severityType = (l) => ({ L1: 'info', L2: 'warning', L3: 'danger' })[l] || 'info'
const typeLabel = (t) => ({ topic: '选题', proposal: '开题', midterm: '中期', thesis: '论文', review: '评阅', student: '综合' })[t] || t || '-'
const reviewStatusText = (s) => ({ pending: '待复核', confirmed: '已确认', false_positive: '误报', ignored: '已忽略' })[s] || s
const reviewStatusType = (s) => ({ pending: 'warning', confirmed: 'danger', false_positive: 'success', ignored: 'info' })[s] || 'info'
const formatDate = (dt) => dt ? new Date(dt).toLocaleDateString('zh-CN') : '-'
const formatDateTime = (dt) => dt ? new Date(dt).toLocaleString('zh-CN') : '-'

const loadStats = async () => {
  try {
    stats.value = await studentApi.getMyAnomalyStats()
  } catch (e) { /* silent */ }
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await studentApi.getMyAnomalyRecords({
      page: filter.page,
      page_size: filter.page_size,
      severity_level: filter.level || undefined
    })
    records.value = res?.items || []
    total.value = res?.total || 0
  } catch (e) { /* silent */ }
  finally { loading.value = false }
}

const loadAll = () => {
  loadStats()
  loadList()
}

const viewDetail = (row) => {
  currentDetail.value = row
  detailVisible.value = true
}

onMounted(loadAll)
</script>

<style scoped lang="scss">
.stats-row { margin-bottom: 16px; }

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  border: 2px solid transparent;

  &:hover { transform: translateY(-2px); }
  &.active { border-color: #409eff; }

  &.l1.active { border-color: #909399; }
  &.l2.active { border-color: #e6a23c; }
  &.l3.active { border-color: #f56c6c; }

  .stat-value { font-size: 28px; font-weight: 700; color: #303133; }
  .stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}
</style>
