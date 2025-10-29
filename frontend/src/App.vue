<template>
  <el-config-provider>
    <div class="app-shell">
      <header class="app-header">
        <h1 class="app-title">宠物检测报告系统</h1>
        <p class="app-subtitle">整合宠物信息与识别结果，一键生成专业报告</p>
      </header>
      <main class="app-main">
        <router-view />
      </main>
      <footer class="app-footer">© {{ new Date().getFullYear() }} 宠物健康智能分析中心</footer>
    </div>
  </el-config-provider>
</template>

<script lang="ts" setup>
import { onMounted } from 'vue'

onMounted(() => {
  console.log('宠物检测报告系统已启动')
})
</script>

<style>
:root {
  --bg-gradient-start: #f1f5f9;
  --bg-gradient-end: #e0e7ff;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --panel-background: rgba(255, 255, 255, 0.92);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
}

body {
  font-family: 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
  color: var(--text-primary);
  background: linear-gradient(180deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
}

.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(16px);
}

.app-header {
  padding: 40px 32px 24px;
  text-align: center;
}

.app-title {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 12px;
}

.app-subtitle {
  color: var(--text-secondary);
  font-size: 16px;
}

.app-main {
  flex: 1;
  padding: 12px 16px 32px;
}

.app-footer {
  text-align: center;
  padding: 16px 0;
  color: #94a3b8;
  font-size: 13px;
}

@media (max-width: 768px) {
  .app-header {
    padding: 32px 16px 18px;
  }

  .app-title {
    font-size: 26px;
  }
}
</style>
