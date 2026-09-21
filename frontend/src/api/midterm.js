import request from '@/utils/request'

// 获取中期检查列表
export function getMidtermList(params) {
  return request.get('/midterm', params)
}

// 获取中期检查详情
export function getMidterm(id) {
  return request.get(`/midterm/${id}`)
}

// 创建中期检查
export function createMidterm(data) {
  return request.post('/midterm', data)
}

// 更新中期检查
export function updateMidterm(id, data) {
  return request.put(`/midterm/${id}`, data)
}

// 提交中期检查
export function submitMidterm(id) {
  return request.post(`/midterm/${id}/submit`)
}

// 评审中期检查
export function reviewMidterm(id, data) {
  return request.post(`/midterm/${id}/review`, data)
}

// 获取整改列表
export function getRectificationList(midtermId, params) {
  return request.get(`/midterm/rectifications`, { midterm_id: midtermId, ...params })
}

// 创建整改
export function createRectification(data) {
  return request.post('/midterm/rectifications', data)
}

// 提交整改
export function submitRectification(id, data) {
  return request.post(`/midterm/rectifications/${id}/submit`, data)
}

// 复检整改
export function reviewRectification(id, data) {
  return request.post(`/midterm/rectifications/${id}/review`, data)
}
