<template>
  <div class="teacher-guidance">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-select v-model="filterTopic" placeholder="按选题筛选" clearable style="width: 280px" @change="load">
          <el-option v-for="t in topics" :key="t.id" :label="`${t.title}（${t.student_name || '未分配学生'}）`" :value="t.id" />
        </el-select>
        <el-button type="primary" @click="showCreate = true">
          <el-icon><Plus /></el-icon> 发起指导
        </el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="list-card">
      <el-timeline v-if="list.length" class="timeline">
        <el-timeline-item
          v-for="item in list"
          :key="item.id"
          :timestamp="fmtTime(item.guidance_time || item.create_time)"
          placement="top"
          :type="item.initiator === 'teacher' ? 'primary' : 'success'"
        >
          <div class="guidance-item">
            <div class="item-header">
              <span class="guidance-title">{{ item.title || '指导记录' }}</span>
              <div class="header-right">
                <el-tag size="small" :type="statusTag(item.status)" effect="light">{{ statusLabel(item.status) }}</el-tag>
                <el-button link type="danger" size="small" @click="remove(item)">删除</el-button>
              </div>
            </div>
            <div class="item-meta">
              <el-tag size="small" type="info" effect="plain">{{ typeLabel(item.guidance_type) }}</el-tag>
              <span class="meta-text">{{ item.topic_title }}</span>
              <span class="meta-text">{{ item.student_name }}</span>
              <span class="meta-text">{{ item.initiator === 'teacher' ? '教师指导' : '学生提问' }}</span>
            </div>
            <div class="item-content">{{ item.content }}</div>
            <!-- 学生回复（教师发起指导后学生回复） -->
            <div v-if="item.student_response" class="item-response">
              <div class="response-label">学生回复：</div>
              <div class="response-content">{{ item.student_response }}</div>
              <div class="response-time">回复于 {{ fmtTime(item.student_reply_time) }}</div>
            </div>
            <!-- 教师自己的回复（回复学生提问） -->
            <div v-if="item.teacher_response" class="item-response teacher">
              <div class="response-label">我的回复：</div>
              <div class="response-content">{{ item.teacher_response }}</div>
              <div class="response-time">回复于 {{ fmtTime(item.teacher_reply_time) }}</div>
            </div>
            <!-- 学生提问、教师未回复 → 显示回复按钮 -->
            <div v-if="item.initiator === 'student' && item.status === 'pending' && !item.teacher_response" class="item-actions">
              <el-button size="small" type="primary" plain @click="openReply(item)">回复</el-button>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无指导记录" />
    </el-card>

    <!-- 发起指导弹窗 -->
    <el-dialog v-model="showCreate" title="发起指导" width="600px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="选择学生" required>
          <el-select v-model="form.topic_id" placeholder="选择选题（含学生）" style="width: 100%">
            <el-option v-for="t in topics" :key="t.id" :label="`${t.title} - ${t.student_name || '未分配'}`" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="指导方式">
          <el-select v-model="form.guidance_type" style="width: 100%">
            <el-option label="面对面" value="meeting" />
            <el-option label="书面" value="written" />
            <el-option label="线上" value="online" />
            <el-option label="电话" value="phone" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="指导主题">
          <el-input v-model="form.title" placeholder="简要描述指导主题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="指导内容" required>
          <el-input v-model="form.content" type="textarea" :rows="6" placeholder="详细描述本次指导内容与建议" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">提交</el-button>
      </template>
    </el-dialog>

    <!-- 教师回复学生提问弹窗 -->
    <el-dialog v-model="showReply" title="回复学生提问" width="560px">
      <div class="reply-quote">{{ replyItem?.content }}</div>
      <el-input v-model="replyText" type="textarea" :rows="4" placeholder="请输入回复内容" />
      <template #footer>
        <el-button @click="showReply = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitReply">提交回复</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'

