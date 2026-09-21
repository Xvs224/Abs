import request from '@/utils/request'

// 获取归档列表
export function getArchiveList(params) {
  return request.get('/archives', params)
}

// 获取归档详情
export function getArchive(id) {
  return request.get(`/archives/${id}`)
}

// 创建归档
export function createArchive(data) {
  return request.post('/archives', data)
}

// 更新归档
export function updateArchive(id, data) {
  return request.put(`/archives/${id}`, data)
}

// 审核归档
export function reviewArchive(id, data) {
  return request.post(`/archives/${id}/review`, data)
}
