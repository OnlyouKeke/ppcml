<template>
  <div class="report-builder">
    <el-page-header content="宠物检测报告生成中心" class="page-header" />

    <el-row :gutter="24" class="layout">
      <el-col :xs="24" :md="10" class="form-column">
        <el-card shadow="hover" class="form-card">
          <template #header>
            <div class="card-title">基础信息填写</div>
          </template>
          <el-form :model="form" label-width="92px" label-position="left" class="info-form">
            <el-form-item label="宠物姓名">
              <el-input v-model="form.petName" placeholder="请输入宠物姓名" clearable />
            </el-form-item>
            <el-form-item label="性别">
              <el-select v-model="form.gender" placeholder="请选择性别" clearable>
                <el-option label="公" value="公" />
                <el-option label="母" value="母" />
                <el-option label="未知" value="未知" />
              </el-select>
            </el-form-item>
            <el-form-item label="年龄">
              <el-input v-model="form.age" placeholder="例如：2岁3个月" clearable />
            </el-form-item>
            <el-form-item label="品种">
              <el-input v-model="form.species" placeholder="请输入宠物品种" clearable />
            </el-form-item>
            <el-form-item label="主人姓名">
              <el-input v-model="form.ownerName" placeholder="请输入主人姓名" clearable />
            </el-form-item>
            <el-form-item label="备注信息">
              <el-input
                v-model="form.notes"
                type="textarea"
                :rows="3"
                placeholder="记录额外说明，例如既往病史、当前症状等"
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

        <el-card shadow="never" class="result-card">
          <template #header>
            <div class="card-title">识别结果</div>
          </template>
          <el-empty v-if="!detections.length" description="暂未识别到内容" :image-size="120" />
          <el-table
            v-else
            :data="detectionTable"
            border
            size="small"
            class="result-table"
            height="240"
          >
            <el-table-column prop="index" label="序号" width="70" align="center" />
            <el-table-column prop="className" label="类别" min-width="120" />
            <el-table-column prop="confidence" label="置信度" width="110" align="center" />
            <el-table-column prop="box" label="位置信息" min-width="180" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="14" class="preview-column">
        <el-card shadow="hover" class="preview-card">
          <template #header>
            <div class="card-title">报告预览与导出</div>
          </template>
          <div class="preview-wrapper">
            <canvas ref="canvasRef" class="report-canvas"></canvas>
          </div>
          <div class="preview-actions">
            <el-button type="success" :disabled="!canDownloadReport" @click="downloadDocx">
              导出 Word 报告
            </el-button>
            <el-button type="primary" :disabled="!hasReport" @click="exportToPdf">导出为 PDF</el-button>
            <el-button :disabled="!hasReport" @click="downloadImage">下载图片</el-button>
            <el-button @click="resetAll">重置内容</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script lang="ts" setup>
import { ElMessage } from 'element-plus'
import { isAxiosError } from 'axios'
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { getHeartbeat, postGenerateCtcReport } from '../api/api'
import type { Detection } from '../types/api'

type FileWithRelativePath = File & { webkitRelativePath?: string }

interface FormState {
  petName: string
  gender: string
  age: string
  species: string
  ownerName: string
  notes: string
}

const form = reactive<FormState>({
  petName: '',
  gender: '',
  age: '',
  species: '',
  ownerName: '',
  notes: ''
})

const selectedFiles = ref<FileWithRelativePath[]>([])
const selectedFolderName = ref('')
const folderFileCount = ref(0)
const fileInputRef = ref<HTMLInputElement | null>(null)
const imageSrc = ref('')
const detections = ref<Detection[]>([])
const isDetecting = ref(false)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const roundnessThreshold = ref(0.3)
const generatedReportBlob = ref<Blob | null>(null)
const generatedReportUrl = ref('')
const previewImageUrl = ref('')

const heartbeatIntervalMs = 5000
let heartbeatTimer: number | null = null
let heartbeatFailureCount = 0
let heartbeatDisconnectNotified = false

const hasReport = computed(() => Boolean(imageSrc.value))
const canDownloadReport = computed(() => Boolean(generatedReportBlob.value))

