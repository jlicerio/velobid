// Vision analysis types matching backend AnalysisResponse

export interface VisionAnalysisResult {
  project_id: string
  blueprint_id: string
  page_num: number
  equipment: VisionItem[]
  ductwork: VisionItem[]
  piping: VisionItem[]
  fixtures: VisionItem[]
  rooms: VisionItem[]
  notes: VisionItem[]
  sidecar_path: string
}

export interface VisionItem {
  type?: string
  quantity?: number
  description?: string
  location?: string
  notes?: string
  [key: string]: unknown
}
