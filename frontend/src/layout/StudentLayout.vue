<template>
  <div class="student-layout">
    <div class="sidebar" :class="{ collapsed: collapsed }">
      <div class="logo">
        <el-icon size="24" :color="themeVars.logoColor"><Reading /></el-icon>
        <span v-show="!collapsed" class="logo-text">论文管理系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        :background-color="themeVars.sidebarBg"
        :text-color="themeVars.sidebarText"
        :active-text-color="themeVars.sidebarActiveText"
        :collapse="collapsed"
        :collapse-transition="false"
        router
      >
        <el-menu-item index="/student/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>
        <el-menu-item index="/student/topics">
          <el-icon><Document /></el-icon>
          <template #title>选题确认</template>
        </el-menu-item>
        <el-menu-item index="/student/proposals">
          <el-icon><Files /></el-icon>
          <template #title>开题报告</template>
        </el-menu-item>
        <el-menu-item index="/student/midterm">
          <el-icon><CircleCheck /></el-icon>
          <template #title>中期检查</template>
        </el-menu-item>
        <el-menu-item index="/student/guidance">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>过程指导</template>
        </el-menu-item>
        <el-sub-menu index="/student/thesis">
          <template #title>
            <el-icon><DocumentCopy /></el-icon>
            <span>论文版本</span>
          </template>
          <el-menu-item index="/student/thesis/draft1">
            <el-icon><Document /></el-icon>
            <template #title>论文一稿</template>
          </el-menu-item>
          <el-menu-item index="/student/thesis/draft2">
            <el-icon><Document /></el-icon>
            <template #title>论文二稿</template>
          </el-menu-item>
          <el-menu-item index="/student/thesis/final">
            <el-icon><DocumentChecked /></el-icon>
            <template #title>论文终审</template>
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/student/reviews">
          <template #title>
            <el-icon><EditPen /></el-icon>
            <span>评阅答辩</span>
          </template>
          <el-menu-item index="/student/reviews/review">
            <el-icon><Reading /></el-icon>
            <template #title>论文评阅</template>
          </el-menu-item>
          <el-menu-item index="/student/reviews/defense">
            <el-icon><ChatLineSquare /></el-icon>
            <template #title>答辩评价</template>
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/student/archives">
          <el-icon><Box /></el-icon>
          <template #title>成果归档</template>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="main-container">
      <div class="header">
        <div class="header-left">
          <el-icon class="toggle-btn" @click="collapsed = !collapsed">
            <Fold v-if="!collapsed" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/student/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ pageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" :src="userStore.userInfo?.avatar">
                {{ userStore.username?.charAt(0) }}
              </el-avatar>
              <span class="username">{{ userStore.userInfo?.real_name }}</span>
              <el-tag size="small" type="success" effect="plain">学生</el-tag>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessageBox, ElMessage } from 'element-plus'
import studentApi from '@/api/student'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(false)

// 学生端主题变量（清新浅色主题 - 柔和蓝绿色系）
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
const pageTitle = computed(() => route.meta.title || '')
const menuTitles = {
  '/student/dashboard': '工作台',
  '/student/topics': '选题确认',
  '/student/proposals': '开题报告',
  '/student/midterm': '中期检查',
  '/student/guidance': '过程指导',
  '/student/thesis': '论文版本',
  '/student/reviews': '评阅答辩',
  '/student/anomaly': '异常提示',
  '/student/archives': '成果归档',
  '/student/profile': '个人中心'
}

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/student/profile')
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

onMounted(() => {
})
</script>

<style scoped lang="scss">
.student-layout {
  /* 学生端主题令牌 - 清新浅色主题 */
  --primary: #0ea5e9;
  --primary-light: #38bdf8;
  --primary-lighter: #e0f2fe;
  --sidebar-bg: #ffffff;
  --sidebar-logo-bg: #f8fafc;
  --sidebar-text: #64748b;
  --sidebar-active-text: #0ea5e9;
  --sidebar-active-bg: #e0f2fe;
  --sidebar-hover-bg: #f1f5f9;

  /* 覆盖 Element Plus 主色为学生端天蓝 */
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
    font-size: 15px;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    border-bottom: 1px solid #e2e8f0;
  }

  .sidebar-menu {
    flex: 1;
    border-right: none;

    :deep(.el-menu-item) {
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

    :deep(.el-sub-menu__title) {
      margin: 4px 12px;
      border-radius: 8px;
      height: 50px;
      line-height: 50px;

      &:hover {
        background-color: var(--sidebar-hover-bg) !important;
      }
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
      &:hover { color: var(--primary); }
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
      &:hover { background: var(--color-fill); }
      .username { font-size: 14px; color: var(--color-text-primary); }
    }
  }
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--bg-page);
}

.menu-badge {
  margin-left: 8px;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
