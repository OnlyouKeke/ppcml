import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getHello, getRoot } from '../api/api'

// 定义接口
export interface ApiResponse {
  message: string
  error?: string
}

// 创建主存储
export const useMainStore = defineStore('main', () => {
  // 状态
  const loading = ref(false)
  const apiMessage = ref('')
  const error = ref('')

  // 获取根路径数据
  const fetchRootData = async () => {
    loading.value = true
    error.value = ''
    
    try {
      const response = await getRoot()
      apiMessage.value = response.message
    } catch (err: any) {
      error.value = err.message || '获取数据失败'
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
      error.value = err.message || '获取数据失败'
      console.error('获取问候数据失败:', err)
    } finally {
      loading.value = false
    }
  }

  // 重置状态
  const resetState = () => {
    apiMessage.value = ''
    error.value = ''
  }

  return {
    loading,
    apiMessage,
    error,
    fetchRootData,
    fetchHelloData,
    resetState
  }
})