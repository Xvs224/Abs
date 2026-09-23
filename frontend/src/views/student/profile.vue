<template>
  <div class="student-profile">
    <el-row :gutter="20">
      <el-col :span="10">
        <el-card shadow="never">
          <template #header>
            <span class="card-title">个人信息</span>
          </template>
          <div class="user-card">
            <el-avatar :size="80" :src="userInfo?.avatar">
              {{ userInfo?.real_name?.charAt(0) || '学' }}
            </el-avatar>
            <div class="user-name">{{ userInfo?.real_name || '-' }}</div>
            <el-tag type="success" size="small">学生</el-tag>
          </div>
          <el-descriptions :column="1" border size="small" class="user-descriptions">
            <el-descriptions-item label="用户名">{{ userInfo?.username || '-' }}</el-descriptions-item>
            <el-descriptions-item label="学号">{{ userInfo?.student_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ userInfo?.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="电话">{{ userInfo?.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="院系">{{ userInfo?.department || '-' }}</el-descriptions-item>
            <el-descriptions-item label="专业">{{ userInfo?.major || '-' }}</el-descriptions-item>
            <el-descriptions-item label="年级">{{ userInfo?.grade || '-' }}</el-descriptions-item>
          </el-descriptions>
          <el-button type="primary" plain style="margin-top: 16px;" @click="openEdit">编辑信息</el-button>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            <span class="card-title">修改密码</span>
          </template>
          <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="100px" style="max-width: 400px;">
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入原密码" />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="请输入新密码" />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="pwdForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleChangePassword" :loading="changingPwd">修改密码</el-button>
              <el-button @click="resetPwdForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="editVisible" title="编辑个人信息" width="500px">
      <el-form ref="editFormRef" :model="editForm" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="editForm.real_name" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        <el-form-item label="院系">
          <el-input v-model="editForm.department" />
        </el-form-item>
        <el-form-item label="专业">
          <el-input v-model="editForm.major" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import studentApi from '@/api/student'

const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)

const pwdFormRef = ref(null)
const editFormRef = ref(null)
const editVisible = ref(false)
const changingPwd = ref(false)

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const editForm = reactive({
  real_name: '',
  email: '',
  phone: '',
  department: '',
  major: ''
})

const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== pwdForm.new_password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

const openEdit = () => {
  Object.assign(editForm, {
    real_name: userInfo.value?.real_name || '',
    email: userInfo.value?.email || '',
    phone: userInfo.value?.phone || '',
    department: userInfo.value?.department || '',
    major: userInfo.value?.major || ''
  })
  editVisible.value = true
}

const handleSaveEdit = async () => {
  try {
    await studentApi.updateMyInfo(userInfo.value.id, editForm)
    await userStore.getUserInfo()
    ElMessage.success('信息已更新')
    editVisible.value = false
  } catch (e) { /* silent */ }
}

const handleChangePassword = async () => {
  await pwdFormRef.value.validate()
  changingPwd.value = true
  try {
    await studentApi.changePassword(userInfo.value.id, {
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password
    })
    ElMessage.success('密码已修改')
    resetPwdForm()
  } catch (e) { /* silent */ }
  finally { changingPwd.value = false }
}

const resetPwdForm = () => {
  Object.assign(pwdForm, { old_password: '', new_password: '', confirm_password: '' })
}

onMounted(() => {
  if (!userInfo.value) {
    userStore.getUserInfo()
  }
})
</script>

<style scoped lang="scss">
.card-title {
  font-size: 16px;
  font-weight: 600;
}

.user-card {
  text-align: center;
  margin-bottom: 20px;

  .user-name {
    font-size: 18px;
    font-weight: 600;
    margin: 12px 0 8px;
    color: #303133;
  }
}

.user-descriptions {
  margin-top: 12px;
}
</style>
