<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <el-icon size="48" color="#ffffff"><DataAnalysis /></el-icon>
        <h1>毕业论文质量监控系统</h1>
        <p>基于异常检测的全过程质量监控平台</p>
      </div>

      <!-- 角色选择 -->
      <div class="role-selector">
        <div
          v-for="item in roleOptions"
          :key="item.value"
          class="role-item"
          :class="{ active: selectedRole === item.value }"
          @click="selectRole(item)"
        >
          <el-icon size="24"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </div>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="login-btn"
          :loading="loading"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>

      <div class="login-tips">
        <p>演示账号（点击角色可快速填充）：</p>
        <p>管理员：admin / admin123</p>
        <p>教师：teacher01 / teacher123</p>
        <p>学生：student01 / student123</p>
      </div>
    </div>

    <div class="login-footer">
      <p>© 2025 毕业论文质量监控系统 · 毕业设计</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import { User, Lock, Avatar, Reading, UserFilled } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)
const selectedRole = ref('admin')

const roleOptions = [
  { value: 'admin', label: '管理员', icon: 'Avatar', username: 'admin', password: 'admin123' },
  { value: 'teacher', label: '教师', icon: 'Reading', username: 'teacher01', password: 'teacher123' },
  { value: 'student', label: '学生', icon: 'UserFilled', username: 'student01', password: 'student123' },
]

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ]
}

const selectRole = (item) => {
  selectedRole.value = item.value
  loginForm.username = item.username
  loginForm.password = item.password
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    loading.value = true

    const res = await userStore.login(loginForm)

    // 校验角色是否匹配
    if (selectedRole.value !== res.role) {
      ElMessage.warning(`您选择的是${getRoleLabel(selectedRole.value)}，但该账号是${getRoleLabel(res.role)}角色`)
    }

    ElMessage.success('登录成功')

    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  } catch (error) {
    console.error('登录失败:', error)
  } finally {
    loading.value = false
  }
}

const getRoleLabel = (role) => {
  const map = { admin: '管理员', teacher: '教师', student: '学生' }
  return map[role] || role
}
</script>

<style scoped lang="scss">
.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 500px;
    height: 500px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 50%;
    top: -200px;
    right: -100px;
  }

  &::after {
    content: '';
    position: absolute;
    width: 300px;
    height: 300px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 50%;
    bottom: -100px;
    left: -50px;
  }
}

.login-box {
  width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 24px;

  h1 {
    font-size: 22px;
    color: #303133;
    margin: 12px 0 8px;
    font-weight: 600;
  }

  p {
    font-size: 13px;
    color: #909399;
    margin: 0;
  }
}

.role-selector {
  display: flex;
  gap: 10px;
  margin-bottom: 24px;

  .role-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 12px 8px;
    border: 2px solid #e4e7ed;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.25s;
    color: #909399;

    span {
      font-size: 13px;
      font-weight: 500;
    }

    &:hover {
      border-color: #0ea5e9;
      color: #0ea5e9;
    }

    &.active {
      border-color: #0ea5e9;
      background: #e0f2fe;
      color: #0ea5e9;
    }
  }
}

.login-form {
  .login-btn {
    width: 100%;
    margin-top: 10px;
    height: 44px;
    font-size: 16px;
  }
}

.login-tips {
  margin-top: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.8;

  p {
    margin: 0;
  }
}

.login-footer {
  margin-top: 30px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  position: relative;
  z-index: 1;

  p {
    margin: 0;
  }
}
</style>
