<template>
  <div class="stage-config-page">
    <div class="page-header">
      <div>
        <h2>阶段时间设定</h2>
        <p class="sub">管理员可自由设定各业务阶段的开始/结束时间，超时后学生提交入口自动锁定。</p>
      </div>
      <div class="header-actions">
        <el-tag type="info">admin 始终可操作不受时间窗限制</el-tag>
        <el-button type="primary" :icon="RefreshRight" @click="loadList">刷新</el-button>
        <el-button type="success" :icon="Check" @click="handleBatchSave" :loading="saving">批量保存</el-button>
      </div>
    </div>

    <el-table :data="list" v-loading="loading" border stripe style="margin-top: 16px">
      <el-table-column label="阶段" prop="module_name" width="120" />
      <el-table-column label="标识" prop="module_key" width="130" />
      <el-table-column label="状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" effect="dark">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="开始时间" min-width="200">
        <template #default="{ row }">
          <el-date-picker
            v-model="row.start_time"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 180px"
          />
        </template>
      </el-table-column>
      <el-table-column label="结束时间" min-width="200">
        <template #default="{ row }">
          <el-date-picker
            v-model="row.end_time"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 180px"
          />
        </template>
      </el-table-column>
      <el-table-column label="结束后锁定" width="220" align="center">
        <template #default="{ row }">
          <el-checkbox v-model="row.student_lock_after_end">学生</el-checkbox>
          <el-checkbox v-model="row.teacher_lock_after_end">教师</el-checkbox>
        </template>
      </el-table-column>
      <el-table-column label="剩余/已过" width="180" align="center">
        <template #default="{ row }">
          <span v-if="row.status === 'pending'" class="status-pending">未开放</span>
          <span v-else-if="row.status === 'active'" class="status-active">
            剩余 {{ daysUntil(row.end_time) }} 天
          </span>
          <span v-else class="status-locked">已结束 {{ daysSince(row.end_time) }} 天</span>
        </template>
      </el-table-column>
      <el-table-column label="备注">
        <template #default="{ row }">
          <el-input v-model="row.description" placeholder="可选" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right" align="center">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="handleSave(row)">保存</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { RefreshRight, Check } from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const saving = ref(false)
const list = ref([])

const statusTag = (s) => ({ pending: 'info', active: 'success', locked: 'danger' }[s] || 'info')
const statusLabel = (s) => ({ pending: '未开放', active: '进行中', locked: '已结束' }[s] || s)
const daysUntil = (iso) => Math.max(0, Math.ceil((new Date(iso) - Date.now()) / 86400000))
const daysSince = (iso) => Math.max(0, Math.ceil((Date.now() - new Date(iso)) / 86400000))

const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/stages')
    list.value = (res || []).map(s => ({
      ...s,
      // 把 ISO 转成 date-picker 要的 datetime-local 格式
      start_time: isoToPicker(s.start_time),
      end_time: isoToPicker(s.end_time),
    }))
  } catch (e) { /* request interceptor 已弹 */ }
  finally { loading.value = false }
}

const isoToPicker = (iso) => {
  if (!iso) return ''
  // '2026-09-23T09:32:45' -> 原样即可用
  return iso.replace('Z', '').slice(0, 19)
}

const handleSave = async (row) => {
  if (!row.start_time || !row.end_time) {
    ElMessage.warning('请先填写完整时间')
    return
  }
  if (new Date(row.end_time) <= new Date(row.start_time)) {
    ElMessage.warning('结束时间必须晚于开始时间')
    return
  }
  try {
    await request.put(`/stages/${row.module_key}`, {
      module_key: row.module_key,
      module_name: row.module_name,
      start_time: row.start_time,
      end_time: row.end_time,
      student_lock_after_end: row.student_lock_after_end ? 1 : 0,
      teacher_lock_after_end: row.teacher_lock_after_end ? 1 : 0,
      description: row.description || '',
    })
    ElMessage.success('保存成功')
    loadList()
  } catch (e) {}
}

const handleBatchSave = async () => {
  saving.value = true
  try {
    const payloads = list.value.map(r => ({
      module_key: r.module_key,
      module_name: r.module_name,
      start_time: r.start_time,
      end_time: r.end_time,
      student_lock_after_end: r.student_lock_after_end ? 1 : 0,
      teacher_lock_after_end: r.teacher_lock_after_end ? 1 : 0,
      description: r.description || '',
    }))
    await request.put('/stages/batch', payloads)
    ElMessage.success('批量保存成功')
    loadList()
  } catch (e) {}
  finally { saving.value = false }
}

onMounted(loadList)
</script>

<style scoped>
.stage-config-page {
  padding: 16px;
  background: linear-gradient(180deg, #f4f8fd 0%, #ffffff 240px);
  min-height: 100%;
}
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-header h2 {
  margin: 0 0 4px 0;
  color: #3a6ea5;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.page-header .sub { margin: 0; color: #8fa6bd; font-size: 13px; }
.header-actions { display: flex; gap: 10px; align-items: center; }

.status-pending { color: #909399; }
.status-active  { color: #3a6ea5; font-weight: 600; }
.status-locked  { color: #b37f40; font-weight: 600; }
</style>
