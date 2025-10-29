import axios from 'axios'
import type { ApiResponse, DetectionResponse } from '../types/api'

type FileWithRelativePath = File & { webkitRelativePath?: string }

// 判断是否在Electron环境中
const isElectron = window.navigator.userAgent.toLowerCase().indexOf('electron') > -1

// 创建axios实例
console.info('[API] Running in electron:', isElectron)

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
    console.debug('[API] Sending request', {
      method: config.method,
      url: config.url,
      baseURL: config.baseURL,
      timeout: config.timeout,
      headers: config.headers
    })
    // 可以在这里添加认证信息等
    return config
  },
  error => {
    console.error('[API] Failed to prepare request', error)
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
    console.error('[API] Request failed', {
      message: error.message,
      code: error.code,
      config: error.config
    })
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

interface CtcReportPayload {
  files: FileWithRelativePath[]
  form: {
    petName: string
    ownerName: string
    age: string
    gender: string
    species: string
    notes: string
    sampleType?: string
    massLocation?: string
  }
  roundnessThreshold?: number
}

export const postGenerateCtcReport = async ({
  files,
  form,
  roundnessThreshold = 0.3
}: CtcReportPayload): Promise<Blob> => {
  const formData = new FormData()
  console.debug('[API] Preparing CTC report request', {
    fileCount: files.length,
    fileNames: files.map(file =>
      (file as FileWithRelativePath).webkitRelativePath || file.name
    ),
    form,
    roundnessThreshold
  })
  files.forEach(file => {
    const relativePath = (file as FileWithRelativePath).webkitRelativePath || file.name
    formData.append('files', file, relativePath)
  })

  formData.append('petName', form.petName || '')
  formData.append('ownerName', form.ownerName || '')
  formData.append('age', form.age || '')
  formData.append('gender', form.gender || '')
  formData.append('species', form.species || '')
  formData.append('notes', form.notes || '')
  formData.append('sampleType', form.sampleType || '')
  formData.append('massLocation', form.massLocation || '')
  formData.append('roundnessThreshold', String(roundnessThreshold))

  try {
    const response = await api.post('/ctc/report', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      responseType: 'blob'
    })

    console.debug('[API] Received CTC report response', {
      size: response.size,
      type: response.type
    })

    return response
  } catch (error) {
    console.error('[API] CTC report request failed', error)
    throw error
  }
}

export default api
