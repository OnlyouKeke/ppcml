<template>
  <div class="report-builder">
    <header class="page-header">
      <div class="page-heading">
        <h2 class="page-title">报告生成工作台</h2>
        <p class="page-subtitle">整合宠物信息与识别结果，一键生成专业报告文本</p>
      </div>
    </header>

    <section class="layout">
      <el-card shadow="hover" class="form-card">
        <template #header>
          <div class="card-title">基础信息填写</div>
        </template>
        <el-form :model="form" label-width="120px" label-position="left" class="info-form">
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="宠主姓名">
                  <el-input v-model="form.ownerName" placeholder="宠主姓名" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="宠物姓名">
                  <el-input v-model="form.petName" placeholder="宠物姓名" clearable />
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
                <el-form-item label="宠物类型">
                  <el-radio-group v-model="form.petType">
                    <el-radio label="猫">猫</el-radio>
                    <el-radio label="狗">狗</el-radio>
                    <el-radio label="其他">其他</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="年龄">
                  <el-input v-model="form.age" placeholder="2岁3个月" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="送检单位">
                  <el-input v-model="form.institutionName" placeholder="请输入机构名称" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="送检时间">
                  <el-date-picker
                    v-model="form.detectionDate"
                    type="date"
                    placeholder="请选择检测日期"
                    value-format="YYYY-MM-DD"
                    style="width: 100%"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="科别">
                  <el-input v-model="form.department" placeholder="请输入科别" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="癌症标志物">
                  <el-input v-model="form.cancerBiomarker" placeholder="请输入癌症标志物" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="样本类型">
                  <el-input v-model="form.sampleType" placeholder="请输入标本类型" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="样品量（单位ml）">
                  <el-input
                    v-model="form.sampleVolume"
                    placeholder="请输入样品量"
                    type="number"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="样本编号">
                  <el-input
                    v-model="form.sampleNumber"
                    :maxlength="sampleNumberMaxLength"
                    :disabled="!form.petType"
                    readonly
                    placeholder="请选择宠物类型后填写"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="样本状态">
                  <el-radio-group v-model="form.sampleStatus">
                    <el-radio label="合格">合格</el-radio>
                    <el-radio label="不合格">不合格</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="一周内是否有药物摄入">
                  <el-radio-group v-model="form.medicationIntake">
                    <el-radio label="是">是</el-radio>
                    <el-radio label="否">否</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="如有，请说明">
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
                <div class="upload-actions">
                  <el-button type="primary" @click="triggerFolderSelection">
                    选择影像文件夹
                  </el-button>
                  <el-button
                    type="primary"
                    plain
                    :disabled="!selectedFiles.length"
                    :loading="isDetecting"
                    @click="runDetection"
                  >
                    {{ isDetecting ? '生成中...' : '生成报告' }}
                  </el-button>
                </div>
                <div class="upload-status">
                  <div v-if="selectedFiles.length" class="file-name">
                    {{ selectedFolderName || '已选文件夹' }}（{{ folderFileCount }} 个文件）
                  </div>
                  <div v-else class="upload-tip">请选择包含五个通道的影像文件夹</div>
                </div>
                <div class="output-folder-section">
                  <div class="output-folder-selector">
                    <el-input
                      v-model="form.outputDirPath"
                      placeholder="请输入或选择输出文件夹路径"
                      clearable
                      class="output-folder-input"
                    >
                      <template #append>
                        <el-button
                          type="primary"
                          plain
                          @click="triggerOutputFolderSelection"
                        >
                          选择输出文件夹
                        </el-button>
                      </template>
                    </el-input>
                  </div>
                  <div class="output-folder-tip">
                    若路径不存在将自动创建，并在其中输出处理结果与 Word 报告。
                  </div>
                </div>
              </div>
            </el-form-item>
        </el-form>
      </el-card>
      
      <el-card shadow="hover" class="mask-card">
        <template #header>
          <div class="card-title">掩码图像选择</div>
        </template>
        <div class="mask-selection">
          <p class="mask-instruction">请选择需要插入 Word 报告的三个通道掩码图像。</p>
          <div v-if="maskDirectoryPath" class="mask-directory">
            掩码图像来源文件夹：<span class="mask-directory-path">{{ maskDirectoryPath }}</span>
          </div>
          <div v-if="isPreviewLoading" class="mask-loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="!reportToken" class="mask-placeholder">
            生成报告预览后，将在此展示生成的所有图像供选择。
          </div>
          <el-empty
            v-else-if="!maskOptions.length"
            description="当前未检测到可用的掩码图像"
            :image-size="100"
            class="mask-empty"
          />
          <div v-else class="mask-options-wrapper">
            <div class="mask-preview-grid">
              <div
                v-for="option in maskOptions"
                :key="`preview-${option.id}`"
                :class="[
                  'mask-preview-card',
                  { active: maskSelectionOrderMap.get(option.id) }
                ]"
                @click="toggleMaskSelection(option.id)"
              >
                <img
                  :src="`data:${option.mimeType};base64,${option.data}`"
                  :alt="option.label"
                  class="mask-preview-image"
                />
                <div class="mask-preview-label">
                  {{ option.label }}
                  <el-tag
                    v-if="maskSelectionOrderMap.get(option.id)"
                    size="small"
                    class="mask-selection-order"
                  >
                    第{{ maskSelectionOrderMap.get(option.id) }}张
                  </el-tag>
                </div>
              </div>
            </div>
            <div class="mask-selected-tip">
              已选择 {{ selectedMaskOptions.length }} / {{ requiredMaskSelectionCount }} 张掩码图像
            </div>
            <div v-if="!isMaskSelectionComplete" class="mask-selection-warning">
              请从上述掩码图像中选择 {{ requiredMaskSelectionCount }} 张，将用于报告预览与导出。
            </div>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="preview-card">
        <template #header>
          <div class="card-title">报告预览</div>
        </template>
        <div class="preview-wrapper">
            <div v-if="isPreviewLoading" class="preview-loading">
              <el-skeleton :rows="8" animated />
            </div>
            <div
              v-else-if="reportData && isMaskSelectionComplete"
              class="preview-content"
            >
              <div class="report-preview">
                <header class="report-header">
                  <div class="report-title">
                    <div class="report-title-line">
                      <span class="report-title-brand">FlowCanis</span>
                      <span class="report-title-text">微流控循环肿瘤细胞分选</span>
                    </div>
                    <div class="report-title-line report-title-line--secondary">
                      与免疫荧光识别检测报告单
                    </div>
                  </div>
                  <div class="report-divider">
                    <span class="report-divider-line report-divider-line--primary" />
                    <span class="report-divider-line report-divider-line--secondary" />
                  </div>
                  <div class="report-number">编号：{{ reportNumberDisplay }}</div>
                </header>
                <div class="report-generated-at">
                  生成时间：{{ formatGeneratedAt(reportData.generatedAt) }}
                </div>
                <section class="report-info">
                  <div class="report-info-divider" />
                  <div
                    v-for="(line, lineIndex) in previewInfoLines"
                    :key="lineIndex"
                    class="report-info-line"
                  >
                    <div
                      v-for="(field, fieldIndex) in line"
                      :key="fieldIndex"
                      class="report-info-field"
                    >
                      <span class="report-info-label">{{ field.label }}：</span>
                      <span class="report-info-value">{{ field.value }}</span>
                    </div>
                  </div>
                  <div class="report-info-divider" />
                </section>
                <section
                  v-if="previewDetailFields.length"
                  class="report-info-details"
                >
                  <div
                    v-for="(field, fieldIndex) in previewDetailFields"
                    :key="fieldIndex"
                    class="report-info-detail"
                  >
                    <span class="report-info-label">{{ field.label }}：</span>
                    <span class="report-info-value">{{ field.value }}</span>
                  </div>
                </section>
                <section v-if="channelPreviewItems.length" class="report-section">
                  <h4 class="section-title">通道图像</h4>
                  <div v-if="channelSummaryTexts.length" class="channel-summary-texts">
                    <p
                      v-for="(text, index) in channelSummaryTexts"
                      :key="`summary-${index}`"
                      class="channel-summary-text"
                    >
                      {{ text }}
                    </p>
                  </div>
                  <div class="channel-preview-grid">
                    <div
                      v-for="item in channelPreviewItems"
                      :key="item.label"
                      class="channel-preview-card"
                    >
                      <div class="channel-preview-label">{{ item.label }}</div>
                      <img
                        :src="item.src"
                        class="channel-preview-image"
                        :alt="`${item.label}预览图`"
                      />
                    </div>
                  </div>
                </section>
                <footer class="preview-footer">
                  检测人：______________&nbsp;&nbsp;&nbsp;&nbsp;审核人：______________&nbsp;&nbsp;&nbsp;&nbsp;报告日期：______________
                </footer>
                <div class="preview-disclaimer">
                  <p
                    v-for="(line, index) in disclaimerLines"
                    :key="index"
                    class="preview-disclaimer-line"
                  >
                    {{ line }}
                  </p>
                </div>
              </div>
            </div>
            <div
              v-else-if="reportData && !isMaskSelectionComplete"
              class="preview-blocker"
            >
              <el-empty
                description="请选择三张掩码图像后查看报告预览"
                :image-size="120"
              />
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
            <el-button
              type="success"
              :disabled="!canDownloadReport || isExporting"
              :loading="isExporting"
              @click="downloadDocx"
            >
              {{ isExporting ? '生成中...' : '导出 Word 报告' }}
            </el-button>
            <el-button :disabled="!hasReport" @click="resetAll">重置内容</el-button>
          </div>
        </el-card>
      </section>
    </div>
  </template>

