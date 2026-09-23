<template>
 <div class="dashboard">
 <!-- 页面标题 -->
 <div class="dashboard-header">
 <h2>{{ isTeacher ? '我的学生数据看板' : '系统数据看板' }}</h2>
 <p v-if="isTeacher" class="sub-title">仅展示您负责指导的学生相关数据</p>
 <p v-else class="sub-title">全局数据概览</p>
 </div>

 <!-- 统计卡片 -->
 <el-row :gutter="20" class="stat-cards">
 <el-col :span="6">
 <div class="stat-card card-1">
 <div class="stat-icon">
 <el-icon size="28"><User /></el-icon>
 </div>
 <div class="stat-info">
 <div class="stat-value">{{ stats.users?.student_count || 0 }}</div>
 <div class="stat-label">{{ isTeacher ? '我的学生' : '学生总数' }}</div>
 </div>
 </div>
 </el-col>
 <el-col :span="6">
 <div class="stat-card card-2">
 <div class="stat-icon">
 <el-icon size="28"><Document /></el-icon>
 </div>
 <div class="stat-info">
 <div class="stat-value">{{ stats.topics?.total || 0 }}</div>
 <div class="stat-label">{{ isTeacher ? '指导选题' : '选题总数' }}</div>
 </div>
 </div>
 </el-col>
 <el-col :span="6">
 <div class="stat-card card-3">
 <div class="stat-icon">
 <el-icon size="28"><Warning /></el-icon>
 </div>
 <div class="stat-info">
 <div class="stat-value">{{ stats.anomalies?.total || 0 }}</div>
 <div class="stat-label">{{ isTeacher ? '学生异常' : '异常记录' }}</div>
 </div>
 </div>
 </el-col>
 <el-col :span="6">
 <div class="stat-card card-4">
 <div class="stat-icon">
 <el-icon size="28"><Box /></el-icon>
 </div>
 <div class="stat-info">
 <div class="stat-value">{{ stats.archives?.total || 0 }}</div>
 <div class="stat-label">已归档</div>
 </div>
 </div>
 </el-col>
 </el-row>

 <!-- 图表区域 -->
 <el-row :gutter="20" class="chart-row">
 <el-col :span="12">
 <div class="chart-card">
 <div class="chart-title">选题状态分布</div>
 <v-chart class="chart" :option="topicPieOption" autoresize />
 </div>
 </el-col>
 <el-col :span="12">
 <div class="chart-card">
 <div class="chart-title">异常检测趋势（近7天）</div>
 <v-chart class="chart" :option="anomalyTrendOption" autoresize />
 </div>
 </el-col>
 </el-row>

 <el-row :gutter="20" class="chart-row">
 <el-col :span="8">
 <div class="chart-card">
 <div class="chart-title">各环节完成情况</div>
 <v-chart class="chart" :option="progressOption" autoresize />
 </div>
 </el-col>
 <el-col :span="8">
 <div class="chart-card">
 <div class="chart-title">异常等级分布</div>
 <v-chart class="chart" :option="anomalyLevelOption" autoresize />
 </div>
 </el-col>
 </el-row>

 <!-- 待处理异常 -->
 <div class="card mt-20">
 <div class="card-header">
 <span class="card-title">{{ isTeacher ? '我的学生待处理异常' : '待处理异常' }}</span>
 <el-button type="primary" link @click="$router.push('/anomaly')">查看全部</el-button>
 </div>
 <el-table :data="pendingAnomalies" stripe v-loading="loading">
 <el-table-column prop="id" label="ID" width="80" />
 <el-table-column prop="feature_name" label="异常特征" />
 <el-table-column prop="severity_level" label="等级" width="100">
 <template #default="{ row }">
 <span :class="`anomaly-${row.severity_level}`">{{ row.severity_level }}</span>
 </template>
 </el-table-column>
 <el-table-column prop="description" label="描述" show-overflow-tooltip />
 <el-table-column prop="detection_time" label="检测时间" width="180">
 <template #default="{ row }">
 {{ formatTime(row.detection_time) }}
 </template>
 </el-table-column>
 </el-table>
 </div>
 </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/store/user'
import { getOverviewStats, getTopicStatusDistribution, getAnomalyTrend } from '@/api/stats'
import { getAnomalyList } from '@/api/anomaly'
import dayjs from 'dayjs'

const userStore = useUserStore()
const loading = ref(false)
const stats = ref({})
const topicStatusData = ref([])
const anomalyTrendData = ref([])
const pendingAnomalies = ref([])

const isTeacher = computed(() => userStore.userInfo?.role === 'teacher')

const formatTime = (time) => {
 return time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'
}

// 选题状态饼图
const topicPieOption = computed(() => ({
 tooltip: { trigger: 'item' },
 legend: { bottom: '5%', left: 'center' },
 series: [{
 type: 'pie',
 radius: ['40%', '70%'],
 avoidLabelOverlap: false,
 itemStyle: {
 borderRadius: 10,
 borderColor: '#fff',
 borderWidth: 2
 },
 label: { show: false },
 emphasis: {
 label: { show: true, fontSize: 14, fontWeight: 'bold' }
 },
 data: topicStatusData.value.map(item => ({
 name: item.label || item.status,
 value: item.value || item.count
 }))
 }],
 color: ['#67C23A', '#E6A23C', '#F56C6C', '#909399']
}))

