import { ref, onMounted, watch } from 'vue'
import request from '@/utils/request'

// 简单缓存，避免同一页面 StageBanner + composable 重复请求
let stageCache = null
let cachePromise = null

const fetchStages = async () => {
  if (stageCache) return stageCache
  if (cachePromise) return cachePromise
  cachePromise = request.get('/stages').then(res => {
    stageCache = res || []
    return stageCache
  }).finally(() => {
    cachePromise = null
  })
  return cachePromise
}

// 供刷新使用
export const clearStageCache = () => {
  stageCache = null
}

/**
 * 判断指定模块的阶段是否对学生锁定
 * 锁定规则：
 *   - pending（尚未开放）：学生禁用
 *   - active（进行中）：学生可用
 *   - locked（已结束）：仅当 student_lock_after_end 为 true 时学生禁用
 * @param {string|import('vue').Ref<string>} moduleKey 模块 key
 * @returns {{ isLocked: import('vue').Ref<boolean>, stage: import('vue').Ref<object|null>, loading: import('vue').Ref<boolean> }}
 */
export function useStageLock(moduleKey) {
  const isLocked = ref(false)
  const stage = ref(null)
  const loading = ref(true)

  const load = async () => {
    const key = typeof moduleKey === 'object' ? moduleKey.value : moduleKey
    if (!key) {
      isLocked.value = false
      loading.value = false
      return
    }
    loading.value = true
    try {
      const list = await fetchStages()
      const hit = (list || []).find(s => s.module_key === key)
      stage.value = hit || null
      // 非进行中阶段均可能锁定：pending 一律锁定，locked 按配置锁定
      if (!hit) {
        isLocked.value = false
      } else if (hit.status === 'active') {
        isLocked.value = false
      } else if (hit.status === 'pending') {
        isLocked.value = true
      } else {
        isLocked.value = !!hit.student_lock_after_end
      }
    } catch (e) {
      isLocked.value = false
      stage.value = null
    } finally {
      loading.value = false
    }
  }

  onMounted(load)
  if (typeof moduleKey === 'object') {
    watch(moduleKey, load)
  }

  return { isLocked, stage, loading }
}
