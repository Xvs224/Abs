import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'
import { useUserStore } from '@/store/user'

// 是否正在刷新 token
let isRefreshing = false
// 等待 token 刷新的请求队列
let pendingRequests = []

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers['Authorization'] = `Bearer ${userStore.token}`
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data

    // 文件下载直接返回
    if (response.config.responseType === 'blob') {
      return response
    }

    // 成功响应
    if (res.code === 200) {
      return res.data
    }

    // 业务错误（HTTP 200 但 code 非 200）
    ElMessage({
      message: res.message || '请求失败',
      type: 'error',
      duration: 3000
    })
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  async error => {
    console.error('响应错误:', error)
    const originalRequest = error.config

    // 401 且非登录/刷新接口 且未在重试中 → 尝试 refresh token
    if (
      error.response &&
      error.response.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes('/auth/login') &&
      !originalRequest.url.includes('/auth/refresh') &&
      !originalRequest.url.includes('/auth/logout')
    ) {
      const userStore = useUserStore()

      if (!userStore.refreshToken) {
        _handleSessionExpired()
        return Promise.reject(error)
      }

      if (isRefreshing) {
        // 正在刷新，排队等待
        return new Promise((resolve, reject) => {
          pendingRequests.push({ originalRequest, resolve, reject })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const response = await axios.post(
          `${service.defaults.baseURL}/auth/refresh`,
          { refresh_token: userStore.refreshToken }
        )
        const newToken = response.data.data.access_token
        userStore.token = newToken

        // 重放排队的请求
        pendingRequests.forEach(({ originalRequest, resolve, reject }) => {
          originalRequest.headers['Authorization'] = `Bearer ${newToken}`
          service(originalRequest).then(resolve).catch(reject)
        })
        pendingRequests = []

        // 重试原请求
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`
        return service(originalRequest)
      } catch (refreshError) {
        pendingRequests = []
        _handleSessionExpired()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 其他错误处理
    let message = '网络错误，请稍后重试'

    if (error.response) {
      switch (error.response.status) {
        case 401:
          message = error.response.data?.message || '未授权，请先登录'
          _handleSessionExpired()
          break
        case 403:
          message = error.response.data?.message || '权限不足，禁止访问'
          break
        case 404:
          message = error.response.data?.message || '请求的资源不存在'
          break
        case 409:
          message = error.response.data?.message || '数据冲突'
          break
        case 422:
          message = error.response.data?.message || '参数验证失败'
          break
        case 429:
          message = '请求过于频繁，请稍后再试'
          break
        case 500:
          message = error.response.data?.message || '服务器内部错误'
          break
        default:
          message = error.response.data?.message || `请求错误 (${error.response.status})`
      }
    } else if (error.request) {
      message = '网络连接失败，请检查网络设置'
    }

    ElMessage({
      message,
      type: 'error',
      duration: 3000
    })

    return Promise.reject(error)
  }
)

function _handleSessionExpired() {
  const userStore = useUserStore()
  userStore.logout()
  ElMessageBox.confirm('登录状态已过期，请重新登录', '提示', {
    confirmButtonText: '重新登录',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    router.push('/login')
  }).catch(() => {})
}

// 封装请求方法
const request = {
  get(url, params = {}, config = {}) {
    return service.get(url, { params, ...config })
  },
  post(url, data = {}, config = {}) {
    return service.post(url, data, config)
  },
  put(url, data = {}, config = {}) {
    return service.put(url, data, config)
  },
  delete(url, config = {}) {
    return service.delete(url, config)
  },
  upload(url, file, config = {}) {
    const formData = new FormData()
    formData.append('file', file)
    return service.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      ...config
    })
  },
  download(url, config = {}) {
    return service.get(url, { responseType: 'blob', ...config })
  }
}

export default request
