<template>
  <div class="guidance-page">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-button type="primary" @click="showCreate = true">
          <el-icon><Plus /></el-icon> 发起提问
        </el-button>
        <el-tag v-if="pendingCount > 0" type="warning" effect="plain">
          待回复 {{ pendingCount }} 条
        </el-tag>
      </div>
    </el-card>

    <el-card shadow="never" class="list-card">
      <el-timeline v-if="list.length" class="timeline">
        <el-timeline-item
          v-for="item in list"
          :key="item.id"
          :timestamp="fmtTime(item.guidance_time || item.create_time)"
          placement="top"
          :type="timelineType(item)"
        >
          <div class="guidance-item">
            <div class="item-header">
              <span class="guidance-title">{{ item.title || '指导记录' }}</span>
              <el-tag size="small" :type="statusTag(item.status)" effect="light">
                {{ statusLabel(item.status) }}
              </el-tag>
            </div>
            <div class="item-meta">
              <el-tag size="small" type="info" effect="plain">{{ typeLabel(item.guidance_type) }}</el-tag>
              <span class="meta-text">{{ item.initiator === 'teacher' ? '教师指导' : '学生提问' }}</span>
            </div>
            <div class="item-content">{{ item.content }}</div>
            <!-- 教师回复（学生提问后老师回复） -->
            <div v-if="item.teacher_response" class="item-response teacher">
              <div class="response-label">教师回复：</div>
              <div class="response-content">{{ item.teacher_response }}</div>
              <div class="response-time">回复于 {{ fmtTime(item.teacher_reply_time) }}</div>
            </div>
            <!-- 学生回复（教师指导后学生回复） -->
            <div v-if="item.student_response" class="item-response">
              <div class="response-label">我的回复：</div>
              <div class="response-content">{{ item.student_response }}</div>
              <div class="response-time">回复于 {{ fmtTime(item.student_reply_time) }}</div>
            </div>
            <!-- 教师发起、学生未回复 → 显示回复按钮 -->
            <div v-if="!item.student_response && item.status === 'pending' && item.initiator === 'teacher'" class="item-actions">
              <el-button size="small" type="primary" plain @click="openReply(item)">回复</el-button>
            </div>
            <!-- 学生提问、教师未回复 → 显示等待提示 -->
            <div v-if="item.initiator === 'student' && item.status === 'pending' && !item.teacher_response" class="wait-tip">
              <el-icon><Clock /></el-icon> 等待教师回复...
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无指导记录，主动向老师提问吧" />
    </el-card>

    <!-- 发起提问弹窗 -->
    <el-dialog v-model="showCreate" title="发起提问" width="560px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="选题">
          <el-input :model-value="topicTitle" disabled />
        </el-form-item>
        <el-form-item label="主题" required>
          <el-input v-model="form.title" placeholder="简要描述问题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="问题内容" required>
          <el-input v-model="form.content" type="textarea" :rows="5" placeholder="详细描述你遇到的问题" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">提交</el-button>
      </template>
    </el-dialog>

    <!-- 回复弹窗 -->
    <el-dialog v-model="showReply" title="回复指导" width="560px">
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Clock } from '@element-plus/icons-vue'
import studentApi from '@/api/student'

const list = ref([])
const showCreate = ref(false)
const showReply = ref(false)
const submitting = ref(false)
const topicTitle = ref('')
const topicId = ref(null)
const replyItem = ref(null)
const replyText = ref('')
const form = ref({ title: '', content: '', guidance_type: 'online' })

const pendingCount = computed(() => list.value.filter(i => i.status === 'pending' && i.initiator === 'teacher').length)

const typeLabel = (t) => ({ meeting: '面对面', written: '书面', online: '线上', phone: '电话', other: '其他' }[t] || t)
const statusLabel = (s) => ({ pending: '待回复', replied: '已回复', closed: '已关闭' }[s] || s)
const statusTag = (s) => ({ pending: 'warning', replied: 'success', closed: 'info' }[s] || 'info')
const timelineType = (item) => item.initiator === 'teacher' ? 'primary' : 'success'
const fmtTime = (t) => t ? t.replace('T', ' ').substring(0, 16) : ''

async function load() {
  try {
    const res = await studentApi.getGuidanceList({ page_size: 100 })
    list.value = res.items || res.data?.items || []
  } catch (e) {
    list.value = []
  }
}

async function loadTopic() {
  try {
    const res = await studentApi.getMyTopic()
    const items = res.data?.items || res.items || []
    // 优先取已通过的选题，否则取第一条
    const mine = items.find(t => t.status === 'approved') || items[0]
    if (mine) {
      topicId.value = mine.id
      topicTitle.value = mine.title
    }
  } catch (e) {}
}

async function submitCreate() {
  if (!form.value.title.trim() || !form.value.content.trim()) {
    return ElMessage.warning('请填写主题和问题内容')
  }
  if (!topicId.value) return ElMessage.error('未找到你的选题，无法发起提问')
  submitting.value = true
  try {
    await studentApi.createGuidance({ topic_id: topicId.value, ...form.value })
    ElMessage.success('提问已提交')
    showCreate.value = false
    form.value = { title: '', content: '', guidance_type: 'online' }
    load()
  } finally {
    submitting.value = false
  }
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
    await studentApi.replyGuidance(replyItem.value.id, { student_response: replyText.value })
    ElMessage.success('回复成功')
    showReply.value = false
    load()
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadTopic()
  load()
})
</script>

<style scoped lang="scss">
.guidance-page { padding: 16px; }
.toolbar-card { margin-bottom: 12px; }
.toolbar { display: flex; align-items: center; gap: 12px; }
.list-card { background: #fff; }
.timeline { padding: 12px 0; }
.guidance-item {
  padding: 12px 16px;
  background: #f4f8fd;
  border-radius: 8px;
  border-left: 3px solid #409eff;
}
.item-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 6px;
}
.guidance-title { font-weight: 600; color: #2c3e50; font-size: 15px; }
.item-meta { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.meta-text { font-size: 12px; color: #909399; }
.item-content { color: #606266; line-height: 1.6; white-space: pre-wrap; }
.item-response {
  margin-top: 10px; padding: 10px 12px;
  background: #ecf5ff; border-radius: 6px;
}
.response-label { font-size: 12px; color: #409eff; margin-bottom: 4px; font-weight: 600; }
.response-content { color: #606266; line-height: 1.6; white-space: pre-wrap; }
.response-time { font-size: 11px; color: #909399; margin-top: 4px; }
.item-actions { margin-top: 10px; }
.wait-tip {
  margin-top: 10px; font-size: 13px; color: #909399;
  display: flex; align-items: center; gap: 4px;
}
.item-response.teacher {
  background: #fdf6ec; border-left-color: #e6a23c;
}
.item-response.teacher .response-label { color: #e6a23c; }
.reply-quote {
  padding: 10px 12px; background: #f4f8fd;
  border-left: 3px solid #409eff; border-radius: 6px;
  color: #606266; margin-bottom: 12px; line-height: 1.6;
}
</style>
