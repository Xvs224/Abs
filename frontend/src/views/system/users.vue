<template>
  <div class="system-users-page">
    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="角色">
          <el-select v-model="searchForm.role" placeholder="全部角色" clearable style="width: 140px">
            <el-option label="管理员" value="admin" />
            <el-option label="教师" value="teacher" />
            <el-option label="学生" value="student" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索用户名/姓名/学号"
            clearable
            style="width: 240px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card class="table-card" shadow="never">
      <div class="table-toolbar">
        <div class="toolbar-left">
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增用户</el-button>
          <el-button :icon="RefreshRight" @click="loadList">刷新</el-button>
        </div>
      </div>

      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="avatar" label="头像" width="70" align="center">
          <template #default="{ row }">
            <el-avatar :size="36" :src="row.avatar">
              {{ row.real_name?.charAt(0) || row.username?.charAt(0) }}
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="role" label="角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="student_id" label="学号/工号" width="120" />
        <el-table-column prop="department" label="院系" width="140" show-overflow-tooltip />
        <el-table-column prop="email" label="邮箱" width="180" show-overflow-tooltip />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              :active-value="1"
              :inactive-value="0"
              :active-text="''"
              :inactive-text="''"
              size="small"
              @change="(val) => handleStatusChange(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="warning" link size="small" @click="handleResetPassword(row)">
              重置密码
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="550px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="user-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="formData.real_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="教师" value="teacher" />
            <el-option label="学生" value="student" />
          </el-select>
        </el-form-item>
        <el-form-item label="学号/工号" prop="student_id">
          <el-input v-model="formData.student_id" placeholder="请输入学号或工号" />
        </el-form-item>
        <el-form-item label="院系" prop="department">
          <el-input v-model="formData.department" placeholder="请输入院系" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入电话" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入初始密码"
            show-password
          />
          <div class="form-tip">密码长度 8-20 位，需包含字母和数字</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, RefreshRight } from '@element-plus/icons-vue'
import { getUserList, createUser, updateUser, deleteUser, changePassword } from '@/api/user'
import dayjs from 'dayjs'

const loading = ref(false)
const dialogVisible = ref(false)
const dialogLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)

const tableData = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const searchForm = reactive({
  role: '',
  keyword: ''
})

const formData = reactive({
  id: null,
  username: '',
  real_name: '',
  role: 'student',
  student_id: '',
  department: '',
  email: '',
  phone: '',
  password: ''
})

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 30, message: '长度在 3 到 30 个字符', trigger: 'blur' }
  ],
  real_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { min: 8, max: 20, message: '密码长度为 8-20 位', trigger: 'blur' },
    {
      pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,20}$/,
      message: '密码需包含字母和数字',
      trigger: 'blur'
    }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '新增用户')

const roleLabel = (role) => {
  const map = { admin: '管理员', teacher: '教师', student: '学生' }
  return map[role] || role
}

const roleTagType = (role) => {
  const map = { admin: 'danger', teacher: 'primary', student: 'success' }
  return map[role] || 'info'
}

const formatTime = (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'

const loadList = async () => {
  loading.value = true
  try {
    const res = await getUserList({
      page: pagination.page,
      page_size: pagination.page_size,
      role: searchForm.role || undefined,
      keyword: searchForm.keyword || undefined
    })
    tableData.value = res.items || res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadList()
}

const handleReset = () => {
  searchForm.role = ''
  searchForm.keyword = ''
  pagination.page = 1
  loadList()
}

const resetForm = () => {
  formData.id = null
  formData.username = ''
  formData.real_name = ''
  formData.role = 'student'
  formData.student_id = ''
  formData.department = ''
  formData.email = ''
  formData.phone = ''
  formData.password = ''
  formRef.value?.resetFields()
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  formData.id = row.id
  formData.username = row.username
  formData.real_name = row.real_name
  formData.role = row.role
  formData.student_id = row.student_id || row.teacher_id || ''
  formData.department = row.department || ''
  formData.email = row.email || ''
  formData.phone = row.phone || ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    dialogLoading.value = true
    if (isEdit.value) {
      const { password, ...updateData } = formData
      await updateUser(formData.id, updateData)
      ElMessage.success('更新成功')
    } else {
      await createUser(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error)
    }
  } finally {
    dialogLoading.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除用户 "${row.username}" 吗？此操作不可恢复。`, '删除确认', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteUser(row.id)
      ElMessage.success('删除成功')
      loadList()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }).catch(() => {})
}

const handleResetPassword = (row) => {
  ElMessageBox.prompt(
    `请输入用户 "${row.username}" 的新密码`,
    '重置密码',
    {
      confirmButtonText: '确认重置',
      cancelButtonText: '取消',
      inputPattern: /^(?=.*[A-Za-z])(?=.*\d).{8,20}$/,
      inputErrorMessage: '密码长度 8-20 位，需包含字母和数字',
      inputType: 'password',
      type: 'warning'
    }
  ).then(async ({ value }) => {
    try {
      await changePassword(row.id, { new_password: value })
      ElMessage.success('密码重置成功')
    } catch (error) {
      console.error('重置密码失败:', error)
    }
  }).catch(() => {})
}

const handleStatusChange = (row, status) => {
  const action = status === 1 ? '启用' : '禁用'
  ElMessageBox.confirm(`确定要${action}用户 "${row.username}" 吗？`, '操作确认', {
    confirmButtonText: `确认${action}`,
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await updateUser(row.id, { status })
      ElMessage.success(`${action}成功`)
    } catch (error) {
      console.error('操作失败:', error)
      // 回滚状态
      row.status = status === 1 ? 0 : 1
    }
  }).catch(() => {
    // 回滚状态
    row.status = status === 1 ? 0 : 1
  })
}

onMounted(() => {
  loadList()
})
</script>

<style scoped lang="scss">
.system-users-page {
  .search-card {
    margin-bottom: 16px;
  }

  .table-card {
    .table-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: 20px;
    }
  }

  .user-form {
    padding-right: 20px;

    .form-tip {
      font-size: 12px;
      color: #909399;
      margin-top: 4px;
    }
  }
}
</style>
