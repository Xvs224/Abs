<template>
  <div class="reviews-page">
    <el-tabs v-model="activeTab" class="review-tabs">
      <!-- 评阅管理 -->
      <el-tab-pane label="评阅管理" name="reviews">
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
            <el-table-column prop="thesis_title" label="论文题目" min-width="200" show-overflow-tooltip />
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
            <el-table-column prop="score" label="评阅成绩" width="100" align="center">
              <template #default="{ row }">
                <span v-if="row.score !== undefined && row.score !== null" :class="scoreClass(row.score)">
                  {{ row.score }}
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="分配时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
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
      </el-tab-pane>

      <!-- 答辩管理 -->
      <el-tab-pane label="答辩管理" name="defenses">
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
            <el-table-column prop="thesis_title" label="论文题目" min-width="180" show-overflow-tooltip />
            <el-table-column prop="student_name" label="学生" width="100" />
            <el-table-column prop="committee" label="答辩委员会" width="150" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.committee || '未安排' }}
              </template>
            </el-table-column>
            <el-table-column prop="defense_time" label="答辩时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.defense_time) }}
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
            <el-table-column prop="score" label="答辩成绩" width="100" align="center">
              <template #default="{ row }">
                <span v-if="row.score !== undefined && row.score !== null" :class="scoreClass(row.score)">
                  {{ row.score }}
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
      </el-tab-pane>
    </el-tabs>

    <!-- 分配评阅对话框 -->
    <el-dialog v-model="assignDialogVisible" title="分配评阅教师" width="500px" :close-on-click-modal="false">
      <el-form ref="assignFormRef" :model="assignForm" :rules="assignRules" label-width="100px">
        <el-form-item label="评阅教师" prop="reviewer_id">
          <el-input v-model="assignForm.reviewer_id" placeholder="请输入评阅教师工号" />
        </el-form-item>
        <el-form-item label="截止日期" prop="deadline">
          <el-date-picker
            v-model="assignForm.deadline"
            type="date"
            placeholder="选择评阅截止日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="assignForm.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="assignLoading" @click="submitAssign">确认分配</el-button>
      </template>
    </el-dialog>

    <!-- 提交评阅对话框 -->
    <el-dialog v-model="reviewSubmitDialogVisible" title="提交评阅意见" width="600px" :close-on-click-modal="false">
      <el-form ref="reviewSubmitFormRef" :model="reviewSubmitForm" :rules="reviewSubmitRules" label-width="100px">
        <el-form-item label="评阅成绩" prop="score">
          <el-input-number v-model="reviewSubmitForm.score" :min="0" :max="100" :precision="1" />
          <span class="form-tip">满分 100 分</span>
        </el-form-item>
        <el-form-item label="总体评价" prop="overall_comment">
          <el-input
            v-model="reviewSubmitForm.overall_comment"
            type="textarea"
            :rows="2"
            placeholder="请输入总体评价"
          />
        </el-form-item>
        <el-form-item label="选题质量" prop="topic_score">
          <el-rate v-model="reviewSubmitForm.topic_score" :max="5" show-text />
        </el-form-item>
        <el-form-item label="论文质量" prop="quality_score">
          <el-rate v-model="reviewSubmitForm.quality_score" :max="5" show-text />
        </el-form-item>
        <el-form-item label="创新性" prop="innovation_score">
          <el-rate v-model="reviewSubmitForm.innovation_score" :max="5" show-text />
        </el-form-item>
        <el-form-item label="详细意见" prop="comment">
          <el-input
            v-model="reviewSubmitForm.comment"
            type="textarea"
            :rows="4"
            placeholder="请输入详细评阅意见"
          />
        </el-form-item>
        <el-form-item label="结论" prop="conclusion">
          <el-radio-group v-model="reviewSubmitForm.conclusion">
            <el-radio value="pass">同意答辩</el-radio>
            <el-radio value="revision">修改后答辩</el-radio>
            <el-radio value="fail">不同意答辩</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewSubmitDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewSubmitLoading" @click="submitReviewForm">
          提交评阅
        </el-button>
      </template>
    </el-dialog>

    <!-- 安排答辩对话框 -->
    <el-dialog v-model="scheduleDialogVisible" title="安排答辩" width="500px" :close-on-click-modal="false">
      <el-form ref="scheduleFormRef" :model="scheduleForm" :rules="scheduleRules" label-width="100px">
        <el-form-item label="答辩时间" prop="defense_time">
          <el-date-picker
            v-model="scheduleForm.defense_time"
            type="datetime"
            placeholder="选择答辩时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="答辩地点" prop="location">
          <el-input v-model="scheduleForm.location" placeholder="请输入答辩地点" />
        </el-form-item>
        <el-form-item label="答辩委员会" prop="committee">
          <el-input v-model="scheduleForm.committee" placeholder="请输入答辩委员会成员" />
        </el-form-item>
        <el-form-item label="答辩秘书" prop="secretary">
          <el-input v-model="scheduleForm.secretary" placeholder="请输入答辩秘书" />
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
        <el-form-item label="报告内容" prop="content_score">
          <el-rate v-model="scoreForm.content_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="答辩表现" prop="defense_score">
          <el-rate v-model="scoreForm.defense_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="综合能力" prop="ability_score">
          <el-rate v-model="scoreForm.ability_score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="答辩成绩" prop="score">
          <el-input-number v-model="scoreForm.score" :min="0" :max="100" :precision="1" />
          <span class="form-tip">满分 100 分</span>
        </el-form-item>
        <el-form-item label="答辩评语" prop="comment">
          <el-input
            v-model="scoreForm.comment"
            type="textarea"
            :rows="4"
            placeholder="请输入答辩评语"
          />
        </el-form-item>
        <el-form-item label="答辩结果" prop="result">
          <el-radio-group v-model="scoreForm.result">
            <el-radio value="excellent">优秀</el-radio>
            <el-radio value="good">良好</el-radio>
            <el-radio value="pass">合格</el-radio>
            <el-radio value="fail">不合格</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scoreDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="scoreLoading" @click="submitScore">提交评分</el-button>
      </template>
    </el-dialog>

    <!-- 评阅详情对话框 -->
    <el-dialog v-model="reviewDetailVisible" title="评阅详情" width="600px">
      <el-descriptions :column="2" border v-if="currentReviewDetail">
        <el-descriptions-item label="论文题目" :span="2">{{ currentReviewDetail.thesis_title }}</el-descriptions-item>
        <el-descriptions-item label="学生">{{ currentReviewDetail.student_name }}</el-descriptions-item>
        <el-descriptions-item label="评阅教师">{{ currentReviewDetail.reviewer_name || '未分配' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="reviewStatusTagType(currentReviewDetail.status)" size="small">
            {{ reviewStatusLabel(currentReviewDetail.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="评阅成绩">
          <span v-if="currentReviewDetail.score !== undefined" :class="scoreClass(currentReviewDetail.score)">
            {{ currentReviewDetail.score }}
          </span>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="评阅意见" :span="2">
          <div class="detail-content">{{ currentReviewDetail.comment || '暂无' }}</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 答辩详情对话框 -->
    <el-dialog v-model="defenseDetailVisible" title="答辩详情" width="600px">
      <el-descriptions :column="2" border v-if="currentDefenseDetail">
        <el-descriptions-item label="论文题目" :span="2">{{ currentDefenseDetail.thesis_title }}</el-descriptions-item>
        <el-descriptions-item label="学生">{{ currentDefenseDetail.student_name }}</el-descriptions-item>
        <el-descriptions-item label="答辩委员会">{{ currentDefenseDetail.committee || '未安排' }}</el-descriptions-item>
        <el-descriptions-item label="答辩时间">{{ formatTime(currentDefenseDetail.defense_time) }}</el-descriptions-item>
        <el-descriptions-item label="答辩地点">{{ currentDefenseDetail.location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="defenseStatusTagType(currentDefenseDetail.status)" size="small">
            {{ defenseStatusLabel(currentDefenseDetail.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="答辩成绩">
          <span v-if="currentDefenseDetail.score !== undefined" :class="scoreClass(currentDefenseDetail.score)">
            {{ currentDefenseDetail.score }}
          </span>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="答辩评语" :span="2">
          <div class="detail-content">{{ currentDefenseDetail.comment || '暂无' }}</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus, RefreshRight } from '@element-plus/icons-vue'
import request from '@/utils/request'
import dayjs from 'dayjs'

const activeTab = ref('reviews')

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

const assignForm = reactive({ reviewer_id: '', deadline: '', remark: '' })
const assignRules = {
  reviewer_id: [{ required: true, message: '请输入评阅教师工号', trigger: 'blur' }]
}

const reviewSubmitForm = reactive({
  score: null,
  overall_comment: '',
  topic_score: 3,
  quality_score: 3,
  innovation_score: 3,
  comment: '',
  conclusion: 'pass'
})
const reviewSubmitRules = {
  score: [{ required: true, message: '请输入评阅成绩', trigger: 'blur' }],
  comment: [{ required: true, message: '请输入评阅意见', trigger: 'blur' }]
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

const scheduleForm = reactive({ defense_time: '', location: '', committee: '', secretary: '' })
const scheduleRules = {
  defense_time: [{ required: true, message: '请选择答辩时间', trigger: 'change' }],
  location: [{ required: true, message: '请输入答辩地点', trigger: 'blur' }]
}

const scoreForm = reactive({
  content_score: 7,
  defense_score: 7,
  ability_score: 7,
  score: null,
  comment: '',
  result: 'pass'
})
const scoreRules = {
  score: [{ required: true, message: '请输入答辩成绩', trigger: 'blur' }],
  comment: [{ required: true, message: '请输入答辩评语', trigger: 'blur' }]
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
  assignForm.reviewer_id = ''
  assignForm.deadline = ''
  assignForm.remark = ''
  assignDialogVisible.value = true
}

const submitAssign = async () => {
  if (!assignFormRef.value) return
  try {
    await assignFormRef.value.validate()
    assignLoading.value = true
    await request.post(`/reviews/${currentRow?.id || ''}/assign`, assignForm)
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
  reviewSubmitForm.score = null
  reviewSubmitForm.overall_comment = ''
  reviewSubmitForm.topic_score = 3
  reviewSubmitForm.quality_score = 3
  reviewSubmitForm.innovation_score = 3
  reviewSubmitForm.comment = ''
  reviewSubmitForm.conclusion = 'pass'
  reviewSubmitDialogVisible.value = true
}

const submitReviewForm = async () => {
  if (!reviewSubmitFormRef.value) return
  try {
    await reviewSubmitFormRef.value.validate()
    reviewSubmitLoading.value = true
    await request.post(`/reviews/${currentRow.id}/submit`, reviewSubmitForm)
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
  scheduleForm.defense_time = ''
  scheduleForm.location = ''
  scheduleForm.committee = ''
  scheduleForm.secretary = ''
  scheduleDialogVisible.value = true
}

const submitSchedule = async () => {
  if (!scheduleFormRef.value) return
  try {
    await scheduleFormRef.value.validate()
    scheduleLoading.value = true
    await request.post(`/defenses/${currentRow?.id || ''}/schedule`, scheduleForm)
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
  scoreForm.content_score = 7
  scoreForm.defense_score = 7
  scoreForm.ability_score = 7
  scoreForm.score = null
  scoreForm.comment = ''
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

onMounted(() => {
  loadReviewList()
  loadDefenseList()
})
</script>

<style scoped lang="scss">
.reviews-page {
  .review-tabs {
    :deep(.el-tabs__content) {
      padding-top: 0;
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
