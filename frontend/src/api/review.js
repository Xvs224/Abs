import request from '@/utils/request'

// 获取评阅列表
export function getReviewList(params) {
  return request.get('/reviews', params)
}

// 获取评阅详情
export function getReview(id) {
  return request.get(`/reviews/${id}`)
}

// 分配评阅
export function createReview(data) {
  return request.post('/reviews', data)
}

// 提交评阅结果
export function submitReview(id, data) {
  return request.post(`/reviews/${id}/submit`, data)
}

// 获取答辩列表
export function getDefenseList(params) {
  return request.get('/defenses', params)
}

// 获取答辩详情
export function getDefense(id) {
  return request.get(`/defenses/${id}`)
}

// 创建答辩安排
export function createDefense(data) {
  return request.post('/defenses', data)
}

// 更新答辩安排
export function updateDefense(id, data) {
  return request.put(`/defenses/${id}`, data)
}

// 提交答辩评分
export function scoreDefense(id, data) {
  return request.post(`/defenses/${id}/score`, data)
}
