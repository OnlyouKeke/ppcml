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
                <el-form-item label="机构名称">
                  <el-input v-model="form.institutionName" placeholder="请输入机构名称" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="报告编号">
                  <el-input v-model="form.reportNumber" placeholder="请输入报告编号" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="检测日期">
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
                <el-form-item label="样本编号">
                  <el-input
                    v-model="form.sampleNumber"
                    :maxlength="sampleNumberMaxLength"
                    :disabled="!form.petType"
                    placeholder="请选择宠物类型后填写"
                    @input="handleSampleNumberInput"
                  />
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
                <el-form-item label="样本状态">
                  <el-radio-group v-model="form.sampleStatus">
                    <el-radio label="合格">合格</el-radio>
                    <el-radio label="不合格">不合格</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="宠物类型">
                  <el-radio-group v-model="form.petType">
                    <el-radio label="猫">猫</el-radio>
                    <el-radio label="狗">狗</el-radio>
                    <el-radio label="其他">其他</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="癌症标志物">
                  <el-input v-model="form.cancerBiomarker" placeholder="请输入癌症标志物" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="科别">
                  <el-input v-model="form.department" placeholder="请输入科别" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="标本类型">
                  <el-input v-model="form.sampleType" placeholder="请输入标本类型" clearable />
                </el-form-item>
              </el-col>
            </el-row>
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
                <el-form-item label="一周内是否有药物摄入">
                  <el-radio-group v-model="form.medicationIntake">
                    <el-radio label="是">是</el-radio>
                    <el-radio label="否">否</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
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
                  'mask-preview-item',
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
                  <div
                    v-for="(row, rowIndex) in previewInfoRows"
                    :key="rowIndex"
                    class="report-info-row"
                  >
                    <div
                      v-for="(field, fieldIndex) in row"
                      :key="fieldIndex"
                      class="report-info-cell"
                      :class="{
                        'report-info-cell--wide': field.span === 2,
                        'report-info-cell--full': field.span === 4
                      }"
                    >
                      <span class="report-info-label">{{ field.label }}：</span>
                      <span class="report-info-value">{{ field.value }}</span>
                    </div>
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
import { ElMessage } from 'element-plus'
import { isAxiosError } from 'axios'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { getHeartbeat, postExportCtcReport, postGenerateCtcReport } from '../api/api'
import type {
  CtcReportDocxResponse,
  CtcReportResponse,
  ReportMaskOption,
  ReportMetadataItem
} from '../types/api'

interface ChannelPreviewItem {
  label: string
  src: string
}

interface PreviewInfoField {
  label: string
  value: string
  span?: number
}

type FileWithRelativePath = File & { webkitRelativePath?: string }

const petTypePrefixes = {
  猫: 'CAT',
  狗: 'DOG',
  其他: 'OTH'
} as const

type PetType = keyof typeof petTypePrefixes

const disclaimerLines = [
  '声明：本检测结果仅供科研及临床辅助参考，不能作为唯一诊断依据。',
  '建议结合兽医临床表现、影像学及其他实验室检查综合判断。'
]

interface FormState {
  institutionName: string
  reportNumber: string
  detectionDate: string
  sampleNumber: string
  sampleVolume: string
  sampleStatus: '合格' | '不合格' | ''
  petType: '猫' | '狗' | '其他' | ''
  cancerBiomarker: string
  department: string
  petName: string
  ownerName: string
  gender: string
  age: string
  sampleType: string
  medicationIntake: '是' | '否' | ''
  notes: string
  outputDirPath: string
}

const form = reactive<FormState>({
  institutionName: '',
  reportNumber: '',
  detectionDate: '',
  sampleNumber: '',
  sampleVolume: '',
  sampleStatus: '',
  petType: '',
  cancerBiomarker: '',
  department: '',
  petName: '',
  ownerName: '',
  gender: '',
  age: '',
  sampleType: '',
  medicationIntake: '',
  notes: '',
  outputDirPath: ''
})

const sanitizeSampleNumberDigits = (value: string) => value.replace(/\D/g, '').slice(0, 7)