<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getNextSampleNumber, postExportCtcReport, postGenerateCtcReport } from '../api/api'
import type {
  CtcReportResponse,
  ReportMaskOption,
  ReportMetadataItem
} from '../types/api'

type FileWithRelativePath = File & { webkitRelativePath?: string }

interface ChannelPreviewItem {
  label: string
  src: string
}

interface PreviewLineField {
  label: string
  value: string
}

interface PreviewDetailField {
  label: string
  value: string
}

const requiredMaskSelectionCount = 3
const sampleNumberMaxLength = 32

const fileInputRef = ref<HTMLInputElement>()
const selectedFiles = ref<FileWithRelativePath[]>([])
const selectedFolderName = ref('')

const isDetecting = ref(false)
const isPreviewLoading = ref(false)
const isExporting = ref(false)

const reportData = ref<CtcReportResponse | null>(null)
const reportToken = ref('')
const previewError = ref('')
const previewWarnings = ref<string[]>([])
const maskOptions = ref<ReportMaskOption[]>([])
const maskSelectionOrderMap = ref(new Map<string, number>())
const maskDirectoryPath = ref('')

const form = reactive({
  ownerName: '',
  petName: '',
  gender: '',
  petType: '',
  age: '',
  institutionName: '',
  detectionDate: '',
  department: '',
  cancerBiomarker: '',
  sampleType: '',
  sampleVolume: '',
  sampleNumber: '',
  sampleStatus: '',
  medicationIntake: '',
  notes: '',
  outputDirPath: '',
  reportNumber: ''
})

