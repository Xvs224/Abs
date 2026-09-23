<template>
  <div class="student-reviews">
    <!-- 评阅结果 -->
    <template v-if="!isDefenseRoute">
      <el-card shadow="never" v-loading="loadingReviews">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>论文评阅</span>
            <el-button :icon="Refresh" size="small" @click="loadReviews">刷新</el-button>
          </div>
        </template>
        <div v-if="reviews.length > 0">
          <div v-for="item in reviews" :key="item.id" class="review-item">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="状态">
                <el-tag :type="reviewStatusType(item.status)" size="small">{{ reviewStatusText(item.status) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="评阅成绩">
                <span v-if="item.total_score" class="score">{{ item.total_score }} 分</span>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="选题质量">{{ item.topic_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="论文质量">{{ item.content_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="研究方法">{{ item.method_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="创新性">{{ item.innovation_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="格式规范">{{ item.format_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="评阅时间">{{ formatDate(item.review_time) }}</el-descriptions-item>
              <el-descriptions-item label="评阅意见" :span="2" v-if="item.opinion">{{ item.opinion }}</el-descriptions-item>
              <el-descriptions-item label="修改建议" :span="2" v-if="item.suggestions">{{ item.suggestions }}</el-descriptions-item>
              <el-descriptions-item label="评审结论" :span="2" v-if="item.result">
                <el-tag :type="resultType(item.result)" size="small">{{ resultText(item.result) }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
        <el-empty v-else description="暂无评阅记录" />
      </el-card>
    </template>

    <!-- 答辩安排 -->
    <template v-else>
      <el-card shadow="never" v-loading="loadingDefense">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>答辩评价</span>
            <el-button :icon="Refresh" size="small" @click="loadDefense">刷新</el-button>
          </div>
        </template>
        <div v-if="defense">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="状态">
              <el-tag :type="defenseStatusType(defense.status)" size="small">{{ defenseStatusText(defense.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="答辩形式">{{ defenseFormText(defense.defense_form) }}</el-descriptions-item>
            <el-descriptions-item label="答辩日期">{{ formatDate(defense.defense_date) }}</el-descriptions-item>
            <el-descriptions-item label="答辩时间">
              {{ defense.defense_time_start || '-' }} ~ {{ defense.defense_time_end || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="答辩地点" :span="2">{{ defense.location || '-' }}</el-descriptions-item>
            <el-descriptions-item label="答辩委员会" :span="2">{{ defense.committee_members || '-' }}</el-descriptions-item>
            <el-descriptions-item label="答辩成绩" v-if="defense.total_score">
              <span class="score">{{ defense.total_score }} 分</span>
            </el-descriptions-item>
            <el-descriptions-item label="成绩等级" v-if="defense.grade">
              <el-tag type="success" size="small">{{ defense.grade }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="答辩评语" :span="2" v-if="defense.opinion">{{ defense.opinion }}</el-descriptions-item>
            <el-descriptions-item label="答辩建议" :span="2" v-if="defense.suggestions">{{ defense.suggestions }}</el-descriptions-item>
            <el-descriptions-item label="答辩结果" :span="2" v-if="defense.result">
              <el-tag :type="defenseResultType(defense.result)" size="small">
                {{ defenseResultText(defense.result) }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        <el-empty v-else description="暂无答辩安排" />
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import studentApi from '@/api/student'

const route = useRoute()
// 根据路由路径决定显示评阅还是答辩
const isDefenseRoute = computed(() => route.path.includes('/defense'))

const reviews = ref([])
const defense = ref(null)
const loadingReviews = ref(false)
const loadingDefense = ref(false)
let timer = null

const formatDate = (dt) => dt ? new Date(dt).toLocaleDateString('zh-CN') : '-'

const reviewStatusText = (s) => ({ pending: '待评阅', reviewing: '评阅中', completed: '已完成' })[s] || s
const reviewStatusType = (s) => ({ pending: 'info', reviewing: 'warning', completed: 'success' })[s] || 'info'

const resultText = (r) => ({ pass: '同意答辩', revision: '修改后答辩', reject: '不同意答辩' })[r] || r
const resultType = (r) => ({ pass: 'success', revision: 'warning', reject: 'danger' })[r] || 'info'

const defenseStatusText = (s) => ({ scheduled: '已安排', completed: '已完成', pending: '待安排', in_progress: '进行中' })[s] || s
const defenseStatusType = (s) => ({ scheduled: 'warning', completed: 'success', pending: 'info', in_progress: 'warning' })[s] || 'info'
const defenseFormText = (f) => ({ offline: '线下答辩', online: '线上答辩' })[f] || f || '-'

const defenseResultText = (r) => ({ pass: '通过', fail: '未通过', reargue: '需重新答辩' })[r] || r
const defenseResultType = (r) => ({ pass: 'success', fail: 'danger', reargue: 'warning' })[r] || 'info'

const loadReviews = async () => {
  loadingReviews.value = true
  try {
    const res = await studentApi.getMyReviews()
    reviews.value = res?.items || []
  } catch (e) { /* silent */ }
  finally { loadingReviews.value = false }
}

const loadDefense = async () => {
  loadingDefense.value = true
  try {
    const res = await studentApi.getMyDefenses()
    defense.value = res?.items?.[0] || null
  } catch (e) { /* silent */ }
  finally { loadingDefense.value = false }
}

// 根据当前路由加载对应数据
const loadCurrentData = () => {
  if (isDefenseRoute.value) {
    loadDefense()
  } else {
    loadReviews()
  }
}

// 路由切换时重新加载
watch(isDefenseRoute, loadCurrentData)

onMounted(() => {
  loadCurrentData()
  // 每30秒自动刷新，确保教师提交评阅后学生端状态能自动同步
  timer = setInterval(loadCurrentData, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped lang="scss">
.review-item {
  margin-bottom: 20px;
}

.score {
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
}
</style>
