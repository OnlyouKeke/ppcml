<template>
  <a-config-provider>
    <div class="app-container">
      <a-layout>
        <a-layout-header class="header">
          <div class="logo">Electron + FastAPI + Vue3</div>
          <a-menu
            mode="horizontal"
            :selected-keys="[activeRoute]"
            @menu-item-click="handleMenuClick"
          >
            <a-menu-item key="home">首页</a-menu-item>
            <a-menu-item key="about">关于</a-menu-item>
          </a-menu>
        </a-layout-header>
        
        <a-layout-content class="content">
          <router-view />
        </a-layout-content>
        
        <a-layout-footer class="footer">
          Electron + FastAPI + Vue3 示例应用 &copy; {{ new Date().getFullYear() }}
        </a-layout-footer>
      </a-layout>
    </div>
  </a-config-provider>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 当前活动路由
const activeRoute = computed(() => {
  return route.name as string
})

// 处理菜单点击
const handleMenuClick = (key: string) => {
  router.push({ name: key })
}

onMounted(() => {
  console.log('应用已加载')
})
</script>

<style>
.app-container {
  height: 100vh;
  width: 100%;
}

.header {
  display: flex;
  align-items: center;
  background-color: var(--color-bg-2);
  padding: 0 20px;
}

.logo {
  font-size: 18px;
  font-weight: bold;
  margin-right: 40px;
  color: var(--color-text-1);
}

.content {
  padding: 20px;
  background-color: var(--color-bg-1);
}

.footer {
  text-align: center;
  color: var(--color-text-3);
  background-color: var(--color-bg-2);
}
</style>