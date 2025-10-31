<template>
  <div class="report-builder">
    <header class="page-header">
      <div class="page-heading">
        <h2 class="page-title">报告生成工作台</h2>
        <p class="page-subtitle">整合宠物信息与识别结果，一键生成专业报告文本</p>
      </div>
    </header>

    <el-row :gutter="24" class="layout">
      <el-col :xs="24" :md="10" class="form-column">
        <el-card shadow="hover" class="form-card">
          <template #header>
            <div class="card-title">基础信息填写</div>
          </template>
          <el-form :model="form" label-width="120px" label-position="left" class="info-form">
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="宠物姓名">
                  <el-input v-model="form.petName" placeholder="宠物姓名" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="宠主姓名">
                  <el-input v-model="form.ownerName" placeholder="宠主姓名" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="性别">
                  <el-select v-model="form.gender" placeholder="请选择性别" clearable>
                    <el-option label="公" value="公" />
                    <el-option label="母" value="母" />
                    <el-option label="未知" value="未知" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="年龄">
                  <el-input v-model="form.age" placeholder="2岁3个月" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="标本类型">
                  <el-input v-model="form.sampleType" placeholder="请输入标本类型" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="一周内药物摄入">
                  <el-radio-group v-model="form.medicationIntake">
                    <el-radio label="是">是</el-radio>
                    <el-radio label="否">否</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="如有，哪些？">
              <el-input
                v-model="form.medicationDetails"
                placeholder="请输入药物名称"
                :disabled="form.medicationIntake !== '是'"
                clearable
              />
            </el-form-item>
            <el-form-item label="备注信息">
              <el-input
                v-model="form.notes"
                type="textarea"
                :rows="3"
                placeholder="既往病史、当前症状等"
                resize="none"
              />
            </el-form-item>
            <el-form-item label="影像导入">
              <div class="upload-area">
                <input
                  ref="fileInputRef"
                  class="upload-input"
                  type="file"
                  webkitdirectory
                  multiple
                  @change="handleFolderChange"
                />
                <el-button
                  type="primary"
                  plain
                  :disabled="!selectedFiles.length"
                  :loading="isDetecting"
                  @click="runDetection"
                >
                  {{ isDetecting ? '生成中...' : '生成报告' }}
                </el-button>
                <div v-if="selectedFiles.length" class="file-name">
                  {{ selectedFolderName || '已选文件夹' }}（{{ folderFileCount }} 个文件）
                </div>
                <div v-else class="upload-tip">请选择包含五个通道的影像文件夹</div>
              </div>
            </el-form-item>
          </el-form>
        </el-card>

      </el-col>

      <el-col :xs="24" :md="14" class="preview-column">
        <el-card shadow="hover" class="preview-card">
          <template #header>
            <div class="card-title">报告预览</div>
          </template>
          <div class="preview-wrapper">
            <div v-if="isPreviewLoading" class="preview-loading">
              <el-skeleton :rows="8" animated />
            </div>
            <div v-else-if="reportData" class="preview-content">
              <div class="preview-header">
                <div class="preview-heading">
                  <h3 class="preview-title">检测报告</h3>
                  <p class="preview-generated-at">生成时间：{{ formatGeneratedAt(reportData.generatedAt) }}</p>
                </div>
              </div>
              <section class="preview-section">
                <h4 class="section-title">基础信息</h4>
                <table class="metadata-table">
                  <tbody>
                    <tr v-for="(row, rowIndex) in metadataRows" :key="rowIndex">
                      <template v-for="(cell, cellIndex) in row" :key="cellIndex">
                        <th class="metadata-heading">
                          <span v-if="cell">{{ cell.label }}</span>
                        </th>
                        <td class="metadata-data">
                          <span v-if="cell">{{ cell.value }}</span>
                        </td>
                      </template>
                    </tr>
                  </tbody>
                </table>
              </section>
              <section v-if="channelPreviewItems.length" class="preview-section">
                <h4 class="section-title">通道图像</h4>
                <div class="channel-preview-grid">
                  <div
                    v-for="item in channelPreviewItems"
                    :key="item.label"
                    class="channel-preview-card"
                  >
                    <div class="channel-preview-label">{{ item.label }}</div>
                    <img :src="item.src" class="channel-preview-image" :alt="`${item.label}预览图`" />
                  </div>
                </div>
              </section>
              <footer class="preview-footer">
                检测人：______________&nbsp;&nbsp;&nbsp;&nbsp;审核人：______________&nbsp;&nbsp;&nbsp;&nbsp;报告日期：______________
              </footer>
            </div>
            <el-empty v-else description="请先生成报告以查看预览" :image-size="120" />
          </div>
          <div v-if="previewError" class="preview-error">
            <el-alert type="error" :closable="false" show-icon>{{ previewError }}</el-alert>
          </div>
          <div v-if="previewWarnings.length" class="preview-warnings">
            <el-alert
              v-for="(message, index) in previewWarnings"
              :key="index"
              type="warning"
              :closable="false"
              show-icon
            >
              {{ message }}
            </el-alert>
          </div>
          <div class="preview-actions">
            <el-button type="success" :disabled="!canDownloadReport" @click="downloadDocx">
              导出 Word 报告
            </el-button>
            <el-button :disabled="!hasReport" @click="resetAll">重置内容</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>


