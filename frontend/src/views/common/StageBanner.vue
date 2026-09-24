<!--
阶段时间提示条（简洁淡蓝色风格，无表情符号）
用法：<StageBanner module-key="proposal" />
-->
<template>
  <el-alert
    v-if="visible"
    :title="alertTitle"
    :type="alertType"
    :closable="false"
    show-icon
    style="margin-bottom: 12px"
  >
    <template #default>
      <div class="stage-banner-content">
        <template v-if="stage">
          <span class="stage-name">{{ stage.module_name }}</span>
          <span class="stage-window">
            时间窗口：
            <b>{{ fmt(stage.start_time) }}</b>
             ~
            <b>{{ fmt(stage.end_time) }}</b>
          </span>
          <span v-if="stage.status === 'active'" class="stage-remain">
            剩余 {{ remainDays }} 天
          </span>
          <span v-else-if="stage.status === 'pending'" class="stage-tip">
            尚未开放，请耐心等待
          </span>
          <span v-else class="stage-tip locked">
            已结束，提交入口已锁定
          </span>
        </template>
        <template v-else>
          <span>未配置阶段时间，请联系管理员</span>
        </template>
      </div>
    </template>
  </el-alert>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import request from '@/utils/request'

const props = defineProps({
  moduleKey: { type: String, required: true },
  onlyWarn: { type: Boolean, default: false },
})

const stage = ref(null)

const visible = computed(() => {
  if (!stage.value) return true
  if (props.onlyWarn) return stage.value.status !== 'active'
  return true
})

// 统一走淡蓝色 success + info，active=浅蓝、pending=灰蓝、locked=深蓝
const alertType = computed(() => {
  if (!stage.value) return 'info'
  return { pending: 'info', active: 'success', locked: 'warning' }[stage.value.status] || 'info'
})

const alertTitle = computed(() => {
  if (!stage.value) return '阶段时间未配置'
  return {
    pending: `${stage.value.module_name} 尚未开放`,
    active: `${stage.value.module_name} 进行中`,
    locked: `${stage.value.module_name} 已结束（已锁定）`,
  }[stage.value.status] || ''
})

const remainDays = computed(() => {
  if (!stage.value?.end_time) return 0
  return Math.max(0, Math.ceil((new Date(stage.value.end_time) - Date.now()) / 86400000))
})

const fmt = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const load = async () => {
  try {
    const list = await request.get('/stages')
    const hit = (list || []).find(s => s.module_key === props.moduleKey)
    stage.value = hit || null
  } catch (e) {
    stage.value = null
  }
}

onMounted(load)
// 路由切换时（如论文一稿→二稿→终审复用同一组件）moduleKey 会变，重新拉取
watch(() => props.moduleKey, load, { immediate: false })
</script>

<style scoped>
.stage-banner-content {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--el-text-color-regular, #606266);
}
.stage-name {
  font-weight: 600;
  color: #4a7fb5;
  letter-spacing: 0.3px;
}
.stage-window b {
  color: var(--el-text-color-primary, #303133);
  font-weight: 600;
}
.stage-remain {
  color: #409eff;
  font-weight: 600;
}
.stage-tip { color: #909399; }
.stage-tip.locked {
  color: #b37f40;
  font-weight: 600;
}
</style>