const buildSampleNumber = (digits: string, petType: string) => {
  const prefix = petTypePrefixes[petType as PetType]
  if (!prefix) {
    return digits
  }
  if (!digits) {
    return prefix
  }
  return `${prefix}${digits}`
}

const handleSampleNumberInput = (value: string) => {
  if (!form.petType) {
    const digitsOnly = sanitizeSampleNumberDigits(value)
    if (digitsOnly !== form.sampleNumber) {
      form.sampleNumber = digitsOnly
    }
    return
  }

  const prefix = petTypePrefixes[form.petType as PetType]
  const stripped = value.startsWith(prefix) ? value.slice(prefix.length) : value
  const digitsOnly = sanitizeSampleNumberDigits(stripped)
  const nextValue = buildSampleNumber(digitsOnly, form.petType)
  if (nextValue !== form.sampleNumber) {
    form.sampleNumber = nextValue
  }
}

const sampleNumberMaxLength = computed(() => {
  if (!form.petType) {
    return 7
  }
  const prefix = petTypePrefixes[form.petType as PetType]
  return prefix.length + 7
})

const getNormalizedSampleNumber = () => {
  const sanitizedValue = sanitizeText(form.sampleNumber)
  if (!sanitizedValue) {
    return ''
  }
  if (!form.petType) {
    return sanitizedValue.toUpperCase()
  }
  const digitsOnly = sanitizeSampleNumberDigits(sanitizedValue)
  return buildSampleNumber(digitsOnly, form.petType)
}