const detectionTable = computed(() =>
  detections.value.map((item, index) => ({
    index: index + 1,
    className: item.class_name || '未知目标',
    confidence: `${(item.confidence * 100).toFixed(1)}%`,
    box: `(${item.box.xmin.toFixed(0)}, ${item.box.ymin.toFixed(0)}) - (${item.box.xmax.toFixed(0)}, ${item.box.ymax.toFixed(0)})`
  }))
)

const expectedChannels = ['1', '2', '3', '4', '5']

const revokeObjectUrl = (url: string) => {
  if (url) {
    window.URL.revokeObjectURL(url)
  }
}

const resetSelectedFolder = () => {
  selectedFiles.value = []
  selectedFolderName.value = ''
  folderFileCount.value = 0
  if (generatedReportUrl.value) {
    revokeObjectUrl(generatedReportUrl.value)
    generatedReportUrl.value = ''
  }
  generatedReportBlob.value = null
  if (previewImageUrl.value) {
    revokeObjectUrl(previewImageUrl.value)
    previewImageUrl.value = ''
  }
}

const updatePreviewImage = () => {
  if (!selectedFiles.value.length) {
    imageSrc.value = ''
    return
  }

  const imageFile =
    selectedFiles.value.find(file => file.type.startsWith('image/')) ||
    selectedFiles.value.find(file => /\.(png|jpe?g|bmp|gif)$/i.test(file.name)) ||
    null

  if (!imageFile) {
    if (generatedReportBlob.value) {
      ElMessage.warning('报告已生成，但未找到可用于预览的图像文件')
    }
    imageSrc.value = ''
    return
  }

  if (previewImageUrl.value) {
    revokeObjectUrl(previewImageUrl.value)
  }

  const url = window.URL.createObjectURL(imageFile)
  previewImageUrl.value = url
  imageSrc.value = url
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
  detections.value = []
  imageSrc.value = ''
  scheduleRender()
}

