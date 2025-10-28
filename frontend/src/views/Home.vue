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

            <el-button type="danger" @click="handleReset">
              重置
            </el-button>
          </div>
        </div>

        <el-divider />

        <div class="detection-section">
          <h3>YOLO 目标检测</h3>
          <p class="section-tip">上传图片后调用后端 YOLO 模型并显示检测结果。</p>

          <el-alert
            v-if="mainStore.detectionError"
            type="error"
            :title="mainStore.detectionError"
            show-icon
            class="section-alert"
          />

          <div class="upload-group">
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              class="file-input"
              :disabled="mainStore.detectionLoading"
              @change="handleFileChange"
            />

            <div class="upload-actions">
              <el-button
                type="primary"
                :disabled="!selectedFile"
                :loading="mainStore.detectionLoading"
                @click="handleDetect"
              >
                开始检测
              </el-button>
              <el-button
                :disabled="!selectedFile && !imagePreviewUrl"
                @click="clearSelection"
              >
                清除
              </el-button>
            </div>
          </div>

          <div v-if="imagePreviewUrl" class="preview-wrapper">
            <el-image
              :src="imagePreviewUrl"
              fit="contain"
              :preview-src-list="[imagePreviewUrl]"
              preview-teleported
              class="preview-image"
            />
          </div>

          <el-skeleton v-if="mainStore.detectionLoading" animated :rows="3" />

          <template v-else>
            <el-table
              v-if="mainStore.detections.length"
              :data="mainStore.detections"
              border
              size="small"
              class="result-table"
            >
              <el-table-column prop="class_name" label="类别" min-width="120" />
              <el-table-column label="置信度" min-width="120">
                <template #default="{ row }">
                  {{ formatConfidence(row.confidence) }}
                </template>
              </el-table-column>
              <el-table-column label="边界框" min-width="220">
                <template #default="{ row }">
                  {{ formatBox(row.box) }}
                </template>
              </el-table-column>
            </el-table>

            <el-empty
              v-else-if="selectedFile"
              description="未检测到目标"
              class="result-empty"
            />
          </template>
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
import { ref, onBeforeUnmount } from 'vue'
import { useMainStore } from '../store'
import type { Detection } from '../store'

// 使用Pinia存储
const mainStore = useMainStore()

// 输入的名字
const name = ref('')

const selectedFile = ref<File | null>(null)
const imagePreviewUrl = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const handleHello = () => {
  mainStore.fetchHelloData(name.value)
}

const handleRoot = () => {
  mainStore.fetchRootData()
}

const handleReset = () => {
  mainStore.resetState()
  clearSelection()
  name.value = ''
}

const revokePreviewUrl = () => {
  if (imagePreviewUrl.value) {
    URL.revokeObjectURL(imagePreviewUrl.value)
    imagePreviewUrl.value = ''
  }
}

const clearSelection = () => {
  revokePreviewUrl()
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  mainStore.resetDetection()
}

const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  mainStore.resetDetection()
  revokePreviewUrl()

  if (!file) {
    selectedFile.value = null
    return
  }

  selectedFile.value = file
  imagePreviewUrl.value = URL.createObjectURL(file)
}

const handleDetect = async () => {
  if (!selectedFile.value) {
    mainStore.detectionError = '请先选择图片文件'
    return
  }

  await mainStore.detectImage(selectedFile.value)
}

const formatConfidence = (value: number) => `${(value * 100).toFixed(1)}%`

const formatBox = (box: Detection['box']) =>
  `(${box.xmin.toFixed(1)}, ${box.ymin.toFixed(1)}) - (${box.xmax.toFixed(1)}, ${box.ymax.toFixed(1)})`

onBeforeUnmount(() => {
  revokePreviewUrl()
})
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
  max-width: 900px;
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

.detection-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-tip {
  color: #606266;
  font-size: 13px;
}

.section-alert {
  max-width: 400px;
}

.upload-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-input {
  padding: 6px 0;
}

.upload-actions {
  display: flex;
  gap: 10px;
}

.preview-wrapper {
  display: flex;
  justify-content: flex-start;
}

.preview-image {
  max-width: 360px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  padding: 6px;
  background-color: #fafafa;
}

.result-table {
  max-width: 100%;
}

.result-empty {
  padding: 10px 0;
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
