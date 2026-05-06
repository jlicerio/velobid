// File item from the GET /api/v1/files/list endpoint

export interface FileItem {
  name: string
  is_dir: boolean
  path: string
  size: number | null
}

export interface FileDeleteResponse {
  message: string
}
