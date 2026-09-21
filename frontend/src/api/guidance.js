import request from '@/utils/request'

// 获取指导计划列表
export function getPlanList(params) {
  return request.get('/guidance/plans', params)
}

// 获取指导计划详情
export function getPlan(id) {
  return request.get(`/guidance/plans/${id}`)
}

// 创建指导计划
export function createPlan(data) {
  return request.post('/guidance/plans', data)
}

// 更新指导计划
export function updatePlan(id, data) {
  return request.put(`/guidance/plans/${id}`, data)
}

// 删除指导计划
export function deletePlan(id) {
  return request.delete(`/guidance/plans/${id}`)
}

// 获取指导记录列表
export function getRecordList(params) {
  return request.get('/guidance/records', params)
}

// 获取指导记录详情
export function getRecord(id) {
  return request.get(`/guidance/records/${id}`)
}

// 创建指导记录
export function createRecord(data) {
  return request.post('/guidance/records', data)
}

// 更新指导记录
export function updateRecord(id, data) {
  return request.put(`/guidance/records/${id}`, data)
}

// 删除指导记录
export function deleteRecord(id) {
  return request.delete(`/guidance/records/${id}`)
}
