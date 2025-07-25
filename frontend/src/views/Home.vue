<template>
  <div class="home-container">
    <a-card class="card" title="FastAPI 通信测试">
      <a-space direction="vertical" size="large" fill>
        <a-alert v-if="mainStore.error" type="error" :content="mainStore.error" />
        
        <a-result
          v-if="mainStore.apiMessage"
          status="success"
          :subtitle="mainStore.apiMessage"
        />
        
        <a-space direction="vertical">
          <a-input
            v-model="name"
            placeholder="请输入你的名字"
            allow-clear
            :disabled="mainStore.loading"
          />
          
          <a-space>
            <a-button type="primary" @click="handleHello" :loading="mainStore.loading">
              获取问候
            </a-button>
            
            <a-button @click="handleRoot" :loading="mainStore.loading">
              获取根路径数据
            </a-button>
            
            <a-button status="danger" @click="mainStore.resetState">
              重置
            </a-button>
          </a-space>
        </a-space>
        
        <a-divider />
        
        <div class="info-section">
          <h3>Electron + FastAPI + Vue3 通信架构</h3>
          <p>这是一个使用 Electron、FastAPI 和 Vue3 构建的应用程序示例。</p>
          <p>前端使用 Vue3 + TypeScript + Pinia + Arco Design 构建。</p>
          <p>后端使用 FastAPI 提供 API 服务。</p>
          <p>Electron 负责将两者整合为桌面应用。</p>
        </div>
      </a-space>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useMainStore } from '../store'

// 使用Pinia存储
const mainStore = useMainStore()

// 输入的名字
const name = ref('')

// 处理获取问候数据
const handleHello = () => {
  mainStore.fetchHelloData(name.value)
}

// 处理获取根路径数据
const handleRoot = () => {
  mainStore.fetchRootData()
}
</script>

<style scoped>
.home-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 20px;
}

.card {
  width: 100%;
  max-width: 600px;
}

.info-section {
  margin-top: 20px;
  color: var(--color-text-2);
}

.info-section h3 {
  margin-bottom: 10px;
  color: var(--color-text-1);
}

.info-section p {
  margin: 5px 0;
}
</style>