import axios from 'axios'
import type { ApiResponse, DetectionResponse } from '../types/api'

// 判断是否在Electron环境中
const isElectron = window.navigator.userAgent.toLowerCase().indexOf('electron') > -1

// 创建axios实例
const api = axios.create({
  // 在Electron环境中直接使用FastAPI的URL，否则使用代理
  // 开发模式使用8001端口，生产模式使用8000端口
  baseURL: isElectron
    ? process.env.NODE_ENV === 'development'
      ? 'http://localhost:8001'
      : 'http://localhost:8000'
    : '/api',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加认证信息等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    // 处理错误响应
    if (error.response) {
      // 服务器返回了错误状态码
      console.error('API错误:', error.response.data)
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('网络错误:', error.request)
    } else {
      // 请求设置时发生错误
      console.error('请求错误:', error.message)
    }
    return Promise.reject(error)
  }
)

// API函数

// 获取根路径数据
export const getRoot = async (): Promise<ApiResponse> => {
  return await api.get('/')
}

// 获取问候数据
export const getHello = async (name: string): Promise<ApiResponse> => {
  return await api.get(`/hello/${name}`)
}

// 上传图片并进行目标检测
export const postDetect = async (file: File): Promise<DetectionResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  return await api.post('/detect', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export default api
