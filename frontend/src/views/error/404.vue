<template>
  <div class="error-page">
    <div class="error-container">
      <div class="error-code">
        <span class="digit digit-4">4</span>
        <span class="digit digit-0">
          <span class="zero-inner">0</span>
        </span>
        <span class="digit digit-4">4</span>
      </div>
      <div class="error-title">页面走丢了</div>
      <div class="error-desc">
        抱歉，您访问的页面不存在或已被移除。
        <br />
        请检查您输入的地址是否正确，或返回首页继续浏览。
      </div>
      <div class="error-actions">
        <el-button type="primary" :icon="House" size="large" @click="goHome">
          返回首页
        </el-button>
        <el-button :icon="ArrowLeft" size="large" @click="goBack">
          返回上一页
        </el-button>
      </div>
      <div class="error-decoration">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
        <div class="circle circle-3"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { House, ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}
</script>

<style scoped lang="scss">
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;

  .error-container {
    text-align: center;
    color: #fff;
    position: relative;
    z-index: 10;
    padding: 40px;
  }

  .error-code {
    font-size: 160px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 20px;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
    text-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);

    .digit {
      display: inline-block;
      animation: bounce 2s ease-in-out infinite;

      &.digit-4 {
        &:first-child {
          animation-delay: 0s;
        }
        &:last-child {
          animation-delay: 0.4s;
        }
      }

      &.digit-0 {
        position: relative;
        width: 140px;
        height: 160px;
        animation-delay: 0.2s;

        .zero-inner {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 120px;
          height: 120px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.15);
          display: flex;
          align-items: center;
          justify-content: center;
          backdrop-filter: blur(10px);
          border: 2px solid rgba(255, 255, 255, 0.3);
        }
      }
    }
  }

  .error-title {
    font-size: 32px;
    font-weight: 600;
    margin-bottom: 16px;
    letter-spacing: 2px;
  }

  .error-desc {
    font-size: 15px;
    line-height: 1.8;
    opacity: 0.85;
    margin-bottom: 36px;
    max-width: 480px;
    margin-left: auto;
    margin-right: auto;
  }

  .error-actions {
    display: flex;
    gap: 16px;
    justify-content: center;

    .el-button {
      border-radius: 25px;
      padding: 0 32px;

      &.el-button--primary {
        background: #fff;
        color: #667eea;
        border: none;

        &:hover {
          background: rgba(255, 255, 255, 0.9);
          color: #667eea;
        }
      }

      &:not(.el-button--primary) {
        background: rgba(255, 255, 255, 0.15);
        color: #fff;
        border: 1px solid rgba(255, 255, 255, 0.3);

        &:hover {
          background: rgba(255, 255, 255, 0.25);
          color: #fff;
          border-color: rgba(255, 255, 255, 0.5);
        }
      }
    }
  }

  .error-decoration {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    overflow: hidden;
    z-index: 1;

    .circle {
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.08);

      &.circle-1 {
        width: 300px;
        height: 300px;
        top: -100px;
        left: -100px;
        animation: float 8s ease-in-out infinite;
      }

      &.circle-2 {
        width: 200px;
        height: 200px;
        bottom: -50px;
        right: -50px;
        animation: float 6s ease-in-out infinite reverse;
      }

      &.circle-3 {
        width: 150px;
        height: 150px;
        top: 40%;
        right: 10%;
        animation: float 10s ease-in-out infinite;
      }
    }
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(30px, -30px);
  }
}

@media (max-width: 768px) {
  .error-page {
    .error-code {
      font-size: 100px;

      .digit-0 {
        width: 90px;
        height: 100px;

        .zero-inner {
          width: 75px;
          height: 75px;
        }
      }
    }

    .error-title {
      font-size: 24px;
    }

    .error-desc {
      font-size: 14px;
    }

    .error-actions {
      flex-direction: column;
      align-items: center;

      .el-button {
        width: 200px;
      }
    }
  }
}
</style>
