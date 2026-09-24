<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: appStore.sidebarCollapsed }">
      <div class="logo">
        <el-icon size="28" :color="themeVars.logoColor"><DataAnalysis /></el-icon>
        <span v-show="!appStore.sidebarCollapsed" class="logo-text">论文质量监控</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        :background-color="themeVars.sidebarBg"
        :text-color="themeVars.sidebarText"
        :active-text-color="themeVars.sidebarActiveText"
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
 <el-breadcrumb-item :to="{ path: homePath }">首页</el-breadcrumb-item>
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

// 教师/管理员端主题变量（清新浅色主题 - 柔和蓝绿色系）
const themeVars = {
  primary: '#0ea5e9',
  primaryLight: '#38bdf8',
  primaryLighter: '#e0f2fe',
  sidebarBg: '#ffffff',
  sidebarLogoBg: '#f8fafc',
  sidebarText: '#64748b',
  sidebarActiveText: '#0ea5e9',
  sidebarActiveBg: '#e0f2fe',
  logoColor: '#0ea5e9',
}

const activeMenu = computed(() => route.path)
const currentPageTitle = computed(() => route.meta.title || '')

const roleText = computed(() => {
  const roleMap = {
    admin: '管理员',
    teacher: '教师'
  }
  return roleMap[userStore.userInfo?.role] || userStore.userInfo?.role
})

// 菜单列表 - 按角色过滤
const menuList = computed(() => {
  const role = userStore.userInfo?.role
  const allMenus = [
    { path: 'dashboard', title: '数据看板', icon: 'DataAnalysis', roles: ['admin', 'teacher'] },
    { path: 'topics', title: '选题管理', icon: 'Document', roles: ['admin', 'teacher'] },
    { path: 'proposals', title: '开题管理', icon: 'Files', roles: ['admin', 'teacher'] },
    { path: 'midterm', title: '中期检查', icon: 'CircleCheck', roles: ['admin', 'teacher'] },
    { path: 'guidance', title: '过程指导', icon: 'ChatDotRound', roles: ['admin', 'teacher'] },
    {
      path: 'thesis',
      title: '论文版本',
      icon: 'DocumentCopy',
      roles: ['admin', 'teacher'],
      children: [
        { path: 'draft1', title: '论文一稿', icon: 'Document' },
        { path: 'draft2', title: '论文二稿', icon: 'Document' },
        { path: 'final', title: '论文终审', icon: 'DocumentChecked' }
      ]
    },
    {
      path: 'reviews',
      title: '评阅答辩',
      icon: 'EditPen',
      roles: ['admin', 'teacher'],
      children: [
        { path: 'review', title: '论文评阅', icon: 'Reading' },
        { path: 'defense', title: '答辩评价', icon: 'ChatLineSquare' }
      ]
    },
    { path: 'anomaly', title: '异常检测', icon: 'Warning', roles: ['admin', 'teacher'] },
    { path: 'archives', title: '成果归档', icon: 'Box', roles: ['admin', 'teacher'] },
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
        { path: 'logs', title: '操作日志', icon: 'List' },
        { path: 'stages', title: '阶段时间设定', icon: 'Timer' }
      ]
    })
  }

  return menus
})

// 首页路径
const homePath = computed(() => {
  return '/dashboard'
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
  /* 教师/管理员端主题令牌 - 清新浅色主题 */
  --primary: #0ea5e9;
  --primary-light: #38bdf8;
  --primary-lighter: #e0f2fe;
  --sidebar-bg: #ffffff;
  --sidebar-logo-bg: #f8fafc;
  --sidebar-text: #64748b;
  --sidebar-active-text: #0ea5e9;
  --sidebar-active-bg: #e0f2fe;
  --sidebar-hover-bg: #f1f5f9;

  /* 覆盖 Element Plus 主色为天蓝 */
  --el-color-primary: #0ea5e9;
  --el-color-primary-light-3: #38bdf8;
  --el-color-primary-light-5: #7dd3fc;
  --el-color-primary-light-7: #bae6fd;
  --el-color-primary-light-8: #e0f2fe;
  --el-color-primary-light-9: #f0f9ff;
  --el-color-primary-dark-2: #0284c7;

  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  border-right: 1px solid #e2e8f0;
  transition: width 0.3s;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.03);

  &.collapsed {
    width: var(--sidebar-collapsed-width);
  }

  .logo {
    height: var(--header-height);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: var(--sidebar-logo-bg);
    color: var(--primary);
    font-size: 16px;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    border-bottom: 1px solid #e2e8f0;

    .logo-text {
      font-size: 15px;
      letter-spacing: 0.5px;
    }
  }

  .sidebar-menu {
    flex: 1;
    border-right: none;

    :deep(.el-menu-item),
    :deep(.el-sub-menu__title) {
      height: 50px;
      line-height: 50px;
      transition: var(--transition-base);
      margin: 4px 12px;
      border-radius: 8px;
      width: auto;

      &:hover {
        background-color: var(--sidebar-hover-bg) !important;
      }
    }

    :deep(.el-menu-item.is-active) {
      background-color: var(--sidebar-active-bg) !important;
      color: var(--sidebar-active-text) !important;
      font-weight: 600;
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
  height: var(--header-height);
  background: var(--bg-card);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .toggle-btn {
      font-size: 20px;
      cursor: pointer;
      color: var(--color-text-regular);
      transition: var(--transition-base);

      &:hover {
        color: var(--primary);
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
      border-radius: var(--radius-sm);
      transition: var(--transition-base);

      &:hover {
        background: var(--color-fill);
      }

      .username {
        font-size: 14px;
        color: var(--color-text-primary);
      }
    }
  }
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--bg-page);
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
