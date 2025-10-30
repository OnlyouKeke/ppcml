import axios, { isAxiosError } from 'axios'
import type {
  ApiResponse,
  CtcReportResponse,
  DetectionResponse,
  HeartbeatResponse
} from '../types/api'

type FileWithRelativePath = File & { webkitRelativePath?: string }

const runtime = window.appRuntime
const isElectron = Boolean(runtime?.isElectron)
const backendUrl = runtime?.backend?.url

const fallbackPort = process.env.NODE_ENV === 'development' ? '8001' : '8000'
const defaultBackendUrl = `http://127.0.0.1:${fallbackPort}`

// 创建axios实例
console.info('[API] Running in electron:', isElectron)
console.info('[API] Backend URL resolved to:', isElectron ? backendUrl ?? defaultBackendUrl : '/api')

const api = axios.create({
  // 在Electron环境中直接使用FastAPI的URL，否则使用代理
  baseURL: isElectron ? backendUrl ?? defaultBackendUrl : '/api',
  timeout: 600000,
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
    const serializedConfig = {
      baseURL: error.config?.baseURL,
      url: error.config?.url,
      method: error.config?.method,
      timeout: error.config?.timeout,
      headers: error.config?.headers
    }

    console.error('[API] Request failed', {
      message: error.message,
      code: error.code,
      config: serializedConfig
    })

    if (error.response) {
      // 服务器返回了错误状态码
      console.error('API错误状态:', error.response.status)
      console.error('API错误响应头:', error.response.headers)
      console.error('API错误响应数据:', error.response.data)
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('网络错误 - 请求信息:', {
        readyState: error.request.readyState,
        status: error.request.status,
        statusText: error.request.statusText,
        responseType: error.request.responseType,
        responseURL: error.request.responseURL,
        withCredentials: error.request.withCredentials
      })
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

export const getHeartbeat = async (): Promise<HeartbeatResponse> => {
  return await api.get('/healthz', { timeout: 5000 })
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
}: CtcReportPayload): Promise<CtcReportResponse> => {
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
    const response = (await api.post<CtcReportResponse>('/ctc/report', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 600000
    })) as unknown as CtcReportResponse

    console.debug('[API] Received CTC report response', {
      hasMetadata: Boolean(response.metadata?.length),
      channelCount: response.channels?.length ?? 0
    })

    return response
  } catch (error) {
    if (isAxiosError(error)) {
      console.error('[API] CTC report request failed with Axios error', {
        message: error.message,
        code: error.code,
        config: {
          baseURL: error.config?.baseURL,
          url: error.config?.url,
          method: error.config?.method
        }
      })
      if (error.request) {
        console.error('[API] Axios request details', {
          readyState: error.request.readyState,
          status: error.request.status,
          statusText: error.request.statusText,
          responseURL: error.request.responseURL
        })
      }
    } else {
      console.error('[API] CTC report request failed with unexpected error', error)
    }
    throw error
  }
}

export default api
