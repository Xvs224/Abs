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
        <el-menu-item index="/student/profile">
          <el-icon><User /></el-icon>
          <template #title>个人中心</template>
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

// 学生端主题变量（清新、活力的青绿色系）
const themeVars = {
  primary: '#0d9488',
  primaryLight: '#14b8a6',
  primaryLighter: '#ccfbf1',
  sidebarBg: '#134e4a',
  sidebarLogoBg: '#042f2e',
  sidebarText: '#ccfbf1',
  sidebarActiveText: '#5eead4',
  sidebarActiveBg: 'rgba(20, 184, 166, 0.2)',
  logoColor: '#5eead4',
}

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta.title || '')
const menuTitles = {
  '/student/dashboard': '工作台',
  '/student/topics': '选题确认',
  '/student/proposals': '开题报告',
  '/student/midterm': '中期检查',
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
  /* 学生端主题令牌 - 清新青绿色系 */
  --primary: #0d9488;
  --primary-light: #14b8a6;
  --primary-lighter: #ccfbf1;
  --sidebar-bg: #134e4a;
  --sidebar-logo-bg: #042f2e;
  --sidebar-text: #ccfbf1;
  --sidebar-active-text: #5eead4;
  --sidebar-active-bg: rgba(20, 184, 166, 0.2);
  --sidebar-hover-bg: rgba(255, 255, 255, 0.06);

  /* 覆盖 Element Plus 主色为学生端青绿 */
  --el-color-primary: #0d9488;
  --el-color-primary-light-3: #3da39a;
  --el-color-primary-light-5: #6db8b0;
  --el-color-primary-light-7: #9ecdc7;
  --el-color-primary-light-8: #b6d8d4;
  --el-color-primary-light-9: #cee8e5;
  --el-color-primary-dark-2: #0a766d;

  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  transition: width 0.3s;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;

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
    color: #fff;
    font-size: 15px;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
  }

  .sidebar-menu {
    flex: 1;
    border-right: none;

    :deep(.el-menu-item) {
      height: 50px;
      line-height: 50px;
      transition: var(--transition-base);

      &:hover {
        background-color: var(--sidebar-hover-bg) !important;
      }
    }

    :deep(.el-menu-item.is-active) {
      background-color: var(--sidebar-active-bg) !important;
      border-right: 3px solid var(--sidebar-active-text);
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