const latestSampleNumberRequest = ref<symbol | null>(null)

const folderFileCount = computed(() => selectedFiles.value.length)

const selectedMaskOptions = computed(() => {
  const orderMap = maskSelectionOrderMap.value
  return maskOptions.value
    .filter(option => orderMap.has(option.id))
    .sort((a, b) => (orderMap.get(a.id)! - orderMap.get(b.id)!))
})

const isMaskSelectionComplete = computed(
  () => selectedMaskOptions.value.length === requiredMaskSelectionCount
)

const canDownloadReport = computed(
  () => Boolean(reportData.value && reportToken.value && isMaskSelectionComplete.value)
)

const hasReport = computed(() => Boolean(reportData.value))

const channelPreviewItems = computed<ChannelPreviewItem[]>(() => {
  const items = reportData.value?.imageSet?.items ?? []
  return items.map(item => ({
    label: item.label,
    src: `data:${item.mimeType};base64,${item.data}`
  }))
})

const channelSummaryTexts = computed(
  () => reportData.value?.channelSummaryTexts ?? []
)

const normalizeMetadataValue = (item: ReportMetadataItem) => {
  const value = (item.value ?? '').toString().trim()
  return value || '未填写'
}

const formatReportDate = (value: string) => {
  const trimmed = value.trim()
  if (!trimmed || trimmed === '未填写') {
    return trimmed || '未填写'
  }

  const match = trimmed.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/)
  if (!match) {
    return trimmed
  }

  const [, year, month, day] = match
  return `${year}年${Number(month)}月${Number(day)}日`
}

