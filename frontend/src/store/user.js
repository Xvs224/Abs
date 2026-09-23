import { defineStore } from 'pinia'
import request from '@/utils/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    refreshToken: localStorage.getItem('refreshToken') || '',
    userInfo: JSON.parse(localStorage.getItem('userInfo') || 'null')
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state) => state.userInfo?.role || '',
    username: (state) => state.userInfo?.real_name || state.userInfo?.username || ''
  },

  actions: {
    async login(loginData) {
      try {
        const res = await request.post('/auth/login', loginData)
        this.token = res.access_token
        this.refreshToken = res.refresh_token
        this.userInfo = res.user
        localStorage.setItem('token', res.access_token)
        localStorage.setItem('refreshToken', res.refresh_token)
        localStorage.setItem('userInfo', JSON.stringify(res.user))
        return res
      } catch (error) {
        throw error
      }
    },

    async getUserInfo() {
      try {
        const res = await request.get('/auth/me')
        this.userInfo = res
        localStorage.setItem('userInfo', JSON.stringify(res))
        return res
      } catch (error) {
        throw error
      }
    },

    async logout() {
      try {
        if (this.token) {
          await request.post('/auth/logout', {
            access_token: this.token,
            refresh_token: this.refreshToken
          })
        }
      } catch (e) {
        // 即使后端登出失败也清除本地状态
      }
      this.token = ''
      this.refreshToken = ''
      this.userInfo = null
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('userInfo')
    }
  }
})
