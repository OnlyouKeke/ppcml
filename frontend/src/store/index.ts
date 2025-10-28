import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getHello, getRoot, postDetect } from '../api/api'
import type { ApiResponse, Detection } from '../types/api'

// 创建主存储
export const useMainStore = defineStore('main', () => {
  // 状态
  const loading = ref(false)
  const apiMessage = ref('')
  const error = ref('')

  const detectionLoading = ref(false)
  const detections = ref<Detection[]>([])
  const detectionError = ref('')

  // 获取根路径数据
  const fetchRootData = async () => {
    loading.value = true
    error.value = ''

    try {
      const response = await getRoot()
      apiMessage.value = response.message
    } catch (err: any) {
      error.value = err?.response?.data?.detail || err.message || '获取数据失败'
      console.error('获取根路径数据失败:', err)
    } finally {
      loading.value = false
    }
  }

  // 获取问候数据
  const fetchHelloData = async (name: string) => {
    if (!name.trim()) {
      error.value = '请输入名字'
      return
    }

    loading.value = true
    error.value = ''

    try {
      const response = await getHello(name)
      apiMessage.value = response.message
    } catch (err: any) {
      error.value = err?.response?.data?.detail || err.message || '获取数据失败'
      console.error('获取问候数据失败:', err)
    } finally {
      loading.value = false
    }
  }

  // 上传图片并执行目标检测
  const detectImage = async (file: File) => {
    detectionLoading.value = true
    detectionError.value = ''

    try {
      const response = await postDetect(file)
      detections.value = response.detections
    } catch (err: any) {
      detectionError.value = err?.response?.data?.detail || err.message || '检测失败'
      console.error('目标检测失败:', err)
      detections.value = []
    } finally {
      detectionLoading.value = false
    }
  }

  const resetDetection = () => {
    detections.value = []
    detectionError.value = ''
  }

  // 重置状态
  const resetState = () => {
    apiMessage.value = ''
    error.value = ''
    resetDetection()
  }

  return {
    loading,
    apiMessage,
    error,
    detectionLoading,
    detections,
    detectionError,
    fetchRootData,
    fetchHelloData,
    detectImage,
    resetDetection,
    resetState
  }
})

export type { ApiResponse, Detection } from '../types/api'
