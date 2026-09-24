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
            <el-table-column label="操作" width="280" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleViewReview(row)">查看</el-button>
                <el-button
                  v-if="row.status === 'pending' && canManage"
                  type="success"
                  link
                  size="small"
                  @click="handleAssignReviewer(row)"
                >
                  分配
                </el-button>
                <el-button
                  v-if="row.status === 'reviewing' && isTeacher"
                  type="warning"
                  link
                  size="small"
                  @click="handleSubmitReview(row)"
                >
                  提交评阅
                </el-button>
                <el-button
                  v-if="canManage && (isAdmin || row.status === 'completed')"
                  type="warning"
                  link
                  size="small"
                  @click="handleEditReview(row)"
                >
                  修改
                </el-button>
                <el-button
                  v-if="canManage && (isAdmin || row.status !== 'completed')"
                  type="danger"
                  link
                  size="small"
                  @click="handleDeleteReview(row)"
                >
                  删除
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
            <el-table-column prop="committee_member_names" label="答辩委员会" width="150" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.committee_member_names || '未安排' }}
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
            <el-table-column label="评阅结果" width="110" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.review_result" :type="row.review_passed ? 'success' : 'danger'" size="small">
                  {{ row.review_result_text }}
                </el-tag>
                <span v-else class="text-muted">未评阅</span>
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
            <el-table-column label="操作" width="280" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleViewDefense(row)">查看</el-button>
                <el-tooltip
                  v-if="row.status === 'pending' && canManage"
                  :content="row.review_passed ? '' : (row.review_result ? `评阅结果为「${row.review_result_text}」，需评阅通过后才可安排答辩` : '该选题尚未完成论文评阅，无法安排答辩')"
                  placement="top"
                  :disabled="row.review_passed"
                >
                  <el-button
                    type="success"
                    link
                    size="small"
                    :disabled="!row.review_passed"
                    @click="handleScheduleDefense(row)"
                  >
                    安排
                  </el-button>
                </el-tooltip>
                <el-button
                  v-if="row.status === 'scheduled' && isTeacher"
                  type="warning"
                  link
                  size="small"
                  @click="handleScoreDefense(row)"
                >
                  评分
                </el-button>
                <el-button
                  v-if="canManage && (isAdmin || row.status === 'completed')"
                  type="warning"
                  link
                  size="small"
                  @click="handleEditDefense(row)"
                >
                  修改
                </el-button>
                <el-button
                  v-if="canManage && (isAdmin || row.status !== 'completed')"
                  type="danger"
                  link
                  size="small"
                  @click="handleDeleteDefense(row)"
                >
                  删除
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
          <el-select
            v-model="assignForm.reviewer_id"
            v-loading="teacherLoading"
            placeholder="请选择评阅教师"
            filterable
            style="width: 100%"
          >
            <el-option v-for="t in teacherOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
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
    <el-dialog v-model="reviewSubmitDialogVisible" :title="editingReviewId ? '修改评阅意见' : '提交评阅意见'" width="600px" :close-on-click-modal="false">
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
        <el-form-item label="评阅意见书">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="handleReviewFileChange"
            :on-remove="handleReviewFileRemove"
            :file-list="reviewFileList"
            accept=".doc,.docx,.pdf"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">将评阅意见书拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 doc、docx、pdf 格式，提交后自动归入归档材料</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewSubmitDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewSubmitLoading" v-if="canReview" @click="submitReviewForm">
          {{ editingReviewId ? '保存修改' : '提交评阅' }}
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
            @change="validateDefenseTime"
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
          <el-select
            v-model="scheduleForm.location"
            v-loading="teacherLoading"
            placeholder="请选择或输入答辩地点"
            filterable
            allow-create
            default-first-option
            style="width: 100%"
          >
            <el-option v-for="loc in locationOptions" :key="loc" :label="loc" :value="loc" />
          </el-select>
        </el-form-item>
        <el-form-item label="答辩委员会" prop="committee_members">
          <el-select
            v-model="scheduleForm.committee_members"
            v-loading="teacherLoading"
            placeholder="请选择答辩委员会成员"
            multiple
            collapse-tags
            collapse-tags-tooltip
            filterable
            style="width: 100%"
          >
            <el-option v-for="t in teacherOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="答辩秘书" prop="secretary_id">
          <el-select
            v-model="scheduleForm.secretary_id"
            v-loading="teacherLoading"
            placeholder="请选择答辩秘书"
            filterable
            clearable
            style="width: 100%"
          >
            <el-option v-for="t in teacherOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="scheduleLoading" @click="submitSchedule">确认安排</el-button>
      </template>
    </el-dialog>

    <!-- 答辩评分对话框 -->
    <el-dialog v-model="scoreDialogVisible" :title="editingDefenseId ? '修改答辩评分' : '答辩评分'" width="600px" :close-on-click-modal="false">
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
        <el-form-item label="答辩记录">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="handleDefenseFileChange"
            :on-remove="handleDefenseFileRemove"
            :file-list="defenseFileList"
            accept=".doc,.docx,.pdf"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">将答辩记录拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 doc、docx、pdf 格式，提交后自动归入归档材料</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scoreDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="scoreLoading" v-if="canManage" @click="submitScore">
          {{ editingDefenseId ? '保存修改' : '提交评分' }}
        </el-button>
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
        <el-descriptions-item label="答辩委员会">{{ currentDefenseDetail.committee_member_names || '未安排' }}</el-descriptions-item>
        <el-descriptions-item label="答辩秘书">{{ currentDefenseDetail.secretary_name || '未安排' }}</el-descriptions-item>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, RefreshRight, UploadFilled } from '@element-plus/icons-vue'
