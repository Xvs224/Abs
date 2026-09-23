import request from '@/utils/request'

// 触发异常检测
export function detectAnomaly(data) {
  return request.post('/anomaly/detect', data)
}

// 批量检测
export function batchDetect(data) {
  return request.post('/anomaly/detect/batch', data)
}

// 获取异常记录列表
export function getAnomalyList(params) {
  return request.get('/anomaly/records', params)
}

// 获取异常记录详情
export function getAnomalyDetail(id) {
  return request.get(`/anomaly/records/${id}`)
}

// 人工复核
export function reviewAnomaly(id, data) {
  return request.post(`/anomaly/records/${id}/review`, data)
}

// 获取复核历史
export function getAnomalyReviews(id) {
  return request.get(`/anomaly/records/${id}/reviews`)
}

// 异常统计
export function getAnomalyStats() {
  return request.get('/anomaly/stats')
}

// 准确性评估
export function evaluateAnomaly(data) {
  return request.post('/anomaly/evaluate', data)
}

// ============ 定时检测调度管理 ============

// 查询调度状态
export function getScheduleStatus() {
  return request.get('/anomaly/schedule')
}

// 更新 cron 表达式
export function updateScheduleCron(cron) {
  return request.put('/anomaly/schedule', null, { params: { cron } })
}

// 暂停定时检测
export function pauseSchedule() {
  return request.post('/anomaly/schedule/pause')
}

// 恢复定时检测
export function resumeSchedule() {
  return request.post('/anomaly/schedule/resume')
}

// 立即触发一次全量检测
export function triggerDetectionNow() {
  return request.post('/anomaly/schedule/trigger')
}