const list = ref([])
const topics = ref([])
const filterTopic = ref(null)
const showCreate = ref(false)
const showReply = ref(false)
const submitting = ref(false)
const replyItem = ref(null)
const replyText = ref('')
const form = ref({ topic_id: null, guidance_type: 'meeting', title: '', content: '' })

const typeLabel = (t) => ({ meeting: '面对面', written: '书面', online: '线上', phone: '电话', other: '其他' }[t] || t)
const statusLabel = (s) => ({ pending: '待回复', replied: '已回复', closed: '已关闭' }[s] || s)
const statusTag = (s) => ({ pending: 'warning', replied: 'success', closed: 'info' }[s] || 'info')
const fmtTime = (t) => t ? t.replace('T', ' ').substring(0, 16) : ''

async function loadTopics() {
  try {
    const res = await request.get('/topics', { page: 1, page_size: 100 })
    const items = res.items || res.data?.items || []
    topics.value = items.filter(t => t.status === 'approved' && t.student_id)
  } catch (e) { topics.value = [] }
}

async function load() {
  try {
    const params = { page: 1, page_size: 100 }
    if (filterTopic.value) params.topic_id = filterTopic.value
    const res = await request.get('/guidance', params)
    list.value = res.items || res.data?.items || []
  } catch (e) { list.value = [] }
}

async function submitCreate() {
  if (!form.value.topic_id) return ElMessage.warning('请选择学生选题')
  if (!form.value.content.trim()) return ElMessage.warning('请填写指导内容')
  submitting.value = true
  try {
    await request.post('/guidance', form.value)
    ElMessage.success('指导记录已创建')
    showCreate.value = false
    form.value = { topic_id: null, guidance_type: 'meeting', title: '', content: '' }
    load()
  } finally {
    submitting.value = false
  }
}

function remove(item) {
  ElMessageBox.confirm(`确定删除这条指导记录吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await request.delete(`/guidance/${item.id}`)
      ElMessage.success('已删除')
      load()
    }).catch(() => {})
}

function openReply(item) {
  replyItem.value = item
  replyText.value = ''
  showReply.value = true
}

async function submitReply() {
  if (!replyText.value.trim()) return ElMessage.warning('请输入回复内容')
  submitting.value = true
  try {
    await request.post(`/guidance/${replyItem.value.id}/teacher-reply`, { teacher_response: replyText.value })
    ElMessage.success('回复成功')
    showReply.value = false
    load()
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadTopics()
  load()
})
</script>

<style scoped lang="scss">
.teacher-guidance { padding: 16px; }
.toolbar-card { margin-bottom: 12px; }
.toolbar { display: flex; gap: 12px; align-items: center; }
.list-card { background: #fff; }
.timeline { padding: 12px 0; }
.guidance-item {
  padding: 12px 16px;
  background: #f4f8fd;
  border-radius: 8px;
  border-left: 3px solid #409eff;
}
.item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.header-right { display: flex; align-items: center; gap: 10px; }
.guidance-title { font-weight: 600; color: #2c3e50; font-size: 15px; }
.item-meta { display: flex; gap: 10px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
.meta-text { font-size: 12px; color: #909399; }
.item-content { color: #606266; line-height: 1.6; white-space: pre-wrap; }
.item-response { margin-top: 10px; padding: 10px 12px; background: #f0f9eb; border-radius: 6px; }
.response-label { font-size: 12px; color: #67c23a; margin-bottom: 4px; font-weight: 600; }
.response-content { color: #606266; line-height: 1.6; white-space: pre-wrap; }
.response-time { font-size: 11px; color: #909399; margin-top: 4px; }
.item-response.teacher { background: #ecf5ff; border-left: 3px solid #409eff; border-radius: 6px; }
.item-response.teacher .response-label { color: #409eff; }
.item-actions { margin-top: 10px; }
.reply-quote {
  padding: 10px 12px; background: #f4f8fd;
  border-left: 3px solid #409eff; border-radius: 6px;
  color: #606266; margin-bottom: 12px; line-height: 1.6;
}
</style>
