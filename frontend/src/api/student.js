import request from '@/utils/request'

export default {
  getMyTopic() {
    return request.get('/topics', { page: 1, page_size: 1 })
  },

  getTopicDetail(id) {
    return request.get(`/topics/${id}`)
  },

  createTopic(data) {
    return request.post('/topics', data)
  },

  updateTopic(id, data) {
    return request.put(`/topics/${id}`, data)
  },

  deleteTopic(id) {
    return request.delete(`/topics/${id}`)
  },

  resubmitTopic(id) {
    return request.post(`/topics/${id}/resubmit`)
  },

  checkDuplicate(title) {
    return request.post('/topics/check-duplicate', { title })
  },

  getAvailableTopics(params = {}) {
    return request.get('/topics/available', { page: 1, page_size: 50, ...params })
  },

  selectTopic(topicId) {
    return request.post('/topics/student/select', { topic_id: topicId })
  },

  selfProposeTopic(data) {
    return request.post('/topics/student/self-propose', data)
  },

  cancelTopic(id) {
    return request.post(`/topics/${id}/cancel`)
  },

  getMyProposal() {
    return request.get('/proposals', { page: 1, page_size: 1 })
  },

  getProposalDetail(id) {
    return request.get(`/proposals/${id}`)
  },

  createProposal(data) {
    return request.post('/proposals', data)
  },

  updateProposal(id, data) {
    return request.put(`/proposals/${id}`, data)
  },

  submitProposal(id) {
    return request.post(`/proposals/${id}/submit`)
  },

  getMyMidterm(params = {}) {
    return request.get('/midterm', { page: 1, page_size: 10, ...params })
  },

  getMidtermDetail(id) {
    return request.get(`/midterm/${id}`)
  },

  createMidterm(data) {
    return request.post('/midterm', data)
  },

  updateMidterm(id, data) {
    return request.put(`/midterm/${id}`, data)
  },

  submitMidterm(id) {
    return request.post(`/midterm/${id}/submit`)
  },

  submitMidtermPPT(id, data) {
    return request.post(`/midterm/${id}/submit-ppt`, data)
  },

  getMyRectifications(params = {}) {
    return request.get('/midterm/rectifications', { page: 1, page_size: 50, ...params })
  },

  getRectificationDetail(id) {
    return request.get(`/midterm/rectifications/${id}`)
  },

  submitRectification(id, data) {
    return request.post(`/midterm/rectifications/${id}/submit`, data)
  },

  getMyThesisVersions(params = {}) {
    return request.get('/thesis/versions', { page: 1, page_size: 50, ...params })
  },

  getThesisVersionDetail(id) {
    return request.get(`/thesis/versions/${id}`)
  },

  uploadThesisVersion(file, { topic_id, version_name, change_log, auto_check, version_num }) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('version_name', version_name || `v${Date.now()}`)
    formData.append('change_log', change_log || '')
    if (version_num) formData.append('version_num', version_num)
    return request.post('/thesis/versions', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(res => {
      if (auto_check && res.id) {
        return request.post(`/thesis/versions/${res.id}/format-check`).then(() => res)
      }
      return res
    })
  },

  updateThesisVersion(id, data) {
    return request.put(`/thesis/versions/${id}`, data)
  },

  deleteThesisVersion(id) {
    return request.delete(`/thesis/versions/${id}`)
  },

  triggerFormatCheck(versionId) {
    return request.post(`/thesis/versions/${versionId}/format-check`)
  },

  getFormatCheckResult(versionId) {
    return request.get(`/thesis/versions/${versionId}/format-check`)
  },

  compareVersions(v1, v2) {
    return request.get('/thesis/versions/compare', { v1, v2 })
  },

  getMyReviews(params = {}) {
    return request.get('/reviews', { page: 1, page_size: 10, ...params })
  },

  getReviewDetail(id) {
    return request.get(`/reviews/${id}`)
  },

  applyReview(versionId, reviewType = 'normal') {
    return request.post('/reviews/apply', { version_id: versionId, review_type: reviewType })
  },

  applyRedefense() {
    return request.post('/defenses/apply-redefense')
  },

  getMyDefenses(params = {}) {
    return request.get('/defenses', { page: 1, page_size: 10, ...params })
  },

  getDefenseDetail(id) {
    return request.get(`/defenses/${id}`)
  },

  getMyAnomalyRecords(params = {}) {
    return request.get('/anomaly/records', { page: 1, page_size: 50, ...params })
  },

  getMyAnomalyStats() {
    return request.get('/anomaly/stats')
  },

  getAnomalyDetail(id) {
    return request.get(`/anomaly/records/${id}`)
  },

  getMyArchives(params = {}) {
    return request.get('/archives', { page: 1, page_size: 10, ...params })
  },

  getArchiveDetail(id) {
    return request.get(`/archives/${id}`)
  },

  createArchive(data) {
    return request.post('/archives', data)
  },

  updateArchive(id, data) {
    return request.put(`/archives/${id}`, data)
  },

  uploadFile(file, module = '', targetId = null) {
    const formData = new FormData()
    formData.append('file', file)
    const params = { module }
    if (targetId) params.target_id = targetId
    return request.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params
    })
  },

  downloadFile(fileId) {
    return request.download(`/files/${fileId}/download`)
  },

  getMyInfo() {
    return request.get('/auth/me')
  },

  changePassword(userId, data) {
    return request.put(`/users/${userId}/password`, data)
  },

  updateMyInfo(userId, data) {
    return request.put(`/users/${userId}`, data)
  },

  // ===== 过程指导 =====
  getGuidanceList(params = {}) {
    return request.get('/guidance', { page: 1, page_size: 50, ...params })
  },
  getGuidanceDetail(id) {
    return request.get(`/guidance/${id}`)
  },
  createGuidance(data) {
    return request.post('/guidance', data)
  },
  replyGuidance(id, data) {
    return request.post(`/guidance/${id}/reply`, data)
  },
  deleteGuidance(id) {
    return request.delete(`/guidance/${id}`)
  }
}