// 异常趋势图
const anomalyTrendOption = computed(() => ({
 tooltip: { trigger: 'axis' },
 legend: { data: ['L1提示', 'L2警告', 'L3告警'] },
 grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
 xAxis: {
 type: 'category',
 boundaryGap: false,
 data: anomalyTrendData.value.map(item => item.date?.slice(5) || '')
 },
 yAxis: { type: 'value' },
 series: [
 {
 name: 'L1提示',
 type: 'line',
 smooth: true,
 data: anomalyTrendData.value.map(item => item.L1 || 0),
 lineStyle: { color: '#409eff' },
 itemStyle: { color: '#409eff' },
 areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
 { offset: 0, color: 'rgba(64,158,255,0.3)' },
 { offset: 1, color: 'rgba(64,158,255,0.05)' }
 ]}}
 },
 {
 name: 'L2警告',
 type: 'line',
 smooth: true,
 data: anomalyTrendData.value.map(item => item.L2 || 0),
 lineStyle: { color: '#E6A23C' },
 itemStyle: { color: '#E6A23C' }
 },
 {
 name: 'L3告警',
 type: 'line',
 smooth: true,
 data: anomalyTrendData.value.map(item => item.L3 || 0),
 lineStyle: { color: '#F56C6C' },
 itemStyle: { color: '#F56C6C' }
 }
 ]
}))

// 各环节进度
const progressOption = computed(() => ({
 tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
 grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
 xAxis: { type: 'value', max: 100 },
 yAxis: {
 type: 'category',
 data: ['选题', '开题', '中期', '评阅', '答辩', '归档']
 },
 series: [{
 type: 'bar',
 data: [
 { value: stats.value.topics?.approved_rate || 0, itemStyle: { color: '#67C23A' } },
 { value: stats.value.proposals?.approved_rate || 0, itemStyle: { color: '#409eff' } },
 { value: stats.value.midterm?.passed_rate || 0, itemStyle: { color: '#E6A23C' } },
 { value: stats.value.reviews?.completion_rate || 0, itemStyle: { color: '#909399' } },
 { value: stats.value.defenses?.completion_rate || 0, itemStyle: { color: '#7c3aed' } },
 { value: stats.value.archives?.archived_rate || 0, itemStyle: { color: '#16a34a' } }
 ],
 barWidth: 20,
 label: {
 show: true,
 position: 'right',
 formatter: '{c}%'
 }
 }]
}))

// 异常等级分布
const anomalyLevelOption = computed(() => ({
 tooltip: { trigger: 'item' },
 series: [{
 type: 'gauge',
 startAngle: 180,
 endAngle: 0,
 min: 0,
 max: stats.value.anomalies?.total || 100,
 splitNumber: 4,
 radius: '90%',
 axisLine: {
 lineStyle: {
 width: 20,
 color: [
 [0.6, '#67C23A'],
 [0.8, '#E6A23C'],
 [1, '#F56C6C']
 ]
 }
 },
 pointer: { show: false },
 axisTick: { show: false },
 splitLine: { show: false },
 axisLabel: { show: false },
 detail: {
 valueAnimation: true,
 formatter: '{value}',
 fontSize: 32,
 color: '#303133',
 offsetCenter: [0, '20%']
 },
 data: [{ value: stats.value.anomalies?.pending || 0, name: '待处理异常' }],
 title: {
 show: true,
 fontSize: 14,
 color: '#909399',
 offsetCenter: [0, '50%']
 }
 }]
}))

const loadData = async () => {
 loading.value = true
 try {
 const [overviewRes, topicRes, trendRes, anomalyRes] = await Promise.all([
 getOverviewStats(),
 getTopicStatusDistribution(),
 getAnomalyTrend(7),
 getAnomalyList({ page: 1, page_size: 5, review_status: 'pending' })
 ])

 stats.value = overviewRes
 topicStatusData.value = topicRes
 anomalyTrendData.value = trendRes
 pendingAnomalies.value = anomalyRes.items || []
 } catch (error) {
 console.error('加载统计数据失败:', error)
 } finally {
 loading.value = false
 }
}

onMounted(() => {
 loadData()
})
</script>

<style scoped lang="scss">
.dashboard {
 .dashboard-header {
 margin-bottom: 20px;

 h2 {
 font-size: 20px;
 font-weight: 600;
 color: #303133;
 margin: 0 0 4px 0;
 }

 .sub-title {
 font-size: 13px;
 color: #909399;
 margin: 0;
 }
 }

 .stat-cards {
    margin-bottom: 20px;

    .stat-card {
      display: flex;
      align-items: center;
      padding: 24px;
      border-radius: 10px;
      color: #fff;
      position: relative;
      overflow: hidden;

      &.card-1 { background: linear-gradient(135deg, #667eea, #764ba2); }
      &.card-2 { background: linear-gradient(135deg, #f093fb, #f5576c); }
      &.card-3 { background: linear-gradient(135deg, #fa709a, #fee140); }
      &.card-4 { background: linear-gradient(135deg, #4facfe, #00f2fe); }

      .stat-icon {
        width: 56px;
        height: 56px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
      }

      .stat-info {
        .stat-value {
          font-size: 28px;
          font-weight: 700;
          line-height: 1.2;
        }

        .stat-label {
          font-size: 13px;
          opacity: 0.85;
          margin-top: 4px;
        }
      }
    }
  }

  .chart-row {
    margin-bottom: 20px;

    .chart-card {
      background: #fff;
      border-radius: 10px;
      padding: 20px;
      height: 320px;
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

      .chart-title {
        font-size: 15px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 12px;
      }

      .chart {
        height: 260px;
        width: 100%;
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .card-title {
      font-size: 15px;
      font-weight: 600;
      color: #303133;
    }
  }
}
</style>
