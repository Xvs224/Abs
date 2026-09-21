import { defineStore } from 'pinia'
import request from '@/utils/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
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
        this.userInfo = res.user
        localStorage.setItem('token', res.access_token)
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

    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
    }
  }
})