import request from '@/utils/request'
import dayjs from 'dayjs'
import { getTopicList } from '@/api/topic'
import { getUserList } from '@/api/user'
import {
  getReviewList, submitReview, updateReview, deleteReview,
  getDefenseList, updateDefense, scoreDefense, deleteDefense
} from '@/api/review'


const userStore = useUserStore()
const isTeacher = computed(() => userStore.userInfo?.role === 'teacher')
const isAdmin = computed(() => userStore.userInfo?.role === 'admin')
const canManage = computed(() => isTeacher.value || isAdmin.value)
// 当前用户是否可提交/修改评阅：管理员或该评阅的指定评阅教师
const canReview = computed(() => {
  if (isAdmin.value) return true
  if (!currentRow) return isTeacher.value
  return currentRow.reviewer_id === userStore.userInfo?.id
})

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
const editingReviewId = ref(null)

const assignForm = reactive({ topic_id: null, reviewer_id: null, deadline: '' })
const assignRules = {
  topic_id: [{ required: true, message: '请选择论文题目', trigger: 'change' }],
  reviewer_id: [{ required: true, message: '请选择评阅教师', trigger: 'change' }]
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
// 开始时间变化时重新校验结束时间
const validateDefenseTime = () => {
  if (scheduleFormRef.value && scheduleForm.defense_time_end) {
    scheduleFormRef.value.validateField('defense_time_end')
  }
}
const scoreDialogVisible = ref(false)
const scoreLoading = ref(false)
const scoreFormRef = ref(null)
const defenseDetailVisible = ref(false)
const currentDefenseDetail = ref(null)
const editingDefenseId = ref(null)

const scheduleForm = reactive({
  topic_id: null,
  defense_date: '',
  defense_time_start: '',
  defense_time_end: '',
  location: '',
  committee_members: [],
  secretary_id: null
})
const scheduleRules = {
  topic_id: [{ required: true, message: '请选择论文题目', trigger: 'change' }],
  defense_date: [{ required: true, message: '请选择答辩日期', trigger: 'change' }],
  defense_time_start: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  defense_time_end: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    {
      validator: (rule, value, callback) => {
        if (value && scheduleForm.defense_time_start && value <= scheduleForm.defense_time_start) {
          callback(new Error('结束时间必须晚于开始时间'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  location: [{ required: true, message: '请输入答辩地点', trigger: 'blur' }]
}

const topicOptions = ref([])
const topicLoading = ref(false)

// 教师列表（答辩委员会、秘书下拉）
const teacherOptions = ref([])
const teacherLoading = ref(false)
// 常见答辩地点
const locationOptions = ref([
  '教学楼A101', '教学楼A102', '教学楼A201', '教学楼A202',
  '教学楼B101', '教学楼B102', '教学楼B201', '教学楼B202',
  '行政楼会议室', '学术报告厅', '线上(腾讯会议)', '线上(钉钉)'
])

const loadTeachers = async () => {
  if (teacherOptions.value.length > 0) return
  teacherLoading.value = true
  try {
    const res = await getUserList({ role: 'teacher', page: 1, page_size: 100 })
    // 响应拦截器已返回 res.data，结构为 { items, total, page, page_size }
    const items = res?.items || res?.list || []
    teacherOptions.value = items.map(u => ({
      value: u.id,
      label: u.real_name || u.username
    }))
  } catch (e) {
    console.error('加载教师列表失败:', e)
  } finally {
    teacherLoading.value = false
  }
}

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

// 评阅意见书上传
const reviewFileList = ref([])
const reviewUploadedFile = ref(null)
// 答辩记录上传
const defenseFileList = ref([])
const defenseUploadedFile = ref(null)

const handleReviewFileChange = (file) => {
  const ext = (file.name || '').substring((file.name || '').lastIndexOf('.')).toLowerCase()
  if (!['.doc', '.docx', '.pdf'].includes(ext)) {
    ElMessage.error('仅支持 doc、docx、pdf 格式')
    reviewFileList.value = []
    return
  }
  reviewFileList.value = [file]
}
const handleReviewFileRemove = () => {
  reviewFileList.value = []
  reviewUploadedFile.value = null
}

const handleDefenseFileChange = (file) => {
  const ext = (file.name || '').substring((file.name || '').lastIndexOf('.')).toLowerCase()
  if (!['.doc', '.docx', '.pdf'].includes(ext)) {
    ElMessage.error('仅支持 doc、docx、pdf 格式')
    defenseFileList.value = []
    return
  }
  defenseFileList.value = [file]
}
const handleDefenseFileRemove = () => {
  defenseFileList.value = []
  defenseUploadedFile.value = null
}

const uploadReviewFile = async () => {
  if (!reviewFileList.value.length) return null
  const rawFile = reviewFileList.value[0].raw
  if (!rawFile) return null  // 已有文件引用，无需重新上传
  const formData = new FormData()
  formData.append('file', rawFile)
  const res = await request.post('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params: { module: 'review' }
  })
  reviewUploadedFile.value = { id: res.id, file_path: res.file_path, file_name: res.original_name }
  return reviewUploadedFile.value
}

const uploadDefenseFile = async () => {
  if (!defenseFileList.value.length) return null
  const rawFile = defenseFileList.value[0].raw
  if (!rawFile) return null  // 已有文件引用，无需重新上传
  const formData = new FormData()
  formData.append('file', rawFile)
  const res = await request.post('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params: { module: 'defense' }
  })
  defenseUploadedFile.value = { id: res.id, file_path: res.file_path, file_name: res.original_name }
  return defenseUploadedFile.value
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
  assignForm.reviewer_id = null
  assignForm.deadline = ''
  assignDialogVisible.value = true
  loadTopicOptions(reviewList.value.map(r => r.topic_id))
  loadTeachers()
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
      reviewer_id: assignForm.reviewer_id,
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
  editingReviewId.value = null
  reviewSubmitForm.total_score = null
  reviewSubmitForm.opinion = ''
  reviewSubmitForm.topic_score = 7
  reviewSubmitForm.content_score = 7
  reviewSubmitForm.method_score = 7
  reviewSubmitForm.innovation_score = 7
  reviewSubmitForm.format_score = 7
  reviewSubmitForm.suggestions = ''
  reviewSubmitForm.result = 'pass'
  reviewFileList.value = []
  reviewUploadedFile.value = null
  reviewSubmitDialogVisible.value = true
}

const handleEditReview = async (row) => {
  currentRow = row
  editingReviewId.value = row.id
  try {
    const res = await request.get(`/reviews/${row.id}`)
    const detail = res.data || res
    // 后端存储 0-100 分制，前端 el-rate 使用 0-10 分制，需要除以 10
    reviewSubmitForm.total_score = detail.total_score ?? null
    reviewSubmitForm.opinion = detail.opinion || ''
    reviewSubmitForm.topic_score = Math.round((detail.topic_score || 0) / 10)
    reviewSubmitForm.content_score = Math.round((detail.content_score || 0) / 10)
    reviewSubmitForm.method_score = Math.round((detail.method_score || 0) / 10)
    reviewSubmitForm.innovation_score = Math.round((detail.innovation_score || 0) / 10)
    reviewSubmitForm.format_score = Math.round((detail.format_score || 0) / 10)
    reviewSubmitForm.suggestions = detail.suggestions || ''
    reviewSubmitForm.result = detail.result || 'pass'
    reviewFileList.value = []
    reviewUploadedFile.value = null
    if (detail.review_file_name) {
      reviewFileList.value = [{ name: detail.review_file_name, url: detail.review_file_path }]
    }
    reviewSubmitDialogVisible.value = true
  } catch (error) {
    console.error('获取评阅详情失败:', error)
  }
}

const handleDeleteReview = (row) => {
  ElMessageBox.confirm(`确定要删除该评阅记录吗？删除后不可恢复。`, '删除确认', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteReview(row.id)
      ElMessage.success('删除成功')
      loadReviewList()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }).catch(() => {})
}

const submitReviewForm = async () => {
  if (!reviewSubmitFormRef.value) return
  try {
    await reviewSubmitFormRef.value.validate()
    reviewSubmitLoading.value = true
    // 上传评阅意见书
    const reviewFile = await uploadReviewFile()
    // 将 0-10 评分转换为 0-100 分制
    const payload = {
      ...reviewSubmitForm,
      topic_score: reviewSubmitForm.topic_score * 10,
      content_score: reviewSubmitForm.content_score * 10,
      method_score: reviewSubmitForm.method_score * 10,
      innovation_score: reviewSubmitForm.innovation_score * 10,
      format_score: reviewSubmitForm.format_score * 10
    }
    if (reviewFile) {
      payload.review_file_id = reviewFile.id
      payload.review_file_path = reviewFile.file_path
      payload.review_file_name = reviewFile.file_name
    }
    if (editingReviewId.value) {
      await updateReview(editingReviewId.value, payload)
      ElMessage.success('评阅修改成功')
    } else {
      await request.post(`/reviews/${currentRow.id}/submit`, payload)
      ElMessage.success('评阅提交成功')
    }
    reviewSubmitDialogVisible.value = false
    editingReviewId.value = null
    reviewFileList.value = []
    reviewUploadedFile.value = null
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
  scheduleForm.committee_members = []
  scheduleForm.secretary_id = null
  scheduleDialogVisible.value = true
  loadTopicOptions(defenseList.value.map(d => d.topic_id))
  loadTeachers()
}

const submitSchedule = async () => {
  if (!scheduleFormRef.value) return
  try {
    await scheduleFormRef.value.validate()
    scheduleLoading.value = true
    const payload = { ...scheduleForm }
    // 委员会成员数组转逗号分隔字符串
    if (Array.isArray(payload.committee_members)) {
      payload.committee_members = payload.committee_members.length
        ? payload.committee_members.join(',')
        : ''
    }
    // 清理空值字段，避免后端类型校验失败
    if (!payload.secretary_id) delete payload.secretary_id
    if (!payload.committee_members) delete payload.committee_members
    // 若已有答辩记录（如重新答辩申请），则更新；否则新建
    if (currentRow && currentRow.id) {
      await request.put(`/defenses/${currentRow.id}`, { ...payload, status: 'scheduled' })
    } else {
      await request.post('/defenses', payload)
    }
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
  editingDefenseId.value = null
  scoreForm.presentation_score = 7
  scoreForm.qa_score = 7
  scoreForm.thesis_quality_score = 7
  scoreForm.total_score = null
  scoreForm.opinion = ''
  scoreForm.grade = ''
  scoreForm.result = 'pass'
  defenseFileList.value = []
  defenseUploadedFile.value = null
  scoreDialogVisible.value = true
}

const handleEditDefense = async (row) => {
  currentRow = row
  editingDefenseId.value = row.id
  try {
    const res = await request.get(`/defenses/${row.id}`)
    const detail = res.data || res
    // 后端存储 0-100 分制，前端 el-rate 使用 0-10 分制，需要除以 10
    scoreForm.presentation_score = Math.round((detail.presentation_score || 0) / 10)
    scoreForm.qa_score = Math.round((detail.qa_score || 0) / 10)
    scoreForm.thesis_quality_score = Math.round((detail.thesis_quality_score || 0) / 10)
    scoreForm.total_score = detail.total_score ?? null
    scoreForm.opinion = detail.opinion || ''
    scoreForm.grade = detail.grade || ''
    scoreForm.result = detail.result || 'pass'
    defenseFileList.value = []
    defenseUploadedFile.value = null
    if (detail.defense_file_name) {
      defenseFileList.value = [{ name: detail.defense_file_name, url: detail.defense_file_path }]
    }
    scoreDialogVisible.value = true
  } catch (error) {
    console.error('获取答辩详情失败:', error)
  }
}

const handleDeleteDefense = (row) => {
  ElMessageBox.confirm(`确定要删除该答辩记录吗？删除后不可恢复。`, '删除确认', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteDefense(row.id)
      ElMessage.success('删除成功')
      loadDefenseList()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }).catch(() => {})
}

const submitScore = async () => {
  if (!scoreFormRef.value) return
  try {
    await scoreFormRef.value.validate()
    scoreLoading.value = true
    // 上传答辩记录
    const defenseFile = await uploadDefenseFile()
    // 将 0-10 评分转换为 0-100 分制
    const payload = {
      ...scoreForm,
      presentation_score: scoreForm.presentation_score * 10,
      qa_score: scoreForm.qa_score * 10,
      thesis_quality_score: scoreForm.thesis_quality_score * 10
    }
    if (defenseFile) {
      payload.defense_file_id = defenseFile.id
      payload.defense_file_path = defenseFile.file_path
      payload.defense_file_name = defenseFile.file_name
    }
    if (editingDefenseId.value) {
      await scoreDefense(editingDefenseId.value, payload)
      ElMessage.success('答辩评分修改成功')
    } else {
      await request.post(`/defenses/${currentRow.id}/score`, payload)
      ElMessage.success('评分提交成功')
    }
    scoreDialogVisible.value = false
    editingDefenseId.value = null
    defenseFileList.value = []
    defenseUploadedFile.value = null
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
