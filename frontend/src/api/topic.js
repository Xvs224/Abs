import request from '@/utils/request'

// 获取选题列表
export function getTopicList(params) {
  return request.get('/topics', params)
}

// 获取选题详情
export function getTopic(id) {
  return request.get(`/topics/${id}`)
}

// 创建选题
export function createTopic(data) {
  return request.post('/topics', data)
}

// 更新选题
export function updateTopic(id, data) {
  return request.put(`/topics/${id}`, data)
}

// 删除选题
export function deleteTopic(id) {
  return request.delete(`/topics/${id}`)
}

// 审核选题
export function reviewTopic(id, data) {
  return request.post(`/topics/${id}/review`, data)
}

// 选题重复检测
export function checkDuplicate(title) {
  return request.get('/topics/duplicate-check', { title })
}
