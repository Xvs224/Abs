<template>
  <div class="reviews-page">
    <!-- 评阅管理 -->
    <template v-if="!isDefenseRoute">
      <el-card class="search-card" shadow="never">
          <el-form :inline="true" :model="reviewSearchForm">
            <el-form-item label="状态">
              <el-select v-model="reviewSearchForm.status" placeholder="全部状态" clearable style="width: 140px">
                <el-option label="待分配" value="pending" />
                <el-option label="评阅中" value="reviewing" />
                <el-option label="已完成" value="completed" />
              </el-select>
            </el-form-item>
            <el-form-item label="关键词">
              <el-input
                v-model="reviewSearchForm.keyword"
                placeholder="搜索学生/论文"
                clearable
                style="width: 240px"
                @keyup.enter="loadReviewList"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="loadReviewList">搜索</el-button>
              <el-button :icon="Refresh" @click="resetReviewSearch">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="table-card" shadow="never">
          <div class="table-toolbar">
            <div class="toolbar-left">
              <el-button type="primary" :icon="Plus" @click="handleAssignReviewer">
                分配评阅
              </el-button>
              <el-button :icon="RefreshRight" @click="loadReviewList">刷新</el-button>
            </div>
          </div>

          <el-table :data="reviewList" v-loading="reviewLoading" stripe border>
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="topic_title" label="论文题目" min-width="200" show-overflow-tooltip />
            <el-table-column prop="student_name" label="学生" width="100" />
            <el-table-column prop="reviewer_name" label="评阅教师" width="100">
              <template #default="{ row }">
                {{ row.reviewer_name || '未分配' }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="reviewStatusTagType(row.status)" size="small">
                  {{ reviewStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_score" label="评阅成绩" width="100" align="center">
              <template #default="{ row }">
                <span v-if="row.total_score !== undefined && row.total_score !== null" :class="scoreClass(row.total_score)">
                  {{ row.total_score }}
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="分配时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.create_time) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleViewReview(row)">查看</el-button>
                <el-button
                  v-if="row.status === 'pending'"
                  type="success"
                  link
                  size="small"
                  @click="handleAssignReviewer(row)"
                >
                  分配
                </el-button>
                <el-button
                  v-if="row.status === 'reviewing'"
                  type="warning"
                  link
                  size="small"
                  @click="handleSubmitReview(row)"
                >
                  提交评阅
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="reviewPagination.page"
              v-model:page-size="reviewPagination.page_size"
              :page-sizes="[10, 20, 50]"
              :total="reviewPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              background
              @size-change="loadReviewList"
              @current-change="loadReviewList"
            />
          </div>
        </el-card>
    </template>

    <!-- 答辩管理 -->
    <template v-else>
      <el-card class="search-card" shadow="never">
          <el-form :inline="true" :model="defenseSearchForm">
            <el-form-item label="状态">
              <el-select v-model="defenseSearchForm.status" placeholder="全部状态" clearable style="width: 140px">
                <el-option label="待安排" value="pending" />
                <el-option label="已安排" value="scheduled" />
                <el-option label="已完成" value="completed" />
              </el-select>
            </el-form-item>
            <el-form-item label="关键词">
              <el-input
                v-model="defenseSearchForm.keyword"
                placeholder="搜索学生/论文"
                clearable
                style="width: 240px"
                @keyup.enter="loadDefenseList"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="loadDefenseList">搜索</el-button>
              <el-button :icon="Refresh" @click="resetDefenseSearch">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="table-card" shadow="never">
          <div class="table-toolbar">
            <div class="toolbar-left">
              <el-button type="primary" :icon="Plus" @click="handleScheduleDefense">
                安排答辩
              </el-button>
              <el-button :icon="RefreshRight" @click="loadDefenseList">刷新</el-button>
            </div>
          </div>

          <el-table :data="defenseList" v-loading="defenseLoading" stripe border>
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="topic_title" label="论文题目" min-width="180" show-overflow-tooltip />
            <el-table-column prop="student_name" label="学生" width="100" />
            <el-table-column prop="committee_members" label="答辩委员会" width="150" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.committee_members || '未安排' }}
              </template>
            </el-table-column>
            <el-table-column label="答辩时间" width="160">
              <template #default="{ row }">
                {{ formatDefenseTime(row) }}
              </template>
            </el-table-column>
            <el-table-column prop="location" label="答辩地点" width="120" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.location || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="defenseStatusTagType(row.status)" size="small">
                  {{ defenseStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_score" label="答辩成绩" width="100" align="center">
              <template #default="{ row }">
                <span v-if="row.total_score !== undefined && row.total_score !== null" :class="scoreClass(row.total_score)">
                  {{ row.total_score }}
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleViewDefense(row)">查看</el-button>
                <el-button
                  v-if="row.status === 'pending'"
                  type="success"
                  link
                  size="small"
                  @click="handleScheduleDefense(row)"
                >
                  安排
                </el-button>
                <el-button
                  v-if="row.status === 'scheduled'"
                  type="warning"
                  link
                  size="small"
                  @click="handleScoreDefense(row)"
                >
                  评分
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="defensePagination.page"
              v-model:page-size="defensePagination.page_size"
              :page-sizes="[10, 20, 50]"
              :total="defensePagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              background
              @size-change="loadDefenseList"
              @current-change="loadDefenseList"
            />
          </div>
        </el-card>
    </template>

    <!-- 分配评阅对话框 -->
    <el-dialog v-model="assignDialogVisible" title="分配评阅教师" width="500px" :close-on-click-modal="false">
      <el-form ref="assignFormRef" :model="assignForm" :rules="assignRules" label-width="100px">
        <el-form-item label="论文题目" prop="topic_id">
          <el-select
            v-model="assignForm.topic_id"
            placeholder="请选择论文题目"
            filterable
            style="width: 100%"
            :loading="topicLoading"
          >
            <el-option
              v-for="topic in topicOptions"
              :key="topic.id"
              :label="`${topic.title}（${topic.student_name}）`"
              :value="topic.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="评阅教师" prop="reviewer_id">
          <el-input v-model="assignForm.reviewer_id" placeholder="请输入评阅教师工号" />
        </el-form-item>
        <el-form-item label="截止日期" prop="deadline">
          <el-date-picker
            v-model="assignForm.deadline"
            type="date"
            placeholder="选择评阅截止日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="assignLoading" v-if='isTeacher' @click="submitAssign">确认分配</el-button>
      </template>
    </el-dialog>

    <!-- 提交评阅对话框 -->
    <el-dialog v-model="reviewSubmitDialogVisible" title="提交评阅意见" width="600px" :close-on-click-modal="false">
      <el-form ref="reviewSubmitFormRef" :model="reviewSubmitForm" :rules="reviewSubmitRules" label-width="100px">
        <el-form-item label="评阅成绩" prop="total_score">
          <el-input-number v-model="reviewSubmitForm.total_score" :min="0" :max="100" :precision="1" />
          <span class="form-tip">满分 100 分</span>
        </el-form-item>
        <el-form-item label="总体评价" prop="opinion">
          <el-input
            v-model="reviewSubmitForm.opinion"
            type="textarea"
            :rows="2"
            placeholder="请输入总体评价"
          />
        </el-form-item>
        <el-form-item label="选题质量" prop="topic_score">
          <el-rate v-model="reviewSubmitForm.topic_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="内容质量" prop="content_score">
          <el-rate v-model="reviewSubmitForm.content_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="研究方法" prop="method_score">
          <el-rate v-model="reviewSubmitForm.method_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="创新性" prop="innovation_score">
          <el-rate v-model="reviewSubmitForm.innovation_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="格式规范" prop="format_score">
          <el-rate v-model="reviewSubmitForm.format_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="详细意见" prop="suggestions">
          <el-input
            v-model="reviewSubmitForm.suggestions"
            type="textarea"
            :rows="4"
            placeholder="请输入详细评阅意见"
          />
        </el-form-item>
        <el-form-item label="结论" prop="result">
          <el-radio-group v-model="reviewSubmitForm.result">
            <el-radio value="pass">同意答辩</el-radio>
            <el-radio value="revision">修改后答辩</el-radio>
            <el-radio value="reject">不同意答辩</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewSubmitDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewSubmitLoading" v-if='isTeacher' @click="submitReviewForm">
          提交评阅
        </el-button>
      </template>
    </el-dialog>

    <!-- 安排答辩对话框 -->
    <el-dialog v-model="scheduleDialogVisible" title="安排答辩" width="500px" :close-on-click-modal="false">
      <el-form ref="scheduleFormRef" :model="scheduleForm" :rules="scheduleRules" label-width="100px">
        <el-form-item label="论文题目" prop="topic_id">
          <el-select
            v-model="scheduleForm.topic_id"
            placeholder="请选择论文题目"
            filterable
            style="width: 100%"
            :loading="topicLoading"
          >
            <el-option
              v-for="topic in topicOptions"
              :key="topic.id"
              :label="`${topic.title}（${topic.student_name}）`"
              :value="topic.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="答辩日期" prop="defense_date">
          <el-date-picker
            v-model="scheduleForm.defense_date"
            type="date"
            placeholder="选择答辩日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="开始时间" prop="defense_time_start">
          <el-time-picker
            v-model="scheduleForm.defense_time_start"
            placeholder="选择开始时间"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" prop="defense_time_end">
          <el-time-picker
            v-model="scheduleForm.defense_time_end"
            placeholder="选择结束时间"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="答辩地点" prop="location">
          <el-input v-model="scheduleForm.location" placeholder="请输入答辩地点" />
        </el-form-item>
        <el-form-item label="答辩委员会" prop="committee_members">
          <el-input v-model="scheduleForm.committee_members" placeholder="请输入答辩委员会成员" />
        </el-form-item>
        <el-form-item label="答辩秘书" prop="secretary_id">
          <el-input v-model="scheduleForm.secretary_id" placeholder="请输入答辩秘书工号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="scheduleLoading" @click="submitSchedule">确认安排</el-button>
      </template>
    </el-dialog>

    <!-- 答辩评分对话框 -->
    <el-dialog v-model="scoreDialogVisible" title="答辩评分" width="600px" :close-on-click-modal="false">
      <el-form ref="scoreFormRef" :model="scoreForm" :rules="scoreRules" label-width="100px">
        <el-form-item label="报告内容" prop="presentation_score">
          <el-rate v-model="scoreForm.presentation_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="答辩表现" prop="qa_score">
          <el-rate v-model="scoreForm.qa_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="论文质量" prop="thesis_quality_score">
          <el-rate v-model="scoreForm.thesis_quality_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="答辩成绩" prop="total_score">
          <el-input-number v-model="scoreForm.total_score" :min="0" :max="100" :precision="1" />
          <span class="form-tip">满分 100 分</span>
        </el-form-item>
        <el-form-item label="答辩评语" prop="opinion">
          <el-input
            v-model="scoreForm.opinion"
            type="textarea"
            :rows="4"
            placeholder="请输入答辩评语"
          />
        </el-form-item>
        <el-form-item label="答辩结果" prop="result">
          <el-radio-group v-model="scoreForm.result">
            <el-radio value="pass">通过</el-radio>
            <el-radio value="fail">不通过</el-radio>
            <el-radio value="reargue">二次答辩</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scoreDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="scoreLoading" v-if='isTeacher' @click="submitScore">提交评分</el-button>
      </template>
    </el-dialog>

    <!-- 评阅详情对话框 -->
    <el-dialog v-model="reviewDetailVisible" title="评阅详情" width="600px">
      <el-descriptions :column="2" border v-if="currentReviewDetail">
        <el-descriptions-item label="论文题目" :span="2">{{ currentReviewDetail.topic_title }}</el-descriptions-item>
        <el-descriptions-item label="学生">{{ currentReviewDetail.student_name }}</el-descriptions-item>
        <el-descriptions-item label="评阅教师">{{ currentReviewDetail.reviewer_name || '未分配' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="reviewStatusTagType(currentReviewDetail.status)" size="small">
            {{ reviewStatusLabel(currentReviewDetail.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="评阅成绩">
          <span v-if="currentReviewDetail.total_score !== undefined" :class="scoreClass(currentReviewDetail.total_score)">
            {{ currentReviewDetail.total_score }}
          </span>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="评阅意见" :span="2">
          <div class="detail-content">{{ currentReviewDetail.suggestions || '暂无' }}</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 答辩详情对话框 -->
    <el-dialog v-model="defenseDetailVisible" title="答辩详情" width="600px">
      <el-descriptions :column="2" border v-if="currentDefenseDetail">
        <el-descriptions-item label="论文题目" :span="2">{{ currentDefenseDetail.topic_title }}</el-descriptions-item>
        <el-descriptions-item label="学生">{{ currentDefenseDetail.student_name }}</el-descriptions-item>
        <el-descriptions-item label="答辩委员会">{{ currentDefenseDetail.committee_members || '未安排' }}</el-descriptions-item>
        <el-descriptions-item label="答辩时间">{{ formatDefenseTime(currentDefenseDetail) }}</el-descriptions-item>
        <el-descriptions-item label="答辩地点">{{ currentDefenseDetail.location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="defenseStatusTagType(currentDefenseDetail.status)" size="small">
            {{ defenseStatusLabel(currentDefenseDetail.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="答辩成绩">
          <span v-if="currentDefenseDetail.total_score !== undefined" :class="scoreClass(currentDefenseDetail.total_score)">
            {{ currentDefenseDetail.total_score }}
          </span>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="答辩评语" :span="2">
          <div class="detail-content">{{ currentDefenseDetail.opinion || '暂无' }}</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { useUserStore } from '@/store/user' 
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus, RefreshRight } from '@element-plus/icons-vue'
import request from '@/utils/request'
import dayjs from 'dayjs'
import { getTopicList } from '@/api/topic'


const userStore = useUserStore()
const isTeacher = computed(() => userStore.userInfo?.role === 'teacher')

const route = useRoute()
// 根据路由路径决定显示评阅还是答辩模块
const isDefenseRoute = computed(() => route.path.includes('/defense'))

// 评阅相关
const reviewLoading = ref(false)
const reviewList = ref([])
const reviewPagination = reactive({ page: 1, page_size: 10, total: 0 })
const reviewSearchForm = reactive({ status: '', keyword: '' })
const assignDialogVisible = ref(false)
const assignLoading = ref(false)
const assignFormRef = ref(null)
const reviewSubmitDialogVisible = ref(false)
const reviewSubmitLoading = ref(false)
const reviewSubmitFormRef = ref(null)
const reviewDetailVisible = ref(false)
const currentReviewDetail = ref(null)

const assignForm = reactive({ topic_id: null, reviewer_id: '', deadline: '' })
const assignRules = {
  topic_id: [{ required: true, message: '请选择论文题目', trigger: 'change' }],
  reviewer_id: [{ required: true, message: '请输入评阅教师工号', trigger: 'blur' }]
}

const reviewSubmitForm = reactive({
  total_score: null,
  opinion: '',
  topic_score: 7,
  content_score: 7,
  method_score: 7,
  innovation_score: 7,
  format_score: 7,
  suggestions: '',
  result: 'pass'
})
const reviewSubmitRules = {
  total_score: [{ required: true, message: '请输入评阅成绩', trigger: 'blur' }],
  suggestions: [{ required: true, message: '请输入评阅意见', trigger: 'blur' }]
}

// 答辩相关
const defenseLoading = ref(false)
const defenseList = ref([])
const defensePagination = reactive({ page: 1, page_size: 10, total: 0 })
const defenseSearchForm = reactive({ status: '', keyword: '' })
const scheduleDialogVisible = ref(false)
const scheduleLoading = ref(false)
const scheduleFormRef = ref(null)
const scoreDialogVisible = ref(false)
const scoreLoading = ref(false)
const scoreFormRef = ref(null)
const defenseDetailVisible = ref(false)
const currentDefenseDetail = ref(null)

const scheduleForm = reactive({
  topic_id: null,
  defense_date: '',
  defense_time_start: '',
  defense_time_end: '',
  location: '',
  committee_members: '',
  secretary_id: ''
})
const scheduleRules = {
  topic_id: [{ required: true, message: '请选择论文题目', trigger: 'change' }],
  defense_date: [{ required: true, message: '请选择答辩日期', trigger: 'change' }],
  defense_time_start: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  defense_time_end: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  location: [{ required: true, message: '请输入答辩地点', trigger: 'blur' }]
}

const topicOptions = ref([])
const topicLoading = ref(false)

const scoreForm = reactive({
  presentation_score: 7,
  qa_score: 7,
  thesis_quality_score: 7,
  total_score: null,
  opinion: '',
  grade: '',
  result: 'pass'
})
const scoreRules = {
  total_score: [{ required: true, message: '请输入答辩成绩', trigger: 'blur' }],
  opinion: [{ required: true, message: '请输入答辩评语', trigger: 'blur' }],
  result: [{ required: true, message: '请选择答辩结果', trigger: 'change' }]
}

let currentRow = null

const reviewStatusLabel = (status) => {
  const map = { pending: '待分配', reviewing: '评阅中', completed: '已完成' }
  return map[status] || status
}

const reviewStatusTagType = (status) => {
  const map = { pending: 'warning', reviewing: 'primary', completed: 'success' }
  return map[status] || 'info'
}

const defenseStatusLabel = (status) => {
  const map = { pending: '待安排', scheduled: '已安排', completed: '已完成' }
  return map[status] || status
}

const defenseStatusTagType = (status) => {
  const map = { pending: 'warning', scheduled: 'primary', completed: 'success' }
  return map[status] || 'info'
}

const scoreClass = (score) => {
  if (score >= 90) return 'score-excellent'
  if (score >= 80) return 'score-good'
  if (score >= 60) return 'score-pass'
  return 'score-fail'
}

const formatTime = (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'

const formatDefenseTime = (row) => {
  if (!row || !row.defense_date) return '-'
  let str = dayjs(row.defense_date).format('YYYY-MM-DD')
  if (row.defense_time_start) {
    str += ' ' + row.defense_time_start
    if (row.defense_time_end) str += '-' + row.defense_time_end
  }
  return str
}

const loadReviewList = async () => {
  reviewLoading.value = true
  try {
    const res = await request.get('/reviews', {
      page: reviewPagination.page,
      page_size: reviewPagination.page_size,
      status: reviewSearchForm.status || undefined,
      keyword: reviewSearchForm.keyword || undefined
    })
    reviewList.value = res.items || res.data || []
    reviewPagination.total = res.total || 0
  } catch (error) {
    console.error('加载评阅列表失败:', error)
  } finally {
    reviewLoading.value = false
  }
}

const resetReviewSearch = () => {
  reviewSearchForm.status = ''
  reviewSearchForm.keyword = ''
  reviewPagination.page = 1
  loadReviewList()
}

const loadDefenseList = async () => {
  defenseLoading.value = true
  try {
    const res = await request.get('/defenses', {
      page: defensePagination.page,
      page_size: defensePagination.page_size,
      status: defenseSearchForm.status || undefined,
      keyword: defenseSearchForm.keyword || undefined
    })
    defenseList.value = res.items || res.data || []
    defensePagination.total = res.total || 0
  } catch (error) {
    console.error('加载答辩列表失败:', error)
  } finally {
    defenseLoading.value = false
  }
}

const resetDefenseSearch = () => {
  defenseSearchForm.status = ''
  defenseSearchForm.keyword = ''
  defensePagination.page = 1
  loadDefenseList()
}

// 评阅操作
const handleAssignReviewer = (row) => {
  currentRow = row
  assignForm.topic_id = row?.topic_id || null
  assignForm.reviewer_id = ''
  assignForm.deadline = ''
  assignDialogVisible.value = true
  loadTopicOptions(reviewList.value.map(r => r.topic_id))
}

// 加载选题列表（排除已使用的选题）
const loadTopicOptions = async (usedTopicIds = []) => {
  topicLoading.value = true
  try {
    const res = await getTopicList({ page: 1, page_size: 100, status: 'approved' })
    const topics = res.items || res.data || []
    topicOptions.value = topics.filter(t => !usedTopicIds.includes(t.id))
  } catch (error) {
    console.error('加载选题列表失败:', error)
  } finally {
    topicLoading.value = false
  }
}

const submitAssign = async () => {
  if (!assignFormRef.value) return
  try {
    await assignFormRef.value.validate()
    assignLoading.value = true
    const payload = {
      topic_id: assignForm.topic_id,
      reviewer_id: parseInt(assignForm.reviewer_id),
      deadline: assignForm.deadline
    }
    if (currentRow?.student_id) payload.student_id = currentRow.student_id
    if (!payload.deadline) delete payload.deadline
    await request.post('/reviews', payload)
    ElMessage.success('分配成功')
    assignDialogVisible.value = false
    loadReviewList()
  } catch (error) {
    if (error !== false) {
      console.error('分配失败:', error)
    }
  } finally {
    assignLoading.value = false
  }
}

const handleSubmitReview = (row) => {
  currentRow = row
  reviewSubmitForm.total_score = null
  reviewSubmitForm.opinion = ''
  reviewSubmitForm.topic_score = 7
  reviewSubmitForm.content_score = 7
  reviewSubmitForm.method_score = 7
  reviewSubmitForm.innovation_score = 7
  reviewSubmitForm.format_score = 7
  reviewSubmitForm.suggestions = ''
  reviewSubmitForm.result = 'pass'
  reviewSubmitDialogVisible.value = true
}

const submitReviewForm = async () => {
  if (!reviewSubmitFormRef.value) return
  try {
    await reviewSubmitFormRef.value.validate()
    reviewSubmitLoading.value = true
    // 将 0-10 评分转换为 0-100 分制
    const payload = {
      ...reviewSubmitForm,
      topic_score: reviewSubmitForm.topic_score * 10,
      content_score: reviewSubmitForm.content_score * 10,
      method_score: reviewSubmitForm.method_score * 10,
      innovation_score: reviewSubmitForm.innovation_score * 10,
      format_score: reviewSubmitForm.format_score * 10
    }
    await request.post(`/reviews/${currentRow.id}/submit`, payload)
    ElMessage.success('评阅提交成功')
    reviewSubmitDialogVisible.value = false
    loadReviewList()
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error)
    }
  } finally {
    reviewSubmitLoading.value = false
  }
}

const handleViewReview = async (row) => {
  reviewDetailVisible.value = true
  try {
    const res = await request.get(`/reviews/${row.id}`)
    currentReviewDetail.value = res
  } catch (error) {
    console.error('获取详情失败:', error)
  }
}

// 答辩操作
const handleScheduleDefense = (row) => {
  currentRow = row
  scheduleForm.topic_id = row?.topic_id || null
  scheduleForm.defense_date = ''
  scheduleForm.defense_time_start = ''
  scheduleForm.defense_time_end = ''
  scheduleForm.location = ''
  scheduleForm.committee_members = ''
  scheduleForm.secretary_id = ''
  scheduleDialogVisible.value = true
  loadTopicOptions(defenseList.value.map(d => d.topic_id))
}

const submitSchedule = async () => {
  if (!scheduleFormRef.value) return
  try {
    await scheduleFormRef.value.validate()
    scheduleLoading.value = true
    const payload = { ...scheduleForm }
    // 清理空字符串字段，避免后端类型校验失败
    if (!payload.secretary_id) delete payload.secretary_id
    if (!payload.committee_members) delete payload.committee_members
    await request.post('/defenses', payload)
    ElMessage.success('安排成功')
    scheduleDialogVisible.value = false
    loadDefenseList()
  } catch (error) {
    if (error !== false) {
      console.error('安排失败:', error)
    }
  } finally {
    scheduleLoading.value = false
  }
}

const handleScoreDefense = (row) => {
  currentRow = row
  scoreForm.presentation_score = 7
  scoreForm.qa_score = 7
  scoreForm.thesis_quality_score = 7
  scoreForm.total_score = null
  scoreForm.opinion = ''
  scoreForm.grade = ''
  scoreForm.result = 'pass'
  scoreDialogVisible.value = true
}

const submitScore = async () => {
  if (!scoreFormRef.value) return
  try {
    await scoreFormRef.value.validate()
    scoreLoading.value = true
    await request.post(`/defenses/${currentRow.id}/score`, scoreForm)
    ElMessage.success('评分提交成功')
    scoreDialogVisible.value = false
    loadDefenseList()
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error)
    }
  } finally {
    scoreLoading.value = false
  }
}

const handleViewDefense = async (row) => {
  defenseDetailVisible.value = true
  try {
    const res = await request.get(`/defenses/${row.id}`)
    currentDefenseDetail.value = res
  } catch (error) {
    console.error('获取详情失败:', error)
  }
}

// 根据当前路由加载对应列表
const loadCurrentList = () => {
  if (isDefenseRoute.value) {
    loadDefenseList()
  } else {
    loadReviewList()
  }
}

// 路由切换时重新加载对应列表
watch(isDefenseRoute, loadCurrentList)

onMounted(() => {
  loadCurrentList()
})
</script>

<style scoped lang="scss">
.reviews-page {
  .search-card {
    margin-bottom: 16px;
  }

  .table-card {
    .table-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: 20px;
    }
  }

  .form-tip {
    margin-left: 10px;
    font-size: 12px;
    color: #909399;
  }

  .detail-content {
    white-space: pre-wrap;
    line-height: 1.6;
    color: #606266;
  }

  .text-muted {
    color: #909399;
  }

  .score-excellent {
    color: #67c23a;
    font-weight: 600;
  }

  .score-good {
    color: #409eff;
    font-weight: 600;
  }

  .score-pass {
    color: #e6a23c;
    font-weight: 600;
  }

  .score-fail {
    color: #f56c6c;
    font-weight: 600;
  }
}
</style>
