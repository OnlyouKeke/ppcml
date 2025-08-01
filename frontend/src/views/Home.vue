<template>
  <div class="home-container">
    <el-card class="card" header="FastAPI 通信测试">
      <div class="card-content">
        <el-alert v-if="mainStore.error" type="error" :title="mainStore.error" show-icon />
        
        <el-result
          v-if="mainStore.apiMessage"
          icon="success"
          :sub-title="mainStore.apiMessage"
        />
        
        <div class="input-section">
          <el-input
            v-model="name"
            placeholder="请输入你的名字"
            clearable
            :disabled="mainStore.loading"
          />
          
          <div class="button-group">
            <el-button type="primary" @click="handleHello" :loading="mainStore.loading">
              获取问候
            </el-button>
            
            <el-button @click="handleRoot" :loading="mainStore.loading">
              获取根路径数据
            </el-button>
            
            <el-button type="danger" @click="mainStore.resetState">
              重置
            </el-button>
          </div>
        </div>
        
        <el-divider />
        
        <div class="info-section">
          <h3>Electron + FastAPI + Vue3 通信架构</h3>
          <p>这是一个使用 Electron、FastAPI 和 Vue3 构建的应用程序示例。</p>
          <p>前端使用 Vue3 + TypeScript + Pinia + Element Plus 构建。</p>
          <p>后端使用 FastAPI 提供 API 服务。</p>
          <p>Electron 负责将两者整合为桌面应用。</p>
        </div>
      </div>
    </el-card>
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
  padding: 0;
  height: 100%;
}

.card {
  width: 100%;
  max-width: 800px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}

.card :deep(.el-card__header) {
  background-color: #f0f5ff;
  color: #1890ff;
  font-weight: bold;
  border-bottom: 1px solid #e6f7ff;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px 0;
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 5px;
}

.info-section {
  margin-top: 10px;
  color: #606266;
  background-color: #fafafa;
  padding: 15px;
  border-radius: 4px;
}

.info-section h3 {
  margin-bottom: 10px;
  color: #303133;
  font-size: 16px;
}

.info-section p {
  margin: 5px 0;
  line-height: 1.6;
}
</style>