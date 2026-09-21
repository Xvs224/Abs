<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <!-- 用户信息卡片 -->
      <el-col :span="8">
        <el-card class="user-card" shadow="hover">
          <div class="user-avatar">
            <el-avatar :size="100" :src="userInfo.avatar">
              {{ userInfo.real_name?.charAt(0) || userInfo.username?.charAt(0) }}
            </el-avatar>
          </div>
          <div class="user-name">{{ userInfo.real_name || userInfo.username }}</div>
          <div class="user-role">
            <el-tag :type="roleTagType" size="small">{{ roleLabel }}</el-tag>
          </div>
          <div class="user-info-list">
            <div class="info-item">
              <span class="info-label">用户名</span>
              <span class="info-value">{{ userInfo.username || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">学号/工号</span>
              <span class="info-value">{{ userInfo.student_id || userInfo.teacher_id || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">邮箱</span>
              <span class="info-value">{{ userInfo.email || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">电话</span>
              <span class="info-value">{{ userInfo.phone || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">院系</span>
              <span class="info-value">{{ userInfo.department || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">注册时间</span>
              <span class="info-value">{{ formatTime(userInfo.created_at) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 修改密码卡片 -->
      <el-col :span="16">
        <el-card class="password-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">修改密码</span>
            </div>
          </template>
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="100px"
            class="password-form"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="请输入原密码"
                show-password
                autocomplete="current-password"
              />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码"
                show-password
                autocomplete="new-password"
              />
              <div class="password-tip">密码长度为 8-20 位，需包含字母和数字</div>
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
                autocomplete="new-password"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="handleSubmit">
                确认修改
              </el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 基本信息编辑卡片 -->
        <el-card class="info-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">基本信息</span>
              <el-button type="primary" link v-if="!editing" @click="editing = true">
                编辑
              </el-button>
            </div>
          </template>
          <el-form
            v-if="editing"
            ref="infoFormRef"
            :model="infoForm"
            :rules="infoRules"
            label-width="100px"
            class="info-form"
          >
            <el-form-item label="姓名" prop="real_name">
              <el-input v-model="infoForm.real_name" placeholder="请输入姓名" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="infoForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="电话" prop="phone">
              <el-input v-model="infoForm.phone" placeholder="请输入电话" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="infoSubmitting" @click="handleInfoSubmit">
                保存
              </el-button>
              <el-button @click="cancelEdit">取消</el-button>
            </el-form-item>
          </el-form>
          <div v-else class="info-display">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="姓名">{{ userInfo.real_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="角色">{{ roleLabel }}</el-descriptions-item>
              <el-descriptions-item label="邮箱">{{ userInfo.email || '-' }}</el-descriptions-item>
              <el-descriptions-item label="电话">{{ userInfo.phone || '-' }}</el-descriptions-item>
              <el-descriptions-item label="院系" :span="2">{{ userInfo.department || '-' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'
import request from '@/utils/request'
import dayjs from 'dayjs'

const userStore = useUserStore()
const userInfo = ref({})
const editing = ref(false)
const submitting = ref(false)
const infoSubmitting = ref(false)
const passwordFormRef = ref(null)
const infoFormRef = ref(null)

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const infoForm = reactive({
  real_name: '',
  email: '',
  phone: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 20, message: '密码长度为 8-20 位', trigger: 'blur' },
    {
      pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,20}$/,
      message: '密码需包含字母和数字',
      trigger: 'blur'
    }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const infoRules = {
  real_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const roleLabel = computed(() => {
  const roleMap = {
    admin: '管理员',
    teacher: '教师',
    student: '学生'
  }
  return roleMap[userInfo.value.role] || userInfo.value.role || '-'
})

const roleTagType = computed(() => {
  const typeMap = {
    admin: 'danger',
    teacher: 'primary',
    student: 'success'
  }
  return typeMap[userInfo.value.role] || 'info'
})

const formatTime = (time) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'
}

const loadUserInfo = async () => {
  try {
    const res = await request.get('/auth/me')
    userInfo.value = res
    infoForm.real_name = res.real_name || ''
    infoForm.email = res.email || ''
    infoForm.phone = res.phone || ''
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

const handleSubmit = async () => {
  if (!passwordFormRef.value) return
  try {
    await passwordFormRef.value.validate()
    submitting.value = true
    await request.put(`/users/${userInfo.value.id}/password`, {
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    ElMessage.success('密码修改成功')
    handleReset()
  } catch (error) {
    if (error !== false) {
      console.error('修改密码失败:', error)
    }
  } finally {
    submitting.value = false
  }
}

const handleReset = () => {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  passwordFormRef.value?.resetFields()
}

const handleInfoSubmit = async () => {
  if (!infoFormRef.value) return
  try {
    await infoFormRef.value.validate()
    infoSubmitting.value = true
    const res = await request.put(`/users/${userInfo.value.id}`, infoForm)
    userInfo.value = { ...userInfo.value, ...res }
    userStore.userInfo = { ...userStore.userInfo, ...res }
    localStorage.setItem('userInfo', JSON.stringify(userStore.userInfo))
    ElMessage.success('信息更新成功')
    editing.value = false
  } catch (error) {
    if (error !== false) {
      console.error('更新信息失败:', error)
    }
  } finally {
    infoSubmitting.value = false
  }
}

const cancelEdit = () => {
  editing.value = false
  infoForm.real_name = userInfo.value.real_name || ''
  infoForm.email = userInfo.value.email || ''
  infoForm.phone = userInfo.value.phone || ''
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped lang="scss">
.profile-page {
  .user-card {
    text-align: center;

    .user-avatar {
      margin-bottom: 16px;
    }

    .user-name {
      font-size: 20px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }

    .user-role {
      margin-bottom: 20px;
    }

    .user-info-list {
      text-align: left;
      border-top: 1px solid #ebeef5;
      padding-top: 16px;

      .info-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        font-size: 13px;

        .info-label {
          color: #909399;
        }

        .info-value {
          color: #303133;
          max-width: 60%;
          text-align: right;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
  }

  .password-card,
  .info-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .card-title {
        font-size: 15px;
        font-weight: 600;
        color: #303133;
      }
    }

    .password-form,
    .info-form {
      max-width: 500px;

      .password-tip {
        font-size: 12px;
        color: #909399;
        margin-top: 4px;
      }
    }

    .info-display {
      padding: 0 10px;
    }
  }
}
</style>
