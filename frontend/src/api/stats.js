import request from '@/utils/request'

// 获取概览统计
export function getOverviewStats() {
  return request.get('/stats/overview')
}

// 选题状态分布
export function getTopicStatusDistribution() {
  return request.get('/stats/topic-status-distribution')
}

// 各院系进度
export function getProgressByDepartment() {
  return request.get('/stats/progress-by-department')
}

// 异常趋势
export function getAnomalyTrend(days = 7) {
  return request.get('/stats/anomaly-trend', { days })
}

// 指导统计
export function getGuidanceStats() {
  return request.get('/stats/guidance-stats')
}

// 成绩分布
export function getScoreDistribution() {
  return request.get('/stats/score-distribution')
}