const runDetection = async () => {
  if (!selectedFiles.value.length) {
    ElMessage.warning('请先选择包含影像的文件夹')
    return
  }

  if (generatedReportUrl.value) {
    revokeObjectUrl(generatedReportUrl.value)
    generatedReportUrl.value = ''
  }
  generatedReportBlob.value = null

  try {
    console.info('[Report] 开始请求后端生成报告', {
      folder: selectedFolderName.value,
      fileCount: selectedFiles.value.length,
      roundnessThreshold: roundnessThreshold.value
    })
    isDetecting.value = true
    startHeartbeat()
    const blob = await postGenerateCtcReport({
      files: selectedFiles.value,
      form: {
        petName: form.petName,
        ownerName: form.ownerName,
        age: form.age,
        gender: form.gender,
        species: form.species,
        notes: form.notes,
        sampleType: '',
        massLocation: ''
      },
      roundnessThreshold: roundnessThreshold.value
    })

    generatedReportBlob.value = blob
    const url = window.URL.createObjectURL(blob)
    generatedReportUrl.value = url
    updatePreviewImage()

    ElMessage.success('报告生成成功，请在预览区域手动导出')
  } catch (error) {
    if (isAxiosError(error)) {
      if (error.code === 'ERR_NETWORK') {
        console.error('[Report] 无法连接后端服务', error)
        ElMessage.error('无法连接后端服务，请确认FastAPI接口已启动（默认端口 8001）。')
      } else if (error.code === 'ECONNABORTED') {
        console.error('[Report] 生成报告请求超时', error)
        ElMessage.error('生成报告超时，请检查后端处理是否正常或稍后重试')
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
    if (!generatedReportBlob.value && generatedReportUrl.value) {
      revokeObjectUrl(generatedReportUrl.value)
      generatedReportUrl.value = ''
    }
  }
}

const resetAll = () => {
  form.petName = ''
  form.gender = ''
  form.age = ''
  form.species = ''
  form.ownerName = ''
  form.notes = ''
  detections.value = []
  imageSrc.value = ''
  resetSelectedFolder()
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  scheduleRender()
}

const downloadImage = () => {
  const canvas = canvasRef.value
  if (!canvas) {
    return
  }

  const link = document.createElement('a')
  link.href = canvas.toDataURL('image/png')
  link.download = `宠物检测报告-${form.petName || '未命名'}.png`
  link.click()
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

const exportToPdf = () => {
  const canvas = canvasRef.value
  if (!canvas) {
    return
  }

  const dataUrl = canvas.toDataURL('image/png')
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('无法打开打印窗口，请检查浏览器设置')
    return
  }

  printWindow.document.write(`<!DOCTYPE html><html><head><title>宠物检测报告</title>`)
  printWindow.document.write(
    '<style>body{margin:0;padding:24px;font-family:\'Microsoft YaHei\',sans-serif;background:#f3f4f6;}' +
      'img{width:100%;max-width:900px;display:block;margin:0 auto;box-shadow:0 12px 32px rgba(15,23,42,0.12);border-radius:16px;}</style>'
  )
  printWindow.document.write('</head><body>')
  printWindow.document.write(`<img src="${dataUrl}" alt="宠物检测报告" />`)
  printWindow.document.write('</body></html>')
  printWindow.document.close()
  printWindow.focus()
  printWindow.print()
}

onBeforeUnmount(() => {
  stopHeartbeat()
  if (generatedReportUrl.value) {
    revokeObjectUrl(generatedReportUrl.value)
    generatedReportUrl.value = ''
  }
  if (previewImageUrl.value) {
    revokeObjectUrl(previewImageUrl.value)
    previewImageUrl.value = ''
  }
})

const scheduleRender = () => {
  nextTick(() => {
    void drawReport()
  })
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

const drawReport = async () => {
  const canvas = canvasRef.value
  if (!canvas) {
    return
  }

  const context = canvas.getContext('2d')
  if (!context) {
    return
  }

  if (!imageSrc.value) {
    drawPlaceholder(canvas, context)
    return
  }

  try {
    const image = await loadImage(imageSrc.value)
    renderCanvasWithData(canvas, context, image, detections.value)
  } catch (error) {
    console.error('渲染报告失败:', error)
    drawPlaceholder(canvas, context)
  }
}

const loadImage = (src: string): Promise<HTMLImageElement> =>
  new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })

const roundedRectPath = (
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number
) => {
  const effectiveRadius = Math.min(radius, width / 2, height / 2)
  ctx.beginPath()
  ctx.moveTo(x + effectiveRadius, y)
  ctx.lineTo(x + width - effectiveRadius, y)
  ctx.quadraticCurveTo(x + width, y, x + width, y + effectiveRadius)
  ctx.lineTo(x + width, y + height - effectiveRadius)
  ctx.quadraticCurveTo(x + width, y + height, x + width - effectiveRadius, y + height)
  ctx.lineTo(x + effectiveRadius, y + height)
  ctx.quadraticCurveTo(x, y + height, x, y + height - effectiveRadius)
  ctx.lineTo(x, y + effectiveRadius)
  ctx.quadraticCurveTo(x, y, x + effectiveRadius, y)
  ctx.closePath()
}

const fillRoundedRect = (
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
  fillStyle: string
) => {
  ctx.save()
  ctx.fillStyle = fillStyle
  roundedRectPath(ctx, x, y, width, height, radius)
  ctx.fill()
  ctx.restore()
}

const strokeRoundedRect = (
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
  strokeStyle: string,
  lineWidth = 1,
  dash: number[] = []
) => {
  ctx.save()
  ctx.strokeStyle = strokeStyle
  ctx.lineWidth = lineWidth
  ctx.setLineDash(dash)
  roundedRectPath(ctx, x, y, width, height, radius)
  ctx.stroke()
  ctx.restore()
}

const drawPlaceholder = (canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D) => {
  const baseWidth = 900
  const baseHeight = 620
  const outerPadding = 32
  const cardRadius = 24
  const accentHeight = 8

  canvas.width = baseWidth
  canvas.height = baseHeight

  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(0, 0, baseWidth, baseHeight)

  const cardWidth = baseWidth - outerPadding * 2
  const cardHeight = baseHeight - outerPadding * 2
  fillRoundedRect(ctx, outerPadding, outerPadding, cardWidth, cardHeight, cardRadius, '#ffffff')
  fillRoundedRect(ctx, outerPadding, outerPadding, cardWidth, accentHeight, cardRadius, '#2563eb')

  ctx.textAlign = 'center'
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 28px "Microsoft YaHei", sans-serif'
  ctx.fillText('宠物健康检测报告', baseWidth / 2, outerPadding + 56)

  ctx.font = '16px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = '#475569'
  ctx.fillText('请填写宠物信息并上传五个通道的影像文件夹以生成报告', baseWidth / 2, outerPadding + 100)

  const hintX = outerPadding + 60
  const hintY = outerPadding + 140
  const hintWidth = cardWidth - 120
  const hintHeight = 220
  fillRoundedRect(ctx, hintX, hintY, hintWidth, hintHeight, 20, 'rgba(37, 99, 235, 0.08)')
  strokeRoundedRect(ctx, hintX, hintY, hintWidth, hintHeight, 20, 'rgba(37, 99, 235, 0.2)', 2, [10, 8])

  ctx.fillStyle = '#1d4ed8'
  ctx.font = 'bold 18px "Microsoft YaHei", sans-serif'
  ctx.fillText('等待影像文件上传...', baseWidth / 2, hintY + hintHeight / 2)

  ctx.font = '15px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = '#64748b'
  ctx.fillText('确保包含五个荧光通道，并选择同一区域的代表性图像以提升分析质量', baseWidth / 2, hintY + hintHeight / 2 + 38)

  ctx.textAlign = 'left'
}

const renderCanvasWithData = (
  canvas: HTMLCanvasElement,
  ctx: CanvasRenderingContext2D,
  image: HTMLImageElement,
  detectionData: Detection[]
) => {
  const baseWidth = 900
  const outerPadding = 32
  const cardRadius = 24
  const cardPadding = 32
  const accentHeight = 8
  const sectionGap = 28
  const smallGap = 18
  const infoLineHeight = 28
  const detectionLineHeight = 26
  const conclusionLineHeight = 26
  const infoFont = '16px "Microsoft YaHei", sans-serif'
  const detectionFont = '15px "Microsoft YaHei", sans-serif'
  const timestamp = new Date().toLocaleString()

  const maxImageWidth = baseWidth - (outerPadding + cardPadding) * 2
  const scale = Math.min(1, maxImageWidth / image.width)
  const imageWidth = Math.round(image.width * scale)
  const imageHeight = Math.round(image.height * scale)

  const measureCtx = document.createElement('canvas').getContext('2d')
  if (!measureCtx) {
    return
  }
  measureCtx.font = infoFont

  const infoLines: string[] = []
  const entries: Array<{ label: string; value: string }> = [
    { label: '宠物姓名', value: form.petName || '未填写' },
    { label: '性别', value: form.gender || '未填写' },
    { label: '年龄', value: form.age || '未填写' },
    { label: '品种', value: form.species || '未填写' },
    { label: '主人', value: form.ownerName || '未填写' }
  ]

  entries.forEach(item => {
    infoLines.push(`${item.label}：${item.value}`)
  })

  const noteContent = form.notes.trim() || '无'
  const infoAreaWidth = baseWidth - (outerPadding + cardPadding) * 2
  const noteLines = wrapText(measureCtx, noteContent, infoAreaWidth - measureCtx.measureText('备注：').width)
  infoLines.push(`备注：${noteLines.shift() || '无'}`)
  noteLines.forEach(line => {
    infoLines.push(`        ${line}`)
  })

  const detectionLines = detectionData.length
    ? detectionData.map((item, index) =>
        `目标${index + 1}：${item.class_name || '未知目标'}，置信度 ${(item.confidence * 100).toFixed(1)}%`
      )
    : ['当前图像未检测到显著目标']

  const totalDetections = detectionData.length
  const highlightMessage = totalDetections
    ? `在当前图像中识别出 ${totalDetections} 个疑似目标，建议结合其他通道进一步确认。`
    : '当前图像未识别到异常信号，请继续检查其他通道与更多样本。'

  const infoBoxPadding = 18
  const summaryBoxPadding = 20
  const conclusionBoxPadding = 18
  const infoBoxHeight = infoLines.length * infoLineHeight + infoBoxPadding * 2
  const detectionBoxHeight = detectionLines.length * detectionLineHeight + summaryBoxPadding * 2 + detectionLineHeight
  const conclusionLines = [
    totalDetections
      ? `结果：检测到 ${totalDetections} 个疑似细胞，请结合图像质量和其他通道进行综合判断。`
      : '结果：当前图像未发现明显异常细胞，请结合其他通道继续排查。',
    '建议：报告仅供临床诊断参考，建议结合既往病史和实验室指标综合评估。'
  ]
  const conclusionBoxHeight = conclusionLines.length * conclusionLineHeight + conclusionBoxPadding * 2
  const footerHeight = 50
  const titleBlockHeight = 80

  const cardHeight =
    cardPadding +
    titleBlockHeight +
    sectionGap +
    infoBoxHeight +
    sectionGap +
    imageHeight +
    sectionGap +
    detectionBoxHeight +
    sectionGap +
    conclusionBoxHeight +
    footerHeight

  canvas.width = baseWidth
  canvas.height = Math.round(cardHeight + outerPadding * 2)

  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  const cardWidth = baseWidth - outerPadding * 2
  const cardHeightActual = canvas.height - outerPadding * 2
  fillRoundedRect(ctx, outerPadding, outerPadding, cardWidth, cardHeightActual, cardRadius, '#ffffff')
  fillRoundedRect(ctx, outerPadding, outerPadding, cardWidth, accentHeight, cardRadius, '#2563eb')

  let currentY = outerPadding + cardPadding
  const centerX = outerPadding + cardWidth / 2

  ctx.textAlign = 'center'
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 30px "Microsoft YaHei", sans-serif'
  ctx.fillText('宠物健康检测报告', centerX, currentY + 30)

  ctx.font = '16px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = '#64748b'
  ctx.fillText(`生成时间：${timestamp}`, centerX, currentY + 62)
  ctx.textAlign = 'left'

  currentY += titleBlockHeight

  ctx.font = 'bold 18px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = '#f97316'
  ctx.fillText('最新填写的信息', outerPadding + cardPadding, currentY)
  currentY += smallGap

  const infoBoxY = currentY
  const infoBoxWidth = cardWidth - cardPadding * 2
  fillRoundedRect(ctx, outerPadding + cardPadding, infoBoxY, infoBoxWidth, infoBoxHeight, 16, '#fff7ed')

  ctx.font = infoFont
  ctx.fillStyle = '#0f172a'
  let textY = infoBoxY + infoBoxPadding + 4
  const textX = outerPadding + cardPadding + infoBoxPadding
  infoLines.forEach(line => {
    ctx.fillText(line, textX, textY)
    textY += infoLineHeight
  })

  currentY = infoBoxY + infoBoxHeight + sectionGap

  const imageX = outerPadding + cardPadding
  const imageY = currentY
  fillRoundedRect(ctx, imageX - 12, imageY - 12, imageWidth + 24, imageHeight + 24, 18, '#e2e8f0')
  ctx.drawImage(image, imageX, imageY, imageWidth, imageHeight)

  const scaleX = imageWidth / image.width
  const scaleY = imageHeight / image.height

  detectionData.forEach(item => {
    const x = imageX + item.box.xmin * scaleX
    const y = imageY + item.box.ymin * scaleY
    const width = (item.box.xmax - item.box.xmin) * scaleX
    const height = (item.box.ymax - item.box.ymin) * scaleY

    ctx.strokeStyle = '#2563eb'
    ctx.lineWidth = 2
    ctx.strokeRect(x, y, width, height)

    const label = `${item.class_name || '目标'} ${(item.confidence * 100).toFixed(1)}%`
    ctx.font = 'bold 13px "Microsoft YaHei", sans-serif'
    const labelWidth = ctx.measureText(label).width + 16
    const labelHeight = 24
    let labelY = y
    if (labelY - labelHeight < imageY) {
      labelY = y + labelHeight
    }
    ctx.fillStyle = 'rgba(37, 99, 235, 0.85)'
    fillRoundedRect(ctx, x, labelY - labelHeight, labelWidth, labelHeight, 8, 'rgba(37, 99, 235, 0.85)')
    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, x + 8, labelY - 7)
  })

  currentY = imageY + imageHeight + sectionGap

  ctx.font = 'bold 18px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = '#2563eb'
  ctx.fillText('检测结果摘要', outerPadding + cardPadding, currentY)
  currentY += smallGap

  const summaryBoxY = currentY
  const summaryBoxWidth = cardWidth - cardPadding * 2
  fillRoundedRect(ctx, outerPadding + cardPadding, summaryBoxY, summaryBoxWidth, detectionBoxHeight, 16, '#eff6ff')

  ctx.font = 'bold 16px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = totalDetections ? '#dc2626' : '#1d4ed8'
  ctx.fillText(highlightMessage, textX, summaryBoxY + summaryBoxPadding + 4)

  ctx.font = detectionFont
  ctx.fillStyle = '#1f2937'
  let detectionY = summaryBoxY + summaryBoxPadding + detectionLineHeight + 4
  detectionLines.forEach(line => {
    ctx.beginPath()
    ctx.fillStyle = '#3b82f6'
    ctx.arc(textX - 10, detectionY - 7, 3, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = '#1f2937'
    ctx.fillText(line, textX, detectionY)
    detectionY += detectionLineHeight
  })

  currentY = summaryBoxY + detectionBoxHeight + sectionGap

  ctx.font = 'bold 18px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = '#15803d'
  ctx.fillText('结论与建议', outerPadding + cardPadding, currentY)
  currentY += smallGap

  const conclusionBoxY = currentY
  fillRoundedRect(ctx, outerPadding + cardPadding, conclusionBoxY, summaryBoxWidth, conclusionBoxHeight, 16, '#dcfce7')

  ctx.font = '16px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = '#166534'
  let conclusionY = conclusionBoxY + conclusionBoxPadding + 4
  conclusionLines.forEach(line => {
    ctx.fillText(line, textX, conclusionY)
    conclusionY += conclusionLineHeight
  })

  currentY = conclusionBoxY + conclusionBoxHeight + sectionGap

  ctx.font = '14px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = '#64748b'
  ctx.textAlign = 'center'
  ctx.fillText(
    '检测人：______________    审核人：______________    报告日期：______________',
    centerX,
    currentY + 24
  )
  ctx.textAlign = 'left'
}

const wrapText = (ctx: CanvasRenderingContext2D, text: string, maxWidth: number) => {
  const lines: string[] = []
  if (!text) {
    return lines
  }
  let currentLine = ''
  for (const char of text) {
    const testLine = `${currentLine}${char}`
    if (ctx.measureText(testLine).width > maxWidth && currentLine) {
      lines.push(currentLine)
      currentLine = char
    } else {
      currentLine = testLine
    }
  }
  if (currentLine) {
    lines.push(currentLine)
  }
  return lines
}

watch(form, scheduleRender, { deep: true })
watch(detections, scheduleRender, { deep: true })
watch(imageSrc, scheduleRender)

scheduleRender()
</script>

<style scoped>
.report-builder {
  padding: 16px 24px 32px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
  min-height: calc(100vh - 120px);
}

.page-header {
  margin-bottom: 24px;
}

.layout {
  align-items: stretch;
}

.form-card,
.preview-card,
.result-card {
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

.result-card {
  margin-top: 24px;
}

.result-table {
  border-radius: 12px;
  overflow: hidden;
}

.preview-wrapper {
  background: #f3f4f6;
  border-radius: 16px;
  padding: 12px;
  min-height: 540px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.report-canvas {
  width: 100%;
  max-width: 900px;
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.18);
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

  .preview-wrapper {
    min-height: 420px;
  }

  .preview-actions {
    justify-content: center;
  }
}
</style>
