<template>
  <div class="about-container">
    <a-card class="card">
      <template #title>
        <div class="card-title">
          <a-avatar :size="64" class="avatar">
            <template #icon><icon-code-square /></template>
          </a-avatar>
          <h2>关于本应用</h2>
        </div>
      </template>
      
      <a-space direction="vertical" size="large">
        <a-typography>
          <a-typography-title :heading="4">技术栈</a-typography-title>
          <a-typography-paragraph>
            本应用使用以下技术栈构建：
          </a-typography-paragraph>
          
          <a-descriptions :data="techStack" layout="inline-vertical" bordered />
          
          <a-typography-title :heading="4" style="margin-top: 20px">架构说明</a-typography-title>
          <a-typography-paragraph>
            本应用采用前后端分离的架构，通过 Electron 将 FastAPI 后端与 Vue3 前端整合为一个桌面应用。
          </a-typography-paragraph>
          
          <a-typography-paragraph>
            <a-steps direction="vertical">
              <a-step title="前端 (Vue3)" description="负责用户界面和交互逻辑" />
              <a-step title="API通信" description="通过HTTP请求与后端通信" />
              <a-step title="后端 (FastAPI)" description="提供API服务和业务逻辑" />
              <a-step title="Electron" description="将前后端整合为桌面应用" />
            </a-steps>
          </a-typography-paragraph>
        </a-typography>
        
        <a-divider />
        
        <div class="footer-info">
          <p>版本: 1.0.0</p>
          <p>© {{ new Date().getFullYear() }} Electron + FastAPI + Vue3 示例应用</p>
        </div>
      </a-space>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { IconCodeSquare } from '@arco-design/web-vue/es/icon'

// 技术栈信息
const techStack = [
  {
    label: '前端框架',
    value: 'Vue 3 + TypeScript'
  },
  {
    label: '状态管理',
    value: 'Pinia'
  },
  {
    label: '路由',
    value: 'Vue Router 4'
  },
  {
    label: 'UI组件库',
    value: 'Arco Design Vue'
  },
  {
    label: '构建工具',
    value: 'Vite'
  },
  {
    label: '后端框架',
    value: 'FastAPI (Python)'
  },
  {
    label: '桌面应用框架',
    value: 'Electron'
  }
]
</script>

<style scoped>
.about-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 20px;
}

.card {
  width: 100%;
  max-width: 800px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  background-color: var(--color-primary-light-4);
}

.footer-info {
  text-align: center;
  color: var(--color-text-3);
  margin-top: 20px;
}
</style>