const previewInfoLines = computed<PreviewLineField[][]>(() => {
  if (!reportData.value) {
    return []
  }

  const metadataMap = new Map<string, string>()
  for (const item of reportData.value.metadata ?? []) {
    metadataMap.set(item.label, normalizeMetadataValue(item))
  }

  const ensureValue = (label: string, fallback = '未填写') => {
    const rawValue = metadataMap.get(label) ?? ''
    const normalized = rawValue.trim()
    if (!normalized || normalized === '未填写') {
      return fallback
    }
    return normalized
  }

  const sampleVolumeRaw = metadataMap.get('样品量（单位ml）')?.trim() ?? ''
  const sampleVolumeValue = sampleVolumeRaw
    ? sampleVolumeRaw.replace(/\s+/g, '').toUpperCase()
    : '未填写'

  const remarkRaw = metadataMap.get('备注')?.trim() ?? ''
  const remarkValue = !remarkRaw || remarkRaw === '未填写' ? '无' : remarkRaw

  const detectionDateRaw = metadataMap.get('检测日期')?.trim() ?? ''
  const detectionDateValue =
    !detectionDateRaw || detectionDateRaw === '未填写'
      ? '未填写'
      : formatReportDate(detectionDateRaw)

  return [
    [
      { label: '宠主姓名', value: ensureValue('宠主姓名') },
      { label: '宠物姓名', value: ensureValue('宠物姓名') },
      { label: '性别', value: ensureValue('性别') },
      { label: '宠物类型', value: ensureValue('宠物类型') },
      { label: '年龄', value: ensureValue('年龄') }
    ],
    [
      { label: '送检单位', value: ensureValue('机构名称') },
      { label: '送检时间', value: detectionDateValue },
      { label: '科别', value: ensureValue('科别') },
      { label: '癌症标志物', value: ensureValue('癌症标志物') }
    ],
    [
      { label: '样本类型', value: ensureValue('标本类型') },
      { label: '样品量', value: sampleVolumeValue },
      { label: '样本编号', value: ensureValue('样本编号') },
      { label: '样本状态', value: ensureValue('样本状态') }
    ],
    [
      { label: '一周内是否有药物摄入', value: ensureValue('一周内是否有药物摄入') },
      { label: '如有，请说明', value: remarkValue }
    ]
  ]
})

const previewDetailFields = computed<PreviewDetailField[]>(() => {
  if (!reportData.value) {
    return []
  }

  const fields: PreviewDetailField[] = []

  const detectionResultRows = reportData.value.detectionResultRows ?? []
  if (detectionResultRows.length) {
    const formattedLines = detectionResultRows
      .map(row => row.join('   '))
      .join('\n')
    fields.push({ label: '检测结果', value: formattedLines })
  }

  if (reportData.value.totals) {
    fields.push({
      label: '统计汇总',
      value: `CTC ${reportData.value.totals.totalCtc} / WBC ${reportData.value.totals.totalWbc}`
    })
  }

  if (reportData.value.resultText) {
    fields.push({ label: '结果说明', value: reportData.value.resultText })
  }

  if (reportData.value.selectionText) {
    fields.push({ label: '掩码选择说明', value: reportData.value.selectionText })
  }

  if (reportData.value.remarkText) {
    fields.push({ label: '备注', value: reportData.value.remarkText })
  }

  return fields
})

const reportNumberDisplay = computed(() => {
  const metadataValue = reportData.value?.metadata?.find(
    item => item.label === '报告编号'
  )?.value
  const fallback = form.reportNumber || form.sampleNumber
  return (metadataValue ?? fallback)?.trim() || '未填写'
})

const disclaimerLines = [
  '本报告仅供兽医专业判断与临床参考，不可直接作为最终诊断依据。',
  '如对检测结果存在疑问，请联系检测机构进行复核。',
  '报告中的影像及数据受采样与环境影响，请结合实际情况综合评估。'
]