<script lang="ts" setup>
import { ElMessage } from 'element-plus'
import { isAxiosError } from 'axios'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { getHeartbeat, postGenerateCtcReport } from '../api/api'
import type { CtcReportResponse, ReportMetadataItem } from '../types/api'

interface ChannelPreviewItem {
  label: string
  src: string
}

type FileWithRelativePath = File & { webkitRelativePath?: string }

interface FormState {
  petName: string
  ownerName: string
  gender: string
  age: string
  sampleType: string
  medicationIntake: '是' | '否' | ''
  medicationDetails: string
  notes: string
}

const form = reactive<FormState>({
  petName: '',
  ownerName: '',
  gender: '',
  age: '',
  sampleType: '',
  medicationIntake: '',
  medicationDetails: '',
  notes: ''
})

watch(
  () => form.medicationIntake,
  value => {
    if (value !== '是') {
      form.medicationDetails = ''
    }
  }
)

const selectedFiles = ref<FileWithRelativePath[]>([])
const selectedFolderName = ref('')
const folderFileCount = ref(0)
const fileInputRef = ref<HTMLInputElement | null>(null)

const isDetecting = ref(false)
const reportData = ref<CtcReportResponse | null>(null)
const generatedReportBlob = ref<Blob | null>(null)
const generatedReportUrl = ref('')
const previewError = ref('')
const previewWarnings = ref<string[]>([])
const isPreviewLoading = ref(false)

const heartbeatIntervalMs = 5000
let heartbeatTimer: number | null = null
let heartbeatFailureCount = 0
let heartbeatDisconnectNotified = false

const roundnessThreshold = ref(0.3)

const hasReport = computed(() => Boolean(reportData.value))
const canDownloadReport = computed(() => Boolean(generatedReportBlob.value))

const sanitizeText = (value: string | null | undefined) => {
  if (!value) {
    return ''
  }
  const trimmed = value.trim()
  return trimmed === '' ? '' : trimmed
}

const splitMedicationDetails = (value: string) =>
  value
    .split(/[、,，;；\n\r]+/)
    .map(item => item.trim())
    .filter(Boolean)

const buildMedicationSchedule = (details: string) => {
  if (!details) {
    return ''
  }
  const parts = splitMedicationDetails(details)
  if (!parts.length) {
    return details
  }
  if (parts.length === 1) {
    return parts[0]
  }
  return parts.map((item, index) => `${index + 1}. ${item}`).join('\n')
}

const resolveMedicationValue = (intake: string, details: string) => {
  const normalizedIntake = sanitizeText(intake)
  const normalizedDetails = sanitizeText(details)

  if (!normalizedIntake) {
    return buildMedicationSchedule(normalizedDetails)
  }

  if (normalizedIntake === '否') {
    return '无（近期未使用药物）'
  }

  if (normalizedIntake === '是') {
    if (!normalizedDetails) {
      return '已服用药物（具体名称未填写）'
    }
    return buildMedicationSchedule(normalizedDetails)
  }

  const schedule = buildMedicationSchedule(normalizedDetails)
  return schedule || normalizedDetails
}

