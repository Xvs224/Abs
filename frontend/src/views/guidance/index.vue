<template>
  <div class="guidance-page">
    <el-tabs v-model="activeTab" class="guidance-tabs">
      <!-- 指导计划标签页 -->
      <el-tab-pane label="指导计划" name="plans">
        <el-card class="plan-card" shadow="never">
          <div class="card-toolbar">
            <el-button type="primary" :icon="Plus" @click="handleAddPlan">新增计划</el-button>
            <el-button :icon="RefreshRight" @click="loadPlans">刷新</el-button>
          </div>
          <el-table :data="planList" v-loading="planLoading" stripe border>
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="title" label="计划标题" min-width="180" show-overflow-tooltip />
            <el-table-column prop="student_name" label="学生" width="100" />
            <el-table-column prop="teacher_name" label="指导教师" width="100" />
            <el-table-column prop="plan_date" label="计划时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.plan_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="planStatusTagType(row.status)" size="small">
                  {{ planStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleViewPlan(row)">查看</el-button>
                <el-button
                  v-if="row.status === 'pending'"
                  type="success"
                  link
                  size="small"
                  @click="handleAddRecordFromPlan(row)"
                >
                  添加记录
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 指导记录标签页 -->
      <el-tab-pane label="指导记录" name="records">
        <el-row :gutter="20">
          <!-- 左侧记录列表 -->
          <el-col :span="8">
            <el-card class="record-list-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <span>指导记录</span>
                  <el-button type="primary" :icon="Plus" size="small" @click="handleAddRecord">
                    新增
                  </el-button>
                </div>
              </template>
              <div class="record-list" v-loading="recordLoading">
                <div
                  v-for="record in recordList"
                  :key="record.id"
                  class="record-item"
                  :class="{ active: currentRecord?.id === record.id }"
                  @click="handleSelectRecord(record)"
                >
                  <div class="record-title">{{ record.title }}</div>
                  <div class="record-meta">
                    <span>{{ record.student_name || record.teacher_name }}</span>
                    <span>{{ formatDate(record.guidance_date) }}</span>
                  </div>
                  <div class="record-type">
                    <el-tag :type="recordTypeTagType(record.type)" size="small">
                      {{ recordTypeLabel(record.type) }}
                    </el-tag>
                  </div>
                </div>
                <el-empty v-if="!recordLoading && recordList.length === 0" description="暂无记录" />
              </div>
            </el-card>
          </el-col>

          <!-- 右侧记录详情 -->
          <el-col :span="16">
            <el-card class="record-detail-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <span>记录详情</span>
                </div>
              </template>
              <div class="record-detail" v-loading="detailLoading">
                <template v-if="currentRecord">
                  <div class="detail-header">
                    <h3 class="detail-title">{{ currentRecord.title }}</h3>
                    <div class="detail-meta">
                      <el-tag :type="recordTypeTagType(currentRecord.type)" size="small">
                        {{ recordTypeLabel(currentRecord.type) }}
                      </el-tag>
                      <span class="meta-item">
                        <el-icon><Calendar /></el-icon>
                        {{ formatTime(currentRecord.guidance_date) }}
                      </span>
                      <span class="meta-item">
                        <el-icon><User /></el-icon>
                        {{ currentRecord.student_name || '-' }}
                      </span>
                      <span class="meta-item">
                        <el-icon><UserFilled /></el-icon>
                        {{ currentRecord.teacher_name || '-' }}
                      </span>
                    </div>
                  </div>

                  <div class="detail-section">
                    <div class="section-title">指导内容</div>
                    <div class="section-content">{{ currentRecord.content || '-' }}</div>
                  </div>

                  <div class="detail-section">
                    <div class="section-title">指导建议</div>
                    <div class="section-content">{{ currentRecord.suggestion || '-' }}</div>
                  </div>

                  <div class="detail-section">
                    <div class="section-title">学生反馈</div>
                    <div class="section-content">{{ currentRecord.feedback || '-' }}</div>
                  </div>

                  <div class="detail-section" v-if="currentRecord.attachments?.length">
                    <div class="section-title">附件</div>
                    <div class="attachment-list">
                      <div v-for="(file, idx) in currentRecord.attachments" :key="idx" class="attachment-item">
                        <el-icon><Paperclip /></el-icon>
                        <span class="file-name">{{ file.name }}</span>
                        <el-button type="primary" link size="small">下载</el-button>
                      </div>
                    </div>
                  </div>

                  <!-- 时间线 -->
                  <div class="timeline-section" v-if="timelineList.length">
                    <div class="section-title">历史记录</div>
                    <el-timeline>
                      <el-timeline-item
                        v-for="(item, index) in timelineList"
                        :key="index"
                        :timestamp="formatTime(item.time)"
                        :type="timelineType(item.type)"
                        placement="top"
                      >
                        <div class="timeline-content">
                          <div class="timeline-title">{{ item.title }}</div>
                          <div class="timeline-desc" v-if="item.description">{{ item.description }}</div>
                        </div>
                      </el-timeline-item>
                    </el-timeline>
                  </div>
                </template>
                <el-empty v-else description="请选择一条记录查看详情" />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增计划对话框 -->
    <el-dialog v-model="planDialogVisible" title="新增指导计划" width="500px" :close-on-click-modal="false">
      <el-form ref="planFormRef" :model="planForm" :rules="planRules" label-width="100px">
        <el-form-item label="计划标题" prop="title">
          <el-input v-model="planForm.title" placeholder="请输入计划标题" />
        </el-form-item>
        <el-form-item label="学生" prop="student_id" v-if="userStore.role !== 'student'">
          <el-input v-model="planForm.student_id" placeholder="请输入学生学号" />
        </el-form-item>
        <el-form-item label="计划时间" prop="plan_date">
          <el-date-picker
            v-model="planForm.plan_date"
            type="datetime"
            placeholder="选择计划时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="指导方式" prop="type">
          <el-select v-model="planForm.type" placeholder="请选择指导方式" style="width: 100%">
            <el-option label="线下指导" value="offline" />
            <el-option label="线上指导" value="online" />
            <el-option label="小组讨论" value="group" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划内容" prop="content">
          <el-input v-model="planForm.content" type="textarea" :rows="3" placeholder="请输入计划内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="planDialogLoading" @click="submitPlan">确定</el-button>
      </template>
    </el-dialog>

    <!-- 新增记录对话框 -->
    <el-dialog v-model="recordDialogVisible" title="新增指导记录" width="600px" :close-on-click-modal="false">
      <el-form ref="recordFormRef" :model="recordForm" :rules="recordRules" label-width="100px">
        <el-form-item label="记录标题" prop="title">
          <el-input v-model="recordForm.title" placeholder="请输入记录标题" />
        </el-form-item>
        <el-form-item label="学生" prop="student_id" v-if="userStore.role !== 'student'">
          <el-input v-model="recordForm.student_id" placeholder="请输入学生学号" />
        </el-form-item>
        <el-form-item label="指导时间" prop="guidance_date">
          <el-date-picker
            v-model="recordForm.guidance_date"
            type="datetime"
            placeholder="选择指导时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="指导方式" prop="type">
          <el-select v-model="recordForm.type" placeholder="请选择指导方式" style="width: 100%">
            <el-option label="线下指导" value="offline" />
            <el-option label="线上指导" value="online" />
            <el-option label="小组讨论" value="group" />
          </el-select>
        </el-form-item>
        <el-form-item label="指导内容" prop="content">
          <el-input v-model="recordForm.content" type="textarea" :rows="3" placeholder="请输入指导内容" />
        </el-form-item>
        <el-form-item label="指导建议" prop="suggestion">
          <el-input v-model="recordForm.suggestion" type="textarea" :rows="2" placeholder="请输入指导建议" />
        </el-form-item>
        <el-form-item label="附件上传">
          <el-upload
            v-model:file-list="uploadFileList"
            action="#"
            multiple
            :auto-upload="false"
            :limit="5"
          >
            <el-button type="primary" :icon="Upload">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持上传多个文件，单个文件不超过 10MB</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="recordDialogLoading" @click="submitRecord">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, RefreshRight, Calendar, User, UserFilled, Paperclip, Upload } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import request from '@/utils/request'
import dayjs from 'dayjs'

const userStore = useUserStore()
const activeTab = ref('records')

// 计划相关
const planLoading = ref(false)
const planList = ref([])
const planDialogVisible = ref(false)
const planDialogLoading = ref(false)
const planFormRef = ref(null)

const planForm = reactive({
  title: '',
  student_id: '',
  plan_date: '',
  type: 'offline',
  content: ''
})

const planRules = {
  title: [{ required: true, message: '请输入计划标题', trigger: 'blur' }],
  plan_date: [{ required: true, message: '请选择计划时间', trigger: 'change' }],
  content: [{ required: true, message: '请输入计划内容', trigger: 'blur' }]
}

// 记录相关
const recordLoading = ref(false)
const detailLoading = ref(false)
const recordList = ref([])
const currentRecord = ref(null)
const recordDialogVisible = ref(false)
const recordDialogLoading = ref(false)
const recordFormRef = ref(null)
const uploadFileList = ref([])

const recordForm = reactive({
  title: '',
  student_id: '',
  guidance_date: '',
  type: 'offline',
  content: '',
  suggestion: ''
})

const recordRules = {
  title: [{ required: true, message: '请输入记录标题', trigger: 'blur' }],
  guidance_date: [{ required: true, message: '请选择指导时间', trigger: 'change' }],
  content: [{ required: true, message: '请输入指导内容', trigger: 'blur' }]
}

// 时间线数据
const timelineList = ref([])

const planStatusLabel = (status) => {
  const map = { pending: '待执行', completed: '已完成', cancelled: '已取消' }
  return map[status] || status
}

const planStatusTagType = (status) => {
  const map = { pending: 'warning', completed: 'success', cancelled: 'info' }
  return map[status] || 'info'
}

const recordTypeLabel = (type) => {
  const map = { offline: '线下指导', online: '线上指导', group: '小组讨论' }
  return map[type] || type
}

const recordTypeTagType = (type) => {
  const map = { offline: 'primary', online: 'success', group: 'warning' }
  return map[type] || 'info'
}

const timelineType = (type) => {
  const map = { create: 'primary', update: 'warning', complete: 'success' }
  return map[type] || 'primary'
}

const formatTime = (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'
const formatDate = (time) => time ? dayjs(time).format('MM-DD HH:mm') : '-'

const loadPlans = async () => {
  planLoading.value = true
  try {
    const res = await request.get('/guidance/plans')
    planList.value = res.items || res.data || []
  } catch (error) {
    console.error('加载指导计划失败:', error)
  } finally {
    planLoading.value = false
  }
}

const loadRecords = async () => {
  recordLoading.value = true
  try {
    const res = await request.get('/guidance/records')
    recordList.value = res.items || res.data || []
  } catch (error) {
    console.error('加载指导记录失败:', error)
  } finally {
    recordLoading.value = false
  }
}

const handleSelectRecord = async (record) => {
  currentRecord.value = record
  detailLoading.value = true
  try {
    const res = await request.get(`/guidance/records/${record.id}`)
    currentRecord.value = res
    // 模拟时间线数据
    timelineList.value = [
      { type: 'create', title: '创建指导记录', time: res.created_at, description: '' },
      { type: 'complete', title: '指导完成', time: res.guidance_date, description: res.content }
    ]
  } catch (error) {
    console.error('获取记录详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}

const handleAddPlan = () => {
  planForm.title = ''
  planForm.student_id = ''
  planForm.plan_date = ''
  planForm.type = 'offline'
  planForm.content = ''
  planFormRef.value?.resetFields()
  planDialogVisible.value = true
}

const submitPlan = async () => {
  if (!planFormRef.value) return
  try {
    await planFormRef.value.validate()
    planDialogLoading.value = true
    await request.post('/guidance/plans', planForm)
    ElMessage.success('创建成功')
    planDialogVisible.value = false
    loadPlans()
  } catch (error) {
    if (error !== false) {
      console.error('创建失败:', error)
    }
  } finally {
    planDialogLoading.value = false
  }
}

const handleViewPlan = (row) => {
  ElMessage.info(`查看计划: ${row.title}`)
}

const handleAddRecordFromPlan = (row) => {
  recordForm.title = row.title
  recordForm.student_id = row.student_id
  recordForm.guidance_date = row.plan_date
  recordForm.type = row.type
  recordDialogVisible.value = true
}

const handleAddRecord = () => {
  recordForm.title = ''
  recordForm.student_id = ''
  recordForm.guidance_date = ''
  recordForm.type = 'offline'
  recordForm.content = ''
  recordForm.suggestion = ''
  uploadFileList.value = []
  recordFormRef.value?.resetFields()
  recordDialogVisible.value = true
}

const submitRecord = async () => {
  if (!recordFormRef.value) return
  try {
    await recordFormRef.value.validate()
    recordDialogLoading.value = true
    await request.post('/guidance/records', recordForm)
    ElMessage.success('保存成功')
    recordDialogVisible.value = false
    loadRecords()
  } catch (error) {
    if (error !== false) {
      console.error('保存失败:', error)
    }
  } finally {
    recordDialogLoading.value = false
  }
}

onMounted(() => {
  loadPlans()
  loadRecords()
})
</script>

<style scoped lang="scss">
.guidance-page {
  .guidance-tabs {
    :deep(.el-tabs__content) {
      padding-top: 0;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-toolbar {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
  }

  .plan-card {
    margin-bottom: 16px;
  }

  .record-list-card {
    height: calc(100vh - 200px);
    min-height: 500px;

    .record-list {
      height: calc(100% - 20px);
      overflow-y: auto;

      .record-item {
        padding: 12px;
        border-bottom: 1px solid #ebeef5;
        cursor: pointer;
        transition: background 0.2s;

        &:hover {
          background: #f5f7fa;
        }

        &.active {
          background: #ecf5ff;
          border-left: 3px solid #409eff;
        }

        .record-title {
          font-size: 14px;
          font-weight: 500;
          color: #303133;
          margin-bottom: 6px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .record-meta {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          color: #909399;
          margin-bottom: 6px;
        }

        .record-type {
          display: flex;
        }
      }
    }
  }

  .record-detail-card {
    min-height: 500px;

    .record-detail {
      .detail-header {
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid #ebeef5;

        .detail-title {
          font-size: 18px;
          font-weight: 600;
          color: #303133;
          margin-bottom: 12px;
        }

        .detail-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 16px;
          align-items: center;

          .meta-item {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 13px;
            color: #606266;

            .el-icon {
              font-size: 14px;
            }
          }
        }
      }

      .detail-section {
        margin-bottom: 20px;

        .section-title {
          font-size: 14px;
          font-weight: 600;
          color: #303133;
          margin-bottom: 8px;
          padding-left: 8px;
          border-left: 3px solid #409eff;
        }

        .section-content {
          background: #f5f7fa;
          padding: 12px 16px;
          border-radius: 4px;
          line-height: 1.8;
          color: #606266;
          white-space: pre-wrap;
        }
      }

      .attachment-list {
        .attachment-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: #f5f7fa;
          border-radius: 4px;
          margin-bottom: 8px;

          .file-name {
            flex: 1;
            font-size: 13px;
            color: #606266;
          }
        }
      }

      .timeline-section {
        margin-top: 24px;

        .timeline-content {
          .timeline-title {
            font-size: 13px;
            font-weight: 500;
            color: #303133;
          }

          .timeline-desc {
            font-size: 12px;
            color: #909399;
            margin-top: 4px;
          }
        }
      }
    }
  }
}
</style>
