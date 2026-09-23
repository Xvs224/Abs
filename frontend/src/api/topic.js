import request from '@/utils/request'

// 获取选题列表
export function getTopicList(params) {
  return request.get('/topics', params)
}

// 获取选题详情
export function getTopic(id) {
  return request.get(`/topics/${id}`)
}

// 创建选题（兼容旧接口）
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

// 重交选题
export function resubmitTopic(id) {
  return request.post(`/topics/${id}/resubmit`)
}

// 审核选题
export function reviewTopic(id, data) {
  return request.post(`/topics/${id}/review`, data)
}

// 选题重复检测
export function checkDuplicate(title) {
  return request.post('/topics/check-duplicate', { title })
}

// 教师发布选题
export function publishTopic(data) {
  return request.post('/topics/teacher/publish', data)
}

// 学生查看可选选题列表
export function getAvailableTopics(params) {
  return request.get('/topics/available', params)
}

// 学生选择教师发布选题
export function selectTopic(topicId) {
  return request.post('/topics/student/select', { topic_id: topicId })
}

// 学生自拟选题
export function selfProposeTopic(data) {
  return request.post('/topics/student/self-propose', data)
}

// 学生取消选题
export function cancelTopic(id) {
  return request.post(`/topics/${id}/cancel`)
}