const formMetadataEntries = computed<ReportMetadataItem[]>(() => {
  const intakeValue = sanitizeText(form.medicationIntake)
  const medicationValue = resolveMedicationValue(form.medicationIntake, form.medicationDetails)

  return [
    { label: '宠物姓名', value: sanitizeText(form.petName) },
    { label: '宠主姓名', value: sanitizeText(form.ownerName) },
    { label: '年龄', value: sanitizeText(form.age) },
    { label: '性别', value: sanitizeText(form.gender) },
    { label: '标本类型', value: sanitizeText(form.sampleType) },
    { label: '一周内是否有药物摄入', value: intakeValue },
    { label: '药物名称', value: medicationValue },
    { label: '备注', value: sanitizeText(form.notes) }
  ]
})

const previewMetadata = computed<ReportMetadataItem[]>(() => {
  if (!reportData.value) {
    return formMetadataEntries.value
  }

  const metadataOrder = reportData.value.metadata.map(item => item.label)
  const metadataMap = new Map<string, string>()

  reportData.value.metadata.forEach(item => {
    metadataMap.set(item.label, sanitizeText(item.value))
  })

  formMetadataEntries.value.forEach(item => {
    metadataMap.set(item.label, sanitizeText(item.value))
  })

  if (!metadataOrder.length) {
    return formMetadataEntries.value
  }

  return metadataOrder.map(label => ({
    label,
    value: sanitizeText(metadataMap.get(label))
  }))
})

const metadataRows = computed(() => {
  const rows: Array<Array<ReportMetadataItem | null>> = []
  const items = previewMetadata.value
  for (let index = 0; index < items.length; index += 2) {
    rows.push([items[index], items[index + 1] ?? null])
  }
  if (!rows.length) {
    rows.push([null, null])
  }
  return rows
})

const channelPreviewItems = computed<ChannelPreviewItem[]>(() => {
  const items = reportData.value?.imageSet?.items ?? []
  if (!items.length) {
    return []
  }
  return items
    .filter(item => item.data)
    .map(item => ({
      label: item.label,
      src: `data:${item.mimeType};base64,${item.data}`
    }))
})

const expectedChannels = ['1', '2', '3', '4', '5']

const revokeObjectUrl = (url: string) => {
  if (url) {
    window.URL.revokeObjectURL(url)
  }
}

const resetPreview = () => {
  reportData.value = null
  previewError.value = ''
  previewWarnings.value = []
}

const resetSelectedFolder = () => {
  selectedFiles.value = []
  selectedFolderName.value = ''
  folderFileCount.value = 0
  resetPreview()
  if (generatedReportUrl.value) {
    revokeObjectUrl(generatedReportUrl.value)
    generatedReportUrl.value = ''
  }
  generatedReportBlob.value = null
}

const base64ToBlob = (base64: string, mimeType: string) => {
  const binary = window.atob(base64)
  const length = binary.length
  const bytes = new Uint8Array(length)
  for (let index = 0; index < length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return new Blob([bytes], { type: mimeType })
}

const applyReportBlob = (data: CtcReportResponse) => {
  const blob = base64ToBlob(
    data.fileContent,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  )
  if (generatedReportUrl.value) {
    revokeObjectUrl(generatedReportUrl.value)
    generatedReportUrl.value = ''
  }
  generatedReportBlob.value = blob
  generatedReportUrl.value = window.URL.createObjectURL(blob)
}

const formatGeneratedAt = (value: string) => {
  const date = new Date(value)
  if (!Number.isNaN(date.getTime())) {
    return date.toLocaleString('zh-CN', { hour12: false })
  }
  return value
}

const handleFolderChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  resetSelectedFolder()

  if (!files || !files.length) {
    return
  }

  const fileArray = Array.from(files) as FileWithRelativePath[]
  const validFiles = fileArray.filter(item => item.name !== '.DS_Store')

  if (!validFiles.length) {
    ElMessage.error('所选文件夹中没有有效的影像文件')
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
    return
  }

  const channelSet = new Set<string>()
  validFiles.forEach(file => {
    const relativePath = file.webkitRelativePath || file.name
    relativePath
      .split('/')
      .filter(Boolean)
      .forEach(part => {
        if (expectedChannels.includes(part)) {
          channelSet.add(part)
        }
      })
  })

  const missingChannels = expectedChannels.filter(channel => !channelSet.has(channel))
  if (missingChannels.length) {
    ElMessage.error(`所选文件夹缺少通道：${missingChannels.join('、')}`)
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
    return
  }

  const firstPath = validFiles[0].webkitRelativePath || validFiles[0].name
  const rootName = firstPath.split('/').filter(Boolean)[0] || validFiles[0].name

  selectedFiles.value = validFiles
  selectedFolderName.value = rootName
  folderFileCount.value = validFiles.length
  console.info('[Report] 已选择影像文件夹', {
    folder: rootName,
    fileCount: validFiles.length,
    expectedChannels,
    roundnessThreshold: roundnessThreshold.value
  })
}