const formatGeneratedAt = (value: string) => {
  if (!value) {
    return '—'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const resetMaskSelection = () => {
  maskSelectionOrderMap.value = new Map<string, number>()
}

const assignSampleNumber = (value: string) => {
  const previousSampleNumber = form.sampleNumber
  const normalized = (value ?? '').toString().trim().toUpperCase()
  const truncated = normalized.slice(0, sampleNumberMaxLength)
  form.sampleNumber = truncated
  if (!form.reportNumber || form.reportNumber === previousSampleNumber) {
    form.reportNumber = truncated
  }
}

const clearSampleNumber = () => {
  const previousSampleNumber = form.sampleNumber
  form.sampleNumber = ''
  if (!form.reportNumber || form.reportNumber === previousSampleNumber) {
    form.reportNumber = ''
  }
}

const resolveFolderName = (files: FileWithRelativePath[]) => {
  if (!files.length) {
    return ''
  }
  const first = files[0]
  const relativePath = first.webkitRelativePath || ''
  if (relativePath.includes('/')) {
    return relativePath.split('/')[0]
  }
  return first.name || ''
}

const handleFolderChange = (event: Event) => {
  const target = event.target as HTMLInputElement | null
  const files = target?.files ? Array.from(target.files) : []
  selectedFiles.value = files as FileWithRelativePath[]
  selectedFolderName.value = resolveFolderName(selectedFiles.value)
  previewError.value = ''
}

const triggerFolderSelection = () => {
  fileInputRef.value?.click()
}

const triggerOutputFolderSelection = async () => {
  if (!window.electronAPI?.selectDirectory) {
    ElMessage.warning('当前环境不支持系统文件夹选择，请手动输入路径')
    return
  }
  try {
    const directory = await window.electronAPI.selectDirectory({
      title: '选择报告输出文件夹',
      defaultPath: form.outputDirPath || undefined
    })
    if (directory) {
      form.outputDirPath = directory
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '无法选择输出文件夹'
    ElMessage.error(message)
  }
}

const extractErrorMessage = (error: unknown) => {
  if (
    error &&
    typeof error === 'object' &&
    'response' in error &&
    (error as any).response?.data?.detail
  ) {
    return (error as any).response.data.detail as string
  }
  if (error instanceof Error) {
    return error.message
  }
  return '操作失败，请稍后重试'
}

watch(
  () => form.petType,
  async (newPetType, oldPetType) => {
    const normalizedNew = (newPetType || '').trim()
    const normalizedOld = (oldPetType || '').trim()

    if (!normalizedNew) {
      latestSampleNumberRequest.value = null
      clearSampleNumber()
      return
    }

    if (normalizedNew === normalizedOld && form.sampleNumber) {
      return
    }

    const requestToken = Symbol('sample-number-request')
    latestSampleNumberRequest.value = requestToken
    const previousSampleNumber = form.sampleNumber

    try {
      const response = await getNextSampleNumber(normalizedNew)
      if (latestSampleNumberRequest.value !== requestToken) {
        return
      }
      assignSampleNumber(response.sampleNumber)
    } catch (error) {
      if (latestSampleNumberRequest.value !== requestToken) {
        return
      }
      assignSampleNumber(previousSampleNumber)
      const message = extractErrorMessage(error)
      ElMessage.error(message || '无法生成样本编号')
    } finally {
      if (latestSampleNumberRequest.value === requestToken) {
        latestSampleNumberRequest.value = null
      }
    }
  }
)

const toggleMaskSelection = (id: string) => {
  const current = new Map(maskSelectionOrderMap.value)
  if (current.has(id)) {
    current.delete(id)
    const reordered = new Map<string, number>()
    Array.from(current.entries())
      .sort((a, b) => a[1] - b[1])
      .forEach(([key], index) => {
        reordered.set(key, index + 1)
      })
    maskSelectionOrderMap.value = reordered
    return
  }

  if (current.size >= requiredMaskSelectionCount) {
    ElMessage.warning(`最多选择${requiredMaskSelectionCount}张掩码图像`)
    return
  }

  current.set(id, current.size + 1)
  maskSelectionOrderMap.value = current
}

const runDetection = async () => {
  if (!selectedFiles.value.length) {
    ElMessage.warning('请先选择包含影像的文件夹')
    return
  }

  isDetecting.value = true
  isPreviewLoading.value = true
  previewError.value = ''

  try {
    const response = await postGenerateCtcReport({
      files: selectedFiles.value,
      form: {
        institutionName: form.institutionName,
        reportNumber: form.reportNumber || form.sampleNumber,
        detectionDate: form.detectionDate,
        sampleNumber: form.sampleNumber,
        sampleVolume: form.sampleVolume,
        sampleStatus: form.sampleStatus,
        petType: form.petType,
        cancerBiomarker: form.cancerBiomarker,
        department: form.department,
        petName: form.petName,
        ownerName: form.ownerName,
        age: form.age,
        gender: form.gender,
        notes: form.notes,
        sampleType: form.sampleType,
        medicationIntake: form.medicationIntake
      },
      previewOnly: true,
      outputDir: form.outputDirPath.trim(),
      maskInputDir: ''
    })

    reportData.value = response
    if (response.generatedSampleNumber) {
      assignSampleNumber(response.generatedSampleNumber)
    }
    reportToken.value = response.reportToken ?? ''
    previewWarnings.value = response.warnings ?? []
    maskOptions.value = response.maskOptions ?? []
    maskDirectoryPath.value = response.maskInputDirectory ?? ''
    resetMaskSelection()
    if (!maskOptions.value.length) {
      ElMessage.info('未检测到可选择的掩码图像')
    }
    ElMessage.success('报告预览生成成功')
  } catch (error) {
    previewError.value = extractErrorMessage(error)
    reportData.value = null
    reportToken.value = ''
    maskOptions.value = []
    resetMaskSelection()
    ElMessage.error(previewError.value)
  } finally {
    isDetecting.value = false
    isPreviewLoading.value = false
  }
}

const downloadDocx = async () => {
  if (!canDownloadReport.value) {
    ElMessage.warning('请选择三张掩码图像后再导出报告')
    return
  }

  if (!reportToken.value) {
    ElMessage.error('缺少报告标识，无法导出')
    return
  }

  isExporting.value = true

  try {
    const response = await postExportCtcReport({
      reportToken: reportToken.value,
      maskOptionIds: selectedMaskOptions.value.map(option => option.id)
    })

    if (!response.fileContent) {
      throw new Error('未收到有效的报告文件数据')
    }

    const binary = atob(response.fileContent)
    const bytes = new Uint8Array(binary.length)
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index)
    }
    const blob = new Blob([bytes], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = response.fileName || 'ctc_report.docx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('Word 报告导出成功')
  } catch (error) {
    const message = extractErrorMessage(error)
    ElMessage.error(message)
  } finally {
    isExporting.value = false
  }
}

const resetAll = () => {
  form.ownerName = ''
  form.petName = ''
  form.gender = ''
  form.petType = ''
  form.age = ''
  form.institutionName = ''
  form.detectionDate = ''
  form.department = ''
  form.cancerBiomarker = ''
  form.sampleType = ''
  form.sampleVolume = ''
  clearSampleNumber()
  form.sampleStatus = ''
  form.medicationIntake = ''
  form.notes = ''
  form.outputDirPath = ''
  form.reportNumber = ''

  selectedFiles.value = []
  selectedFolderName.value = ''
  reportData.value = null
  reportToken.value = ''
  previewError.value = ''
  previewWarnings.value = []
  maskOptions.value = []
  maskDirectoryPath.value = ''
  resetMaskSelection()
  latestSampleNumberRequest.value = null

  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

defineExpose({
  runDetection,
  downloadDocx,
  resetAll
})
</script>

<style scoped>
.report-builder {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  text-align: center;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

.page-subtitle {
  margin-top: 4px;
  font-size: 14px;
  color: #64748b;
}

.layout {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

@media (min-width: 1280px) {
  .layout {
    display: grid;
    grid-template-columns: minmax(360px, 1.1fr) minmax(320px, 0.9fr);
    grid-auto-rows: min-content;
    gap: 24px;
  }

  .form-card {
    grid-column: 1 / -1;
  }
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.08), rgba(14, 165, 233, 0.08));
  border: 1px dashed rgba(79, 70, 229, 0.3);
}

.upload-input {
  position: absolute;
  width: 0.1px;
  height: 0.1px;
  opacity: 0;
  overflow: hidden;
  pointer-events: none;
}

.upload-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.upload-status {
  font-size: 14px;
  color: #334155;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-weight: 600;
  color: #1f2937;
}

.upload-tip {
  color: #64748b;
}

.output-folder-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.output-folder-input {
  width: 100%;
}

.output-folder-tip {
  font-size: 12px;
  color: #94a3b8;
}

.mask-selection {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mask-options-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mask-preview-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
}

.mask-preview-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 22px 40px -30px rgba(79, 70, 229, 0.55);
  cursor: pointer;
  transition: all 0.2s ease;
}

.mask-preview-card:hover {
  transform: translateY(-4px);
  border-color: #6366f1;
  box-shadow: 0 26px 46px -30px rgba(79, 70, 229, 0.55);
}

.mask-preview-card.active {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
}

.mask-preview-image {
  width: 100%;
  height: 160px;
  object-fit: contain;
  border-radius: 12px;
  border: 1px dashed rgba(99, 102, 241, 0.4);
  background: #f8fafc;
  padding: 8px;
}

.mask-preview-card.active .mask-preview-image {
  border-color: #4f46e5;
  background: rgba(79, 70, 229, 0.08);
}

.mask-preview-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.mask-selection-order {
  border-color: rgba(79, 70, 229, 0.3);
  background: rgba(99, 102, 241, 0.12);
  color: #4338ca;
}

.mask-selected-tip {
  font-size: 13px;
  color: #475569;
}

.mask-selection-warning {
  font-size: 13px;
  color: #f97316;
  background: rgba(253, 186, 116, 0.18);
  border-radius: 12px;
  padding: 10px 12px;
}

.preview-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-content {
  background: #ffffff;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 32px 60px -38px rgba(15, 23, 42, 0.55);
  border-top: 2px solid #000000;
  border-bottom: 2px solid #000000;
}

.report-preview {
  font-family: "Songti SC", "Songti SC Regular", "SimSun", serif;
  font-size: 14.67px;
  line-height: 1.6;
  color: #1f2937;
}

.report-preview * {
  font-family: inherit;
}

.report-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.report-title {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.report-title-line {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.report-title-brand,
.report-title-text,
.report-title-line--secondary {
  font-size: 24px;
  font-weight: 700;
}

.report-title-line--secondary {
  letter-spacing: 0.08em;
}

.report-divider {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.report-divider-line {
  display: block;
  width: 100%;
  height: 1px;
  background: #1f2937;
}

.report-divider-line--primary {
  height: 2px;
}

.report-divider-line--secondary {
  background: #6b7280;
}

.report-number,
.report-generated-at,
.report-info-label,
.report-info-value,
.channel-summary-text,
.channel-preview-label,
.preview-footer,
.preview-disclaimer-line {
  font-size: 14.67px;
  font-weight: 400;
}

.report-number {
  text-align: right;
}

.report-generated-at {
  margin-top: 8px;
}


.report-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.report-info-divider {
  width: 100%;
  height: 1px;
  background: #000;
}

.report-info-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
}

.report-info-field {
  display: flex;
  gap: 4px;
  white-space: nowrap;
}

.report-info-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.report-info-detail {
  display: flex;
  gap: 4px;
}

.report-info-detail .report-info-value {
  white-space: pre-wrap;
}

.report-info-label {
  font-weight: 500;
}

.channel-summary-texts {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.channel-preview-label {
  text-align: center;
}

.preview-footer {
  margin-top: 16px;
  text-align: center;
}

.preview-disclaimer {
  margin-top: 16px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.channel-preview-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
}

.channel-preview-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.channel-preview-image {
  width: 100%;
  border-radius: 12px;
  background: #ffffff;
  border: 1px dashed rgba(148, 163, 184, 0.6);
  padding: 8px;
  object-fit: contain;
}

.preview-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 12px;
}

@media (max-width: 768px) {
  .preview-content {
    padding: 16px;
  }

  .mask-preview-image {
    height: 140px;
  }
}
</style>
