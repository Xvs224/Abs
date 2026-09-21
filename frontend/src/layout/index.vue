<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: appStore.sidebarCollapsed }">
      <div class="logo">
        <el-icon size="28" color="#fff"><DataAnalysis /></el-icon>
        <span v-show="!appStore.sidebarCollapsed" class="logo-text">论文质量监控</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#1f2d3d"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        router
      >
        <template v-for="item in menuList" :key="item.path">
          <el-sub-menu v-if="item.children" :index="item.path">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item
              v-for="child in item.children"
              :key="child.path"
              :index="`/${item.path}/${child.path}`"
            >
              <el-icon><component :is="child.icon" /></el-icon>
              <span>{{ child.title }}</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="`/${item.path}`">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </div>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 顶部导航栏 -->
      <div class="header">
        <div class="header-left">
          <el-icon class="toggle-btn" @click="appStore.toggleSidebar()">
            <Fold v-if="!appStore.sidebarCollapsed" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" :src="userStore.userInfo?.avatar">
                {{ userStore.username?.charAt(0) }}
              </el-avatar>
              <span class="username">{{ userStore.username }}</span>
              <el-tag size="small" type="info" effect="plain">{{ roleText }}</el-tag>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 内容区 -->
      <div class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { useAppStore } from '@/store/app'
import { ElMessageBox, ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const activeMenu = computed(() => route.path)
const currentPageTitle = computed(() => route.meta.title || '')

const roleText = computed(() => {
  const roleMap = {
    admin: '管理员',
    teacher: '教师',
    student: '学生'
  }
  return roleMap[userStore.userInfo?.role] || userStore.userInfo?.role
})

// 菜单列表 - 按角色过滤
const menuList = computed(() => {
  const role = userStore.userInfo?.role
  const allMenus = [
    { path: 'dashboard', title: '数据看板', icon: 'DataAnalysis', roles: ['admin', 'teacher', 'student'] },
    { path: 'topics', title: '选题管理', icon: 'Document', roles: ['admin', 'teacher', 'student'] },
    { path: 'proposals', title: '开题管理', icon: 'Files', roles: ['admin', 'teacher', 'student'] },
    { path: 'guidance', title: '过程指导', icon: 'ChatDotRound', roles: ['admin', 'teacher', 'student'] },
    { path: 'midterm', title: '中期检查', icon: 'CircleCheck', roles: ['admin', 'teacher', 'student'] },
    { path: 'thesis', title: '论文版本', icon: 'DocumentCopy', roles: ['admin', 'teacher', 'student'] },
    { path: 'reviews', title: '评阅答辩', icon: 'EditPen', roles: ['admin', 'teacher', 'student'] },
    { path: 'anomaly', title: '异常检测', icon: 'Warning', roles: ['admin', 'teacher', 'student'] },
    { path: 'archives', title: '成果归档', icon: 'Box', roles: ['admin', 'teacher', 'student'] },
  ]

  const menus = allMenus.filter(m => !m.roles || m.roles.includes(role))

  if (role === 'admin') {
    menus.push({
      path: 'system',
      title: '系统管理',
      icon: 'Setting',
      roles: ['admin'],
      children: [
        { path: 'users', title: '用户管理', icon: 'UserFilled' },
        { path: 'logs', title: '操作日志', icon: 'List' }
      ]
    })
  }

  return menus
})

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    }).catch(() => {})
  }
}
</script>

<style scoped lang="scss">
.layout-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 220px;
  background: #1f2d3d;
  transition: width 0.3s;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;

  &.collapsed {
    width: 64px;
  }

  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: #17202a;
    color: #fff;
    font-size: 16px;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;

    .logo-text {
      font-size: 15px;
    }
  }

  .sidebar-menu {
    flex: 1;
    border-right: none;

    :deep(.el-menu-item),
    :deep(.el-sub-menu__title) {
      height: 50px;
      line-height: 50px;
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .toggle-btn {
      font-size: 20px;
      cursor: pointer;
      color: #606266;

      &:hover {
        color: #409eff;
      }
    }
  }

  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      padding: 5px 10px;
      border-radius: 4px;
      transition: background 0.2s;

      &:hover {
        background: #f5f7fa;
      }

      .username {
        font-size: 14px;
        color: #303133;
      }
    }
  }
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
