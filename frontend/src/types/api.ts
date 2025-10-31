export interface HeartbeatResponse {
  status: string
  timestamp: string
  uptime: number
}

export interface ReportMetadataItem {
  label: string
  value: string
}

export interface ReportChannelStat {
  channel: string
  ctc: number
  wbc: number
}

export interface ReportImageItem {
  label: string
  mimeType: string
  data: string
}

export interface ReportImageSet {
  items: ReportImageItem[]
}

export interface CtcReportResponse {
  fileName: string
  fileContent: string
  generatedAt: string
  metadata: ReportMetadataItem[]
  channels: ReportChannelStat[]
  totals: {
    totalCtc: number
    totalWbc: number
  }
  resultText: string
  remarkText: string
  selectionText: string
  hasCtcImages: boolean
  imageSet?: ReportImageSet | null
  warnings?: string[]
}