const runDetection = async () => {
  if (!selectedFiles.value.length) {
    ElMessage.warning('请先选择包含影像的文件夹')
    return
  }

  previewError.value = ''
  previewWarnings.value = []
  isPreviewLoading.value = true

  if (generatedReportUrl.value) {
    revokeObjectUrl(generatedReportUrl.value)
    generatedReportUrl.value = ''
  }
  generatedReportBlob.value = null
  reportData.value = null

  try {
    console.info('[Report] 开始请求后端生成报告', {
      folder: selectedFolderName.value,
      fileCount: selectedFiles.value.length,
      roundnessThreshold: roundnessThreshold.value
    })
    isDetecting.value = true
    startHeartbeat()
    const response = await postGenerateCtcReport({
      files: selectedFiles.value,
      form: {
        petName: form.petName,
        ownerName: form.ownerName,
        age: form.age,
        gender: form.gender,
        sampleType: form.sampleType,
        medicationIntake: form.medicationIntake,
        medicationDetails: form.medicationDetails,
        notes: form.notes
      },
      roundnessThreshold: roundnessThreshold.value
    })

    applyReportBlob(response)
    reportData.value = response
    previewWarnings.value = response.warnings ?? []
    ElMessage.success('报告生成成功，预览已同步更新')
  } catch (error) {
    previewError.value = '报告生成失败，请稍后重试。'
    if (isAxiosError(error)) {
      if (error.code === 'ERR_NETWORK') {
        console.error('[Report] 无法连接后端服务', error)
        ElMessage.error('无法连接后端服务，请确认FastAPI接口已启动（默认端口 8001）。')
        previewError.value = '无法连接后端服务，请确认后端已启动。'
      } else if (error.code === 'ECONNABORTED') {
        console.error('[Report] 生成报告请求超时', error)
        ElMessage.error('生成报告超时，请检查后端处理是否正常或稍后重试')
        previewError.value = '生成报告超时，请稍后重试。'
      } else {
        console.error('[Report] 生成报告失败', error)
        ElMessage.error('生成报告失败，请稍后重试')
      }
    } else {
      console.error('[Report] 生成报告失败', error)
      ElMessage.error('生成报告失败，请稍后重试')
    }
  } finally {
    stopHeartbeat()
    isDetecting.value = false
    isPreviewLoading.value = false
    if (!generatedReportBlob.value && generatedReportUrl.value) {
      revokeObjectUrl(generatedReportUrl.value)
      generatedReportUrl.value = ''
    }
    if (!reportData.value) {
      previewWarnings.value = []
    }
  }
}