watch(
  () => form.petType,
  newValue => {
    if (!newValue) {
      form.sampleNumber = ''
      return
    }
    const digitsOnly = sanitizeSampleNumberDigits(form.sampleNumber)
    const nextValue = buildSampleNumber(digitsOnly, newValue)
    if (nextValue !== form.sampleNumber) {
      form.sampleNumber = nextValue
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
const reportToken = ref('')
const maskOptions = ref<ReportMaskOption[]>([])
const selectedMaskOptionIds = ref<string[]>([])
const maskDirectoryPath = ref('')
const previewError = ref('')
const previewWarnings = ref<string[]>([])
const isPreviewLoading = ref(false)
const isExporting = ref(false)

const requiredMaskSelectionCount = 3

const heartbeatIntervalMs = 5000
let heartbeatTimer: number | null = null
let heartbeatFailureCount = 0
let heartbeatDisconnectNotified = false

const roundnessThreshold = ref(0.3)

const hasReport = computed(() => Boolean(reportData.value))
const selectedMaskOptions = computed(() =>
  selectedMaskOptionIds.value
    .map(id => maskOptions.value.find(option => option.id === id) ?? null)
    .filter((option): option is ReportMaskOption => Boolean(option))
)
const isMaskSelectionComplete = computed(
  () => selectedMaskOptions.value.length === requiredMaskSelectionCount
)
const maskSelectionOrderMap = computed(() => {
  const order = new Map<string, number>()
  selectedMaskOptionIds.value.forEach((id, index) => {
    order.set(id, index + 1)
  })
  return order
})
const canDownloadReport = computed(
  () => Boolean(reportToken.value) && isMaskSelectionComplete.value
)

const sanitizeText = (value: string | null | undefined) => {
  if (!value) {
    return ''
  }
  const trimmed = value.trim()
  return trimmed === '' ? '' : trimmed
}

const formatDateForDisplay = (value: string) => {
  if (!value) {
    return ''
  }
  const match = value.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/)
  if (!match) {
    return value
  }
  const [, year, month, day] = match
  const monthNumber = Number(month)
  const dayNumber = Number(day)
  return `${year}年${monthNumber}月${dayNumber}日`
}

const wrapWithParentheses = (value: string) => {
  if (!value) {
    return '（未填写）'
  }
  const trimmed = value.trim()
  if (trimmed.startsWith('（') && trimmed.endsWith('）')) {
    return trimmed
  }
  return `（${trimmed}）`
}

const ensureValue = (value: string, fallback = '未填写') => (value ? value : fallback)

const formatSampleVolume = (value: string) => {
  if (!value) {
    return '未填写'
  }
  const compact = value.replace(/\s+/g, '')
  if (/ml$/i.test(compact)) {
    return value
  }
  return `${value} ml`
}

const formMetadataEntries = computed<ReportMetadataItem[]>(() => {
  const intakeValue = sanitizeText(form.medicationIntake)
  return [
    { label: '机构名称', value: sanitizeText(form.institutionName) },
    { label: '报告编号', value: sanitizeText(form.reportNumber) },
    { label: '检测日期', value: sanitizeText(form.detectionDate) },
    { label: '样本编号', value: getNormalizedSampleNumber() },
    { label: '样品量（单位ml）', value: sanitizeText(form.sampleVolume) },
    { label: '样本状态', value: sanitizeText(form.sampleStatus) },
    { label: '宠物类型', value: sanitizeText(form.petType) },
    { label: '癌症标志物', value: sanitizeText(form.cancerBiomarker) },
    { label: '科别', value: sanitizeText(form.department) },
    { label: '宠物姓名', value: sanitizeText(form.petName) },
    { label: '宠主姓名', value: sanitizeText(form.ownerName) },
    { label: '年龄', value: sanitizeText(form.age) },
    { label: '性别', value: sanitizeText(form.gender) },
    { label: '标本类型', value: sanitizeText(form.sampleType) },
    { label: '一周内是否有药物摄入', value: intakeValue },
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

const previewMetadataMap = computed(() => {
  const map = new Map<string, string>()
  previewMetadata.value.forEach(item => {
    if (item) {
      map.set(item.label, sanitizeText(item.value))
    }
  })
  return map
})

const getPreviewMetadataValue = (label: string) => previewMetadataMap.value.get(label) ?? ''

const previewNotesDisplay = computed(() => {
  const value = getPreviewMetadataValue('备注')
  return value || '无'
})

const reportNumberDisplay = computed(() => {
  const value = getPreviewMetadataValue('报告编号')
  return value ? `[${value}]` : '[未填写]'
})

const previewInfoRows = computed<PreviewInfoField[][]>(() => {
  const getValue = (label: string) => getPreviewMetadataValue(label)
  const detectionDate = formatDateForDisplay(getValue('检测日期'))
  return [
    [
      { label: '送检单位', value: wrapWithParentheses(getValue('机构名称')) },
      { label: '宠主姓名', value: wrapWithParentheses(getValue('宠主姓名')) },
      { label: '宠物姓名', value: wrapWithParentheses(getValue('宠物姓名')) },
      { label: '受检宠物', value: wrapWithParentheses(getValue('宠物类型')) }
    ],
    [
      { label: '送检日期', value: wrapWithParentheses(detectionDate) },
      { label: '年龄', value: wrapWithParentheses(getValue('年龄')) },
      { label: '性别', value: wrapWithParentheses(getValue('性别')) },
      { label: '标本类型', value: wrapWithParentheses(getValue('标本类型')) }
    ],
    [
      { label: '样本编号', value: wrapWithParentheses(getValue('样本编号')) },
      { label: '样本状态', value: ensureValue(getValue('样本状态')) },
      { label: '样品量', value: formatSampleVolume(getValue('样品量（单位ml）')) },
      { label: '癌症标志物', value: wrapWithParentheses(getValue('癌症标志物')) }
    ],
    [
      { label: '科别', value: wrapWithParentheses(getValue('科别')) },
      {
        label: '药物摄入情况',
        value: ensureValue(getValue('一周内是否有药物摄入'))
      },
      { label: '备注', value: previewNotesDisplay.value, span: 2 }
    ]
  ]
})

const channelSummaryTexts = computed(() => {
  const texts = reportData.value?.channelSummaryTexts ?? []
  return texts
    .map(text => sanitizeText(text))
    .filter((text): text is string => Boolean(text))
})

const selectedMaskPreviewItems = computed<ChannelPreviewItem[]>(() => {
  if (!isMaskSelectionComplete.value) {
    return []
  }
  return selectedMaskOptions.value.map(option => ({
    label: option.label,
    src: `data:${option.mimeType};base64,${option.data}`
  }))
})

const channelPreviewItems = computed<ChannelPreviewItem[]>(() => {
  if (selectedMaskPreviewItems.value.length) {
    return selectedMaskPreviewItems.value
  }
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

const toggleMaskSelection = (optionId: string) => {
  const currentIndex = selectedMaskOptionIds.value.indexOf(optionId)
  if (currentIndex >= 0) {
    selectedMaskOptionIds.value.splice(currentIndex, 1)
    return
  }

  if (selectedMaskOptionIds.value.length >= requiredMaskSelectionCount) {
    ElMessage.warning(`最多只能选择${requiredMaskSelectionCount}张掩码图像`)
    return
  }

  selectedMaskOptionIds.value.push(optionId)
}

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
  reportToken.value = ''
  maskOptions.value = []
  selectedMaskOptionIds.value = []
  isExporting.value = false
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

const applyReportBlob = (data: { fileContent?: string } | CtcReportDocxResponse) => {
  if (!data.fileContent) {
    return
  }
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

  const outputDirPath = form.outputDirPath.trim()
  if (!outputDirPath) {
    ElMessage.warning('请先填写输出文件夹路径')
    return
  }

  form.outputDirPath = outputDirPath

  previewError.value = ''
  previewWarnings.value = []
  isPreviewLoading.value = true
  maskDirectoryPath.value = ''

  if (generatedReportUrl.value) {
    revokeObjectUrl(generatedReportUrl.value)
    generatedReportUrl.value = ''
  }
  generatedReportBlob.value = null
  reportToken.value = ''
  maskOptions.value = []
  selectedMaskOptionIds.value = []
  reportData.value = null

  try {
    console.info('[Report] 开始请求后端生成报告', {
      folder: selectedFolderName.value,
      fileCount: selectedFiles.value.length,
      roundnessThreshold: roundnessThreshold.value,
      outputDirPath
    })
    isDetecting.value = true
    startHeartbeat()
    const response = await postGenerateCtcReport({
      files: selectedFiles.value,
      form: {
        institutionName: form.institutionName,
        reportNumber: form.reportNumber,
        detectionDate: form.detectionDate,
        sampleNumber: getNormalizedSampleNumber(),
        sampleVolume: form.sampleVolume,
        sampleStatus: form.sampleStatus,
        petType: form.petType,
        cancerBiomarker: form.cancerBiomarker,
        department: form.department,
        petName: form.petName,
        ownerName: form.ownerName,
        age: form.age,
        gender: form.gender,
        sampleType: form.sampleType,
        medicationIntake: form.medicationIntake,
        notes: form.notes
      },
      roundnessThreshold: roundnessThreshold.value,
      previewOnly: true,
      outputDir: outputDirPath
    })

    reportData.value = response
    reportToken.value = response.reportToken ?? ''
    maskOptions.value = response.maskOptions ?? []
    const responseMaskInputDir = (response.maskInputDirectory ?? '').trim()
    const responseUserOutputDir = (response.userOutputDirectory ?? '').trim()
    maskDirectoryPath.value =
      responseUserOutputDir || responseMaskInputDir || outputDirPath
    const importedMaskOptions = maskOptions.value.filter(option =>
      option.id.startsWith('external::') || option.channel === 'external'
    )
    if (responseMaskInputDir && importedMaskOptions.length) {
      selectedMaskOptionIds.value = importedMaskOptions
        .slice(0, requiredMaskSelectionCount)
        .map(option => option.id)
    } else {
      selectedMaskOptionIds.value = []
    }
    previewWarnings.value = response.warnings ?? []
    if (
      maskOptions.value.length > 0 &&
      maskOptions.value.length < requiredMaskSelectionCount
    ) {
      ElMessage.warning(
        `仅检测到 ${maskOptions.value.length} 张掩码图像，请确认影像数据是否完整`
      )
    }
    ElMessage.success('报告生成成功，预览已同步更新')
  } catch (error) {
    previewError.value = '报告生成失败，请稍后重试。'
    if (isAxiosError(error)) {
      if (error.code === 'ERR_NETWORK') {
        console.error('[Report] 无法连接后端服务', error)
        ElMessage.error('无法连接后端服务，请确认FastAPI接口已启动（默认端口范围 15000-15003）。')
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

const downloadDocx = async () => {
  if (!reportToken.value) {
    ElMessage.warning('请先生成预览，再导出 Word 文件')
    return
  }

  if (!isMaskSelectionComplete.value) {
    ElMessage.warning(`请选择${requiredMaskSelectionCount}张掩码图像后再导出`)
    return
  }

  try {
    isExporting.value = true
    const response = await postExportCtcReport({
      reportToken: reportToken.value,
      maskOptionIds: [...selectedMaskOptionIds.value]
    })

    applyReportBlob(response)
    reportToken.value = response.reportToken ?? reportToken.value

    if (!generatedReportBlob.value || !generatedReportUrl.value) {
      ElMessage.error('导出 Word 文件失败，请稍后重试')
      return
    }

    const downloadName = `${selectedFolderName.value || 'ctc_dataset'}-report.docx`
    const link = document.createElement('a')
    link.href = generatedReportUrl.value
    link.download = downloadName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success('Word 报告已生成并开始下载')
  } catch (error) {
    if (isAxiosError(error)) {
      console.error('[Report] 导出 Word 报告失败', error)
      if (error.code === 'ERR_NETWORK') {
        ElMessage.error('无法连接后端服务，导出失败')
      } else {
        ElMessage.error('导出 Word 报告失败，请稍后重试')
      }
    } else {
      console.error('[Report] 导出 Word 报告时出现异常', error)
      ElMessage.error('导出 Word 报告失败，请稍后重试')
    }
  } finally {
    isExporting.value = false
  }
}

const resetAll = () => {
  form.institutionName = ''
  form.reportNumber = ''
  form.detectionDate = ''
  form.sampleNumber = ''
  form.sampleVolume = ''
  form.sampleStatus = ''
  form.petType = ''
  form.cancerBiomarker = ''
  form.department = ''
  form.petName = ''
  form.ownerName = ''
  form.gender = ''
  form.age = ''
  form.sampleType = ''
  form.medicationIntake = ''
  form.notes = ''
  form.outputDirPath = ''
  resetSelectedFolder()
  maskDirectoryPath.value = ''
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

const beforeUpload = (file: File) => {
  // Validate folder (optional, can add checks here)
  if (file.type === '') { // indicates directory
    return true
  }
  ElMessage.error('请选择文件夹')
  return false
}

const triggerOutputFolderSelection = async () => {
  if (!window.electronAPI?.selectDirectory) {
    ElMessage.warning('当前环境不支持文件夹选择，请手动输入输出路径')
    return
  }

  try {
    const selectedPath = await window.electronAPI.selectDirectory({
      title: '选择输出文件夹',
      buttonLabel: '选择',
      properties: ['openDirectory', 'createDirectory']
    })

    if (selectedPath) {
      form.outputDirPath = selectedPath
    }
  } catch (error) {
    console.error('[Report] 选择输出文件夹失败', error)
    ElMessage.error('选择输出文件夹时出现问题，请重试')
  }
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
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-card,
.mask-card,
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

.output-folder-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.output-folder-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.output-folder-input :deep(.el-input-group__append) {
  padding: 0;
}

.output-folder-input :deep(.el-button) {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

.output-folder-label {
  display: inline-block;
  min-width: 32px;
  color: #1f2937;
}

.output-folder-path {
  font-size: 13px;
  color: #4b5563;
  word-break: break-all;
}

.output-folder-tip {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.5;
  word-break: break-all;
}

.mask-selection {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mask-instruction {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
}

.mask-directory {
  font-size: 12px;
  color: #4b5563;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 8px;
  padding: 8px 12px;
  line-height: 1.6;
  border: 1px solid rgba(99, 102, 241, 0.18);
  word-break: break-all;
}

.mask-directory-path {
  font-weight: 600;
  color: #1e3a8a;
}

.mask-loading {
  padding: 8px 0 4px;
}

.mask-placeholder {
  font-size: 13px;
  color: #6b7280;
  background: rgba(243, 244, 246, 0.9);
  border-radius: 12px;
  padding: 14px 16px;
  line-height: 1.6;
}

.mask-options-wrapper {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mask-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.mask-preview-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(99, 102, 241, 0.2);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(226, 232, 240, 0.75) 100%);
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.mask-preview-item:hover {
  border-color: #6366f1;
  box-shadow: 0 12px 24px rgba(99, 102, 241, 0.18);
  transform: translateY(-2px);
}

.mask-preview-item.active {
  border-color: #4f46e5;
  box-shadow: 0 16px 28px rgba(79, 70, 229, 0.25);
}

.mask-preview-image {
  width: 100%;
  border-radius: 10px;
  object-fit: cover;
  box-shadow: 0 8px 18px rgba(79, 70, 229, 0.22);
}

.mask-preview-label {
  font-size: 12px;
  font-weight: 600;
  color: #1e3a8a;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.mask-selected-tip {
  font-size: 13px;
  font-weight: 600;
  color: #4338ca;
}

.mask-selection-order {
  background: rgba(99, 102, 241, 0.12);
  border: none;
  color: #4338ca;
}

.mask-selection-warning {
  font-size: 12px;
  color: #b91c1c;
  background: rgba(248, 113, 113, 0.12);
  border-radius: 10px;
  padding: 10px 12px;
}

.mask-empty {
  padding: 18px 0;
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
.el-empty,
.preview-blocker {
  width: 100%;
}

.preview-content {
  display: flex;
  flex-direction: column;
  width: 100%;
  background: transparent;
  box-shadow: none;
  padding: 0;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.report-preview {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(254, 242, 242, 0.94) 100%);
  border-radius: 18px;
  padding: 28px 32px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  border: 1px solid rgba(220, 38, 38, 0.18);
  box-shadow: 0 18px 36px rgba(185, 28, 28, 0.12);
  min-height: 100%;
}

.report-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.report-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: center;
}

.report-title-line {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
  font-weight: 700;
  color: #111827;
  font-size: 20px;
}

.report-title-brand {
  font-size: 28px;
  color: #dc2626;
  font-family: 'Times New Roman', 'SimSun', serif;
  letter-spacing: 0.08em;
}

.report-title-line--secondary {
  font-size: 18px;
}

.report-divider {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.report-divider-line {
  display: block;
  width: 100%;
  border-radius: 999px;
}

.report-divider-line--primary {
  height: 3px;
  background: linear-gradient(
    90deg,
    rgba(220, 38, 38, 0) 0%,
    rgba(220, 38, 38, 0.55) 18%,
    rgba(220, 38, 38, 0.9) 50%,
    rgba(220, 38, 38, 0.55) 82%,
    rgba(220, 38, 38, 0) 100%
  );
}

.report-divider-line--secondary {
  height: 1px;
  background: rgba(15, 23, 42, 0.18);
}

.report-number {
  align-self: flex-end;
  font-size: 14px;
  font-weight: 600;
  color: #b91c1c;
}

.report-generated-at {
  align-self: flex-end;
  font-size: 12px;
  color: #6b7280;
}

.report-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-info-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.report-info-cell {
  border: 1px solid rgba(220, 38, 38, 0.25);
  border-radius: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.96);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 46px;
  box-shadow: 0 4px 10px rgba(220, 38, 38, 0.08);
}

.report-info-cell--wide {
  grid-column: span 2;
}

.report-info-cell--full {
  grid-column: span 4;
}

.report-info-label {
  font-weight: 600;
  color: #991b1b;
  white-space: nowrap;
}

.report-info-value {
  color: #111827;
  word-break: break-word;
}

.report-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 1px dashed rgba(220, 38, 38, 0.3);
  padding-top: 16px;
}

.channel-summary-texts {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.preview-blocker {
  display: flex;
  align-items: center;
  justify-content: center;
}

.channel-summary-text {
  margin: 0;
  font-size: 12px;
  color: #475569;
  text-align: left;
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

.preview-disclaimer {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  line-height: 1.6;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-disclaimer-line {
  margin: 0;
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

  .report-preview {
    padding: 24px 20px 28px;
  }

  .report-info-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .preview-actions {
    justify-content: center;
  }
}

@media (max-width: 600px) {
  .report-preview {
    padding: 20px 16px 24px;
  }

  .report-info-row {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }

  .report-info-cell--wide,
  .report-info-cell--full {
    grid-column: span 1;
  }
}
</style>
