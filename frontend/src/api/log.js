import request from '@/utils/request'

// 获取操作日志列表
export function getLogList(params) {
  return request.get('/logs', params)
}

// 获取日志详情
export function getLog(id) {
  return request.get(`/logs/${id}`)
}

// 获取模块列表
export function getModuleList() {
  return request.get('/logs/modules/list')
}