const downloadDocx = () => {
  if (!generatedReportBlob.value || !generatedReportUrl.value) {
    ElMessage.warning('请先生成报告后再导出 Word 文件')
    return
  }

  const downloadName = `${selectedFolderName.value || 'ctc_dataset'}-report.docx`
  const link = document.createElement('a')
  link.href = generatedReportUrl.value
  link.download = downloadName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const resetAll = () => {
  form.petName = ''
  form.ownerName = ''
  form.gender = ''
  form.age = ''
  form.sampleType = ''
  form.medicationIntake = ''
  form.medicationDetails = ''
  form.notes = ''
  resetSelectedFolder()
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const startHeartbeat = () => {
  if (heartbeatTimer !== null) {
    return
  }

  console.info('[Report] 启动心跳检测', { interval: heartbeatIntervalMs })
  heartbeatFailureCount = 0
  heartbeatDisconnectNotified = false

  heartbeatTimer = window.setInterval(async () => {
    try {
      await getHeartbeat()
      if (heartbeatFailureCount > 0) {
        console.info('[Report] 心跳检测已恢复')
      }
      heartbeatFailureCount = 0
      heartbeatDisconnectNotified = false
    } catch (error) {
      heartbeatFailureCount += 1
      console.warn('[Report] 心跳检测失败', { count: heartbeatFailureCount, error })

      if (heartbeatFailureCount === 1) {
        ElMessage.warning('检测报告正在生成，请耐心等待（正在保持与后端的连接）')
      } else if (heartbeatFailureCount >= 3 && !heartbeatDisconnectNotified) {
        ElMessage.error('后端长时间未响应，请检查服务是否正常运行')
        heartbeatDisconnectNotified = true
      }
    }
  }, heartbeatIntervalMs)
}

const stopHeartbeat = () => {
  if (heartbeatTimer !== null) {
    window.clearInterval(heartbeatTimer)
    heartbeatTimer = null
    console.info('[Report] 已停止心跳检测')
  }

  heartbeatFailureCount = 0
  heartbeatDisconnectNotified = false
}

onBeforeUnmount(() => {
  stopHeartbeat()
  if (generatedReportUrl.value) {
    revokeObjectUrl(generatedReportUrl.value)
    generatedReportUrl.value = ''
  }
})
</script>


<style scoped>
.report-builder {
  padding: 16px 24px 32px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
  min-height: calc(100vh - 120px);
}

.page-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.page-heading {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.page-title {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
}

.page-subtitle {
  margin: 0;
  font-size: 14px;
  color: #475569;
}

.layout {
  align-items: stretch;
}

.form-card,
.preview-card {
  border-radius: 16px;
  overflow: hidden;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.info-form {
  padding-right: 8px;
}

.form-row {
  margin-bottom: 4px;
}

.form-row:last-of-type {
  margin-bottom: 0;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.upload-input {
  border: 1px dashed #cbd5f5;
  padding: 12px;
  border-radius: 10px;
  background-color: rgba(255, 255, 255, 0.86);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.upload-input:hover {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.file-name {
  font-size: 13px;
  color: #4b5563;
}

.upload-tip {
  font-size: 13px;
  color: #9ca3af;
}

.preview-wrapper {
  background: #f3f4f6;
  border-radius: 16px;
  padding: 16px;
  min-height: 560px;
  display: flex;
  width: 100%;
}

.preview-loading,
.preview-content,
.el-empty {
  width: 100%;
}

.preview-content {
  background: #ffffff;
  border-radius: 14px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 18px 32px rgba(15, 23, 42, 0.12);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.preview-heading {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preview-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #111827;
}

.preview-generated-at {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}


.metadata-table {
  width: 100%;
  border-collapse: collapse;
  border-spacing: 0;
  background-color: transparent;
}

.metadata-table tbody tr {
  background-color: transparent;
}

.metadata-heading,
.metadata-data {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.12);
  font-size: 14px;
}

.metadata-heading {
  width: 18%;
  color: #1d4ed8;
  font-weight: 600;
  text-align: right;
  background-color: transparent;
}

.metadata-data {
  color: #0f172a;
  word-break: break-word;
  background-color: transparent;
  white-space: pre-line;
}

.metadata-table tbody tr:last-child .metadata-heading,
.metadata-table tbody tr:last-child .metadata-data {
  border-bottom: none;
}

.channel-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.channel-preview-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(226, 232, 240, 0.85) 100%);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.12);
}

.channel-preview-label {
  font-size: 13px;
  font-weight: 600;
  color: #1e3a8a;
  text-align: center;
}

.channel-preview-image {
  width: 100%;
  border-radius: 10px;
  object-fit: cover;
  box-shadow: 0 6px 16px rgba(30, 64, 175, 0.2);
}

.preview-footer {
  margin-top: auto;
  text-align: center;
  font-size: 13px;
  color: #64748b;
}

.preview-error,
.preview-warnings {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-actions {
  margin-top: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
}

@media (max-width: 991px) {
  .report-builder {
    padding: 12px 16px 24px;
  }

  .page-header {
    align-items: flex-start;
  }

  .page-title {
    font-size: 22px;
  }

  .preview-wrapper {
    min-height: 480px;
    padding: 12px;
  }

  .preview-content {
    padding: 18px;
  }

  .preview-actions {
    justify-content: center;
  }

  .metadata-heading {
    width: 24%;
    text-align: left;
  }
}
</style>
