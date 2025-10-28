export interface ApiResponse {
  message: string
  error?: string
}

export interface DetectionBox {
  xmin: number
  ymin: number
  xmax: number
  ymax: number
}

export interface Detection {
  class_id: number
  class_name: string
  confidence: number
  box: DetectionBox
}

export interface DetectionResponse {
  detections: Detection[]
}
