import request from '@/utils/request'

// 获取开题报告列表
export function getProposalList(params) {
  return request.get('/proposals', params)
}

// 获取开题报告详情
export function getProposal(id) {
  return request.get(`/proposals/${id}`)
}

// 创建开题报告
export function createProposal(data) {
  return request.post('/proposals', data)
}

// 更新开题报告
export function updateProposal(id, data) {
  return request.put(`/proposals/${id}`, data)
}

// 提交开题报告
export function submitProposal(id) {
  return request.post(`/proposals/${id}/submit`)
}

// 审核开题报告
export function reviewProposal(id, data) {
  return request.post(`/proposals/${id}/review`, data)
}
