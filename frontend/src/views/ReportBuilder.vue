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
                  accept="image/*"
                  @change="handleFileChange"
                />
                <el-button
                  type="primary"
                  plain
                  :disabled="!selectedFile"
                  :loading="isDetecting"
                  @click="runDetection"
                >
                  {{ isDetecting ? '识别中...' : '识别图片' }}
                </el-button>
                <div v-if="selectedFile" class="file-name">{{ selectedFile.name }}</div>
                <div v-else class="upload-tip">请选择需要识别的影像图片，支持常见图片格式</div>
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
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { postDetect } from '../api/api'
import type { Detection } from '../types/api'

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

const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const imageSrc = ref('')
const detections = ref<Detection[]>([])
const isDetecting = ref(false)
const canvasRef = ref<HTMLCanvasElement | null>(null)

const hasReport = computed(() => Boolean(imageSrc.value))

const detectionTable = computed(() =>
  detections.value.map((item, index) => ({
    index: index + 1,
    className: item.class_name || '未知目标',
    confidence: `${(item.confidence * 100).toFixed(1)}%`,
    box: `(${item.box.xmin.toFixed(0)}, ${item.box.ymin.toFixed(0)}) - (${item.box.xmax.toFixed(0)}, ${item.box.ymax.toFixed(0)})`
  }))
)

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || !files.length) {
    return
  }

  const file = files[0]
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }

  selectedFile.value = file
  detections.value = []

  const reader = new FileReader()
  reader.onload = () => {
    imageSrc.value = typeof reader.result === 'string' ? reader.result : ''
    scheduleRender()
  }
  reader.readAsDataURL(file)
}

const runDetection = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择需要识别的图片')
    return
  }

  try {
    isDetecting.value = true
    const response = await postDetect(selectedFile.value)
    detections.value = response.detections || []
    if (detections.value.length) {
      ElMessage.success('识别完成，已生成检测结果')
    } else {
      ElMessage.info('识别完成，未检测到明显目标')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('识别失败，请稍后重试')
  } finally {
    isDetecting.value = false
    scheduleRender()
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
  selectedFile.value = null
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

const scheduleRender = () => {
  nextTick(() => {
    void drawReport()
  })
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

const drawPlaceholder = (canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D) => {
  canvas.width = 900
  canvas.height = 600
  ctx.fillStyle = '#f3f4f6'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = '#9ca3af'
  ctx.font = '20px "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('请完善宠物信息并上传影像图片，生成检测报告', canvas.width / 2, canvas.height / 2)
  ctx.textAlign = 'left'
}

const renderCanvasWithData = (
  canvas: HTMLCanvasElement,
  ctx: CanvasRenderingContext2D,
  image: HTMLImageElement,
  detectionData: Detection[]
) => {
  const padding = 36
  const baseWidth = 900
  const maxImageWidth = baseWidth - padding * 2
  const scale = Math.min(1, maxImageWidth / image.width)
  const imageWidth = Math.round(image.width * scale)
  const imageHeight = Math.round(image.height * scale)
  const infoFont = '16px "Microsoft YaHei", sans-serif'
  const infoLineHeight = 28
  const titleFont = 'bold 28px "Microsoft YaHei", sans-serif'
  const sectionGap = 18
  const detectionFont = '15px "Microsoft YaHei", sans-serif'
  const detectionLineHeight = 26
  const infoAreaWidth = baseWidth - padding * 2
  const timestamp = new Date().toLocaleString()

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
  const noteLines = wrapText(measureCtx, noteContent, infoAreaWidth - measureCtx.measureText('备注：').width)
  infoLines.push(`备注：${noteLines.shift() || '无'}`)
  noteLines.forEach(line => {
    infoLines.push(`        ${line}`)
  })

  const detectionLines = detectionData.length
    ? detectionData.map((item, index) =>
        `目标${index + 1}：${item.class_name || '未知目标'}，置信度 ${(item.confidence * 100).toFixed(1)}%`
      )
    : ['未检测到显著目标']

  const infoSectionHeight = infoLines.length * infoLineHeight
  const detectionSectionHeight = detectionLines.length * detectionLineHeight + detectionLineHeight
  const canvasHeight =
    padding +
    42 +
    sectionGap +
    infoSectionHeight +
    sectionGap +
    imageHeight +
    sectionGap +
    detectionSectionHeight +
    padding

  canvas.width = baseWidth
  canvas.height = Math.round(canvasHeight)

  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  ctx.fillStyle = '#1f2937'
  ctx.font = titleFont
  ctx.fillText('宠物健康检测报告', padding, padding + 6)

  ctx.font = '14px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = '#6b7280'
  ctx.fillText(`生成时间：${timestamp}`, padding, padding + 34)

  ctx.font = infoFont
  ctx.fillStyle = '#111827'
  let currentY = padding + 34 + sectionGap
  infoLines.forEach(line => {
    ctx.fillText(line, padding, currentY)
    currentY += infoLineHeight
  })

  currentY += sectionGap - infoLineHeight
  const imageTop = currentY

  ctx.fillStyle = '#e5e7eb'
  ctx.fillRect(padding - 6, imageTop - 6, imageWidth + 12, imageHeight + 12)
  ctx.drawImage(image, padding, imageTop, imageWidth, imageHeight)

  const scaleX = imageWidth / image.width
  const scaleY = imageHeight / image.height

  detectionData.forEach(item => {
    const x = padding + item.box.xmin * scaleX
    const y = imageTop + item.box.ymin * scaleY
    const width = (item.box.xmax - item.box.xmin) * scaleX
    const height = (item.box.ymax - item.box.ymin) * scaleY

    ctx.strokeStyle = '#ef4444'
    ctx.lineWidth = 2
    ctx.strokeRect(x, y, width, height)

    const label = `${item.class_name || '目标'} ${(item.confidence * 100).toFixed(1)}%`
    ctx.font = 'bold 14px "Microsoft YaHei", sans-serif'
    const labelWidth = ctx.measureText(label).width + 14
    const labelHeight = 24
    let labelY = y
    if (labelY - labelHeight < imageTop) {
      labelY = y + labelHeight
    }
    ctx.fillStyle = 'rgba(239, 68, 68, 0.9)'
    ctx.fillRect(x, labelY - labelHeight, labelWidth, labelHeight)
    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, x + 7, labelY - 7)
  })

  currentY = imageTop + imageHeight + sectionGap
  ctx.font = 'bold 18px "Microsoft YaHei", sans-serif'
  ctx.fillStyle = '#1f2937'
  ctx.fillText('检测结果摘要', padding, currentY)

  currentY += detectionLineHeight
  ctx.font = detectionFont
  ctx.fillStyle = '#374151'
  detectionLines.forEach(line => {
    ctx.fillText(line, padding, currentY)
    currentY += detectionLineHeight
  })
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
