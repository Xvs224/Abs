import request from '@/utils/request'

// 获取论文版本列表
export function getVersionList(params) {
  return request.get('/thesis/versions', params)
}

// 获取论文版本详情
export function getVersion(id) {
  return request.get(`/thesis/versions/${id}`)
}

// 提交新版本
export function createVersion(data) {
  return request.post('/thesis/versions', data)
}

// 更新版本信息
export function updateVersion(id, data) {
  return request.put(`/thesis/versions/${id}`, data)
}

// 删除版本
export function deleteVersion(id) {
  return request.delete(`/thesis/versions/${id}`)
}

// 触发格式检测
export function checkFormat(id) {
  return request.post(`/thesis/versions/${id}/check-format`)
}

// 获取格式检测结果
export function getFormatCheck(id) {
  return request.get(`/thesis/versions/${id}/format-check`)
}

// 版本对比
export function compareVersions(versionA, versionB) {
  return request.get('/thesis/versions/compare', { version_a: versionA, version_b: versionB })
}
