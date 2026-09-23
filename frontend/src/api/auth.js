import request from '@/utils/request'

// 登录
export function login(data) {
  return request.post('/auth/login', data)
}

// 刷新令牌
export function refreshToken(refreshToken) {
  return request.post('/auth/refresh', { refresh_token: refreshToken })
}

// 登出（撤销令牌）
export function logout(accessToken, refreshToken) {
  return request.post('/auth/logout', {
    access_token: accessToken,
    refresh_token: refreshToken
  })
}

// 获取当前用户信息
export function getCurrentUser() {
  return request.get('/auth/me')
}
