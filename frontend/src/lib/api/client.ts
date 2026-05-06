import { ApiError, NetworkError } from './errors'

export interface ApiRequestOptions {
  method?: string
  headers?: Record<string, string>
  body?: unknown
  signal?: AbortSignal
}

export async function apiFetch<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { method = 'GET', headers = {}, body, signal } = options

  const requestHeaders: Record<string, string> = {
    ...headers,
  }

  if (body !== undefined && !(body instanceof FormData)) {
    requestHeaders['Content-Type'] = 'application/json'
  }

  try {
    const response = await fetch(`/api/v1${path}`, {
      method,
      headers: requestHeaders,
      body: body instanceof FormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
      signal,
      credentials: 'include',
    })

    if (!response.ok) {
      let detail: string | undefined
      try {
        const errorBody = await response.json()
        detail = errorBody.detail || response.statusText
      } catch {
        detail = response.statusText
      }
      throw new ApiError(response.status, detail || 'Request failed')
    }

    // Handle blob/file responses
    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      return response.json() as Promise<T>
    }

    // For non-JSON responses, return the whole response
    return response as unknown as T
  } catch (err) {
    if (err instanceof ApiError) throw err
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw err
    }
    throw new NetworkError(err)
  }
}

export function buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
  if (!params) return path
  const searchParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      searchParams.set(key, String(value))
    }
  }
  const qs = searchParams.toString()
  return qs ? `${path}?${qs}` : path
}
