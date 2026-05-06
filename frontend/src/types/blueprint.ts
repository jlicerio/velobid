// Blueprint types matching backend pydantic schemas

export interface BlueprintPage {
  page_number: number
  filename: string
  path: string
  url: string
  width: number | null
  height: number | null
}

export interface BlueprintUploadResponse {
  blueprint_id: string
  project_id: string
  original_filename: string
  file_extension: string
  file_size_bytes: number
  page_count: number
  page_images: BlueprintPage[]
  is_pdf: boolean
  uploaded_at: string
  metadata_path: string
}

export interface BlueprintListItem {
  blueprint_id: string
  project_id: string
  original_filename: string
  file_extension: string
  file_size_bytes: number
  page_count: number
  is_pdf: boolean
  uploaded_at: string
}

export interface BlueprintListResponse {
  project_id: string
  blueprints: BlueprintListItem[]
}

export interface BlueprintDetailResponse {
  blueprint_id: string
  project_id: string
  original_filename: string
  file_extension: string
  file_size_bytes: number
  page_count: number
  page_images: BlueprintPage[]
  is_pdf: boolean
  uploaded_at: string
  metadata_path: string
  original_file_path: string
}
