import axios, { isAxiosError } from 'axios'
import type {
  CtcReportDocxResponse,
  CtcReportResponse,
  HeartbeatResponse,
  SampleNumberResponse
} from '../types/api'

type FileWithRelativePath = File & { webkitRelativePath?: string }

const runtime = window.appRuntime
const isElectron = Boolean(runtime?.isElectron)
const backendUrl = runtime?.backend?.url

const fallbackPort = '15000'
const defaultBackendUrl = `http://127.0.0.1:${fallbackPort}`

// 创建axios实例
console.info('[API] Running in electron:', isElectron)
console.info('[API] Backend URL resolved to:', isElectron ? backendUrl ?? defaultBackendUrl : '/api')

const api = axios.create({
  // 在Electron环境中直接使用FastAPI的URL，否则使用代理
  baseURL: isElectron ? backendUrl ?? defaultBackendUrl : '/api',
  timeout: 9000000,
  maxBodyLength: Infinity,
  maxContentLength: Infinity,
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

export const getHeartbeat = async (): Promise<HeartbeatResponse> => {
  return await api.get('/healthz', { timeout: 50000 })
}

export const getNextSampleNumber = async (
  petType: string
): Promise<SampleNumberResponse> => {
  const data = await api.get('/ctc/sample-number/next', {
    params: { petType }
  })
  const sampleNumber = (data as any)?.sampleNumber
  if (typeof sampleNumber !== 'string') {
    throw new Error('无效的样本编号响应')
  }
  return { sampleNumber }
}

interface CtcReportPayload {
  files: FileWithRelativePath[]
  form: {
    institutionName: string
    reportNumber: string
    detectionDate: string
    sampleNumber: string
    sampleVolume: string
    sampleStatus: string
    petType: string
    cancerBiomarker: string
    department: string
    petName: string
    ownerName: string
    age: string
    gender: string
    notes: string
    sampleType?: string
    medicationIntake?: string
  }
  roundnessThreshold?: number
  previewOnly?: boolean
  outputDir?: string
  maskInputDir?: string
}

export const postGenerateCtcReport = async ({
  files,
  form,
  roundnessThreshold = 0.3,
  previewOnly = false,
  outputDir = '',
  maskInputDir = ''
}: CtcReportPayload): Promise<CtcReportResponse> => {
  const formData = new FormData()
  console.debug('[API] Preparing CTC report request', {
    fileCount: files.length,
    fileNames: files.map(file =>
      (file as FileWithRelativePath).webkitRelativePath || file.name
    ),
    form,
    roundnessThreshold,
    previewOnly,
    outputDir,
    maskInputDir
  })
  files.forEach(file => {
    const relativePath = (file as FileWithRelativePath).webkitRelativePath || file.name
    formData.append('files', file, relativePath)
  })

  formData.append('petName', form.petName || '')
  formData.append('ownerName', form.ownerName || '')
  formData.append('age', form.age || '')
  formData.append('gender', form.gender || '')
  formData.append('notes', form.notes || '')
  formData.append('institutionName', form.institutionName || '')
  formData.append('reportNumber', form.reportNumber || '')
  formData.append('detectionDate', form.detectionDate || '')
  formData.append('sampleNumber', form.sampleNumber || '')
  formData.append('sampleVolume', form.sampleVolume || '')
  formData.append('sampleStatus', form.sampleStatus || '')
  formData.append('petType', form.petType || '')
  formData.append('cancerBiomarker', form.cancerBiomarker || '')
  formData.append('department', form.department || '')
  formData.append('sampleType', form.sampleType || '')
  formData.append('medicationIntake', form.medicationIntake || '')
  formData.append('roundnessThreshold', String(roundnessThreshold))
  formData.append('previewOnly', previewOnly ? 'true' : 'false')
  formData.append('outputDirPath', outputDir || '')
  formData.append('maskInputDirPath', maskInputDir || '')

  try {
    const response = (await api.post<CtcReportResponse>('/ctc/report', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 9000000
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

interface ExportReportPayload {
  reportToken: string
  maskOptionIds?: string[]
  maskOptionId?: string
}

export const postExportCtcReport = async ({
  reportToken,
  maskOptionIds,
  maskOptionId
}: ExportReportPayload): Promise<CtcReportDocxResponse> => {
  const formData = new FormData()
  formData.append('reportToken', reportToken)
  formData.append('maskOptionId', maskOptionId ?? '')
  if (maskOptionIds && maskOptionIds.length) {
    formData.append('maskOptionIds', JSON.stringify(maskOptionIds))
  } else {
    formData.append('maskOptionIds', '')
  }

  try {
    const response = (await api.post<CtcReportDocxResponse>('/ctc/report/export', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 9000000
    })) as unknown as CtcReportDocxResponse

    console.debug('[API] Received CTC report export response', {
      hasFile: Boolean(response.fileContent)
    })

    return response
  } catch (error) {
    if (isAxiosError(error)) {
      console.error('[API] CTC report export failed with Axios error', {
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
      console.error('[API] Unexpected error when exporting CTC report', error)
    }
    throw error
  }
}

export default api